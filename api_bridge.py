#!/usr/bin/env python3
"""
API Bridge — n8n -> Google Maps Scraper -> LeadGen CRM
Uses Flask (no pydantic dependency, works on Python 3.14+)

Run:
    pip install -r requirements-bridge.txt
    python api_bridge.py
"""

import json
import os
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
CRM_API_URL      = os.getenv("CRM_API_URL",      "https://auto-leadgen-crm-backend.vercel.app")
BATCH_API_SECRET = os.getenv("BATCH_API_SECRET",  "")
BRIDGE_SECRET    = os.getenv("BRIDGE_SECRET",     "")
SCRAPER_BINARY   = os.getenv("SCRAPER_BINARY",    "./google-maps-scraper.exe")
MAX_DEPTH        = int(os.getenv("SCRAPER_MAX_DEPTH", "3"))
PORT             = int(os.getenv("PORT",           "8001"))

# In-memory job store
jobs = {}

app = Flask(__name__)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    binary_exists = Path(SCRAPER_BINARY).exists()
    return jsonify({
        "status": "ok",
        "scraper_binary": SCRAPER_BINARY,
        "binary_found": binary_exists,
        "crm_url": CRM_API_URL,
    })


@app.route("/webhook/scrape", methods=["POST"])
def webhook_scrape():
    # Auth check
    if BRIDGE_SECRET:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {BRIDGE_SECRET}":
            return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)
    if not data or "reps" not in data:
        return jsonify({"error": "Missing reps in body"}), 400

    reps = [
        r for r in data["reps"]
        if r.get("city") and r.get("state") and r.get("niches")
    ]

    if not reps:
        return jsonify({"job_id": None, "status": "skipped",
                        "message": "No reps with city/state/niches"}), 200

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "running",
        "started_at": time.time(),
        "rep_count": len(reps),
        "total_leads": 0,
        "error": None,
    }

    # Run in background thread
    t = threading.Thread(target=run_scrape_job, args=(job_id, reps), daemon=True)
    t.start()

    return jsonify({
        "job_id": job_id,
        "status": "running",
        "reps_queued": len(reps),
        "message": f"Scraping {len(reps)} rep(s) in background",
    })


@app.route("/jobs/<job_id>")
def get_job(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


# ── Scraping logic ────────────────────────────────────────────────────────────
def run_scrape_job(job_id, reps):
    total_leads = 0
    try:
        for rep in reps:
            niches = rep.get("niches", [])
            for niche in niches:
                keyword = f"{niche} in {rep['city']} {rep['state']}"
                print(f"[{job_id}] Scraping: {keyword!r}")

                results = scrape_keyword(keyword)
                leads   = to_crm_leads(results, rep, niche)

                if leads:
                    post_to_crm(leads)
                    total_leads += len(leads)
                    print(f"[{job_id}] Sent {len(leads)} leads for {keyword!r}")
                else:
                    print(f"[{job_id}] No leads for {keyword!r}")

        jobs[job_id].update({"status": "completed", "total_leads": total_leads})
        print(f"[{job_id}] DONE — {total_leads} total leads sent to CRM")

    except Exception as exc:
        jobs[job_id].update({"status": "failed", "error": str(exc)})
        print(f"[{job_id}] ERROR: {exc}")


def scrape_keyword(keyword):
    with tempfile.TemporaryDirectory() as tmp:
        keywords_file = Path(tmp) / "keywords.txt"
        results_file  = Path(tmp) / "results.json"
        log_file      = Path(tmp) / "scraper.log"

        keywords_file.write_text(keyword, encoding="utf-8")

        binary = str(Path(SCRAPER_BINARY).resolve())
        # Run from the binary's own directory so playwright finds its browsers
        binary_dir = str(Path(SCRAPER_BINARY).resolve().parent)

        cmd = [
            binary,
            "-input",   str(keywords_file),
            "-results", str(results_file),
            "-json",
            "-depth",   str(MAX_DEPTH),
            "-exit-on-inactivity", "3m",
        ]

        print(f"  [cmd] {' '.join(cmd)}")

        # Write stdout/stderr to a log file to avoid capture issues on Windows
        with open(log_file, "w", encoding="utf-8", errors="replace") as lf:
            proc = subprocess.run(
                cmd,
                stdout=lf,
                stderr=lf,
                stdin=subprocess.DEVNULL,
                cwd=binary_dir,
                timeout=600,
            )

        log_text = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
        print(f"  [exit] returncode={proc.returncode}")
        if log_text.strip():
            print(f"  [log] {log_text[:800]}")

        if not results_file.exists():
            print(f"  [warn] results file not created: {results_file}")
            return []

        text = results_file.read_text(encoding="utf-8").strip()
        if not text:
            return []

        entries = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return entries


def to_crm_leads(entries, rep, niche):
    """Map Go scraper Entry fields to CRM batchInsertLeads shape."""
    leads = []
    for e in entries:
        phone = (e.get("phone") or "").strip()
        if not phone:
            continue

        website   = (e.get("web_site") or "").strip()
        comp_addr = e.get("complete_address") or {}

        leads.append({
            "businessName":  e.get("title") or "",
            "phone":         phone,
            "city":          comp_addr.get("city")  or rep.get("city", ""),
            "state":         comp_addr.get("state") or rep.get("state", ""),
            "niche":         niche,
            "websiteStatus": "HAS_WEBSITE" if website else "NO_WEBSITE",
            "websiteUrl":    website or None,
            "assignedRepId": rep["id"],
        })

    cap = rep.get("dailyLeadCap", 150)
    return leads[:cap]


def post_to_crm(leads):
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{CRM_API_URL}/api/leads/batch",
            headers={
                "x-batch-secret": BATCH_API_SECRET,
                "Content-Type":   "application/json",
            },
            json={"leads": leads},
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"CRM {resp.status_code}: {resp.text[:200]}")
        print(f"  CRM accepted {len(leads)} leads -> {resp.json()}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    binary_path = Path(SCRAPER_BINARY)
    if not binary_path.exists():
        print(f"WARNING: scraper binary not found at {binary_path.resolve()}")
        print("Build it: go build -o google-maps-scraper.exe .")
    else:
        print(f"Scraper binary : {binary_path.resolve()}")

    print(f"CRM URL        : {CRM_API_URL}")
    print(f"Listening on   : http://0.0.0.0:{PORT}")

    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
