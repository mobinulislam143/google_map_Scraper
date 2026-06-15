# 🚀 START HERE - Quick Start Guide

## Everything is Ready!

Your project is fully configured. Just **run one command** to start scraping.

---

## ✅ What's Been Set Up

- ✓ `scraper.py` - Main scraper script
- ✓ `credential.json` - Google Sheets API authentication
- ✓ `requirements.txt` - Python dependencies
- ✓ `RUN.bat` / `RUN.ps1` - Auto-run scripts
- ✓ Google Sheet connected and ready to receive data

---

## 🎯 How to Run

### Option 1: Auto-Run (Easiest)

**Double-click one of these files:**
- `RUN.bat` (Windows Batch)
- `RUN.ps1` (PowerShell)

They will:
1. ✓ Install Python dependencies automatically
2. ✓ Start the scraper
3. ✓ Keep the window open when done

### Option 2: Manual (Terminal)

```powershell
# Navigate to folder
cd D:\ai project\google-maps-scraper

# Install dependencies
pip install -r requirements.txt

# Run scraper
python scraper.py
```

---

## 📊 What Happens

When you run the scraper:

```
============================================================
GOOGLE MAPS PROPERTY MANAGEMENT SCRAPER
============================================================

Initializing Google Sheets API...

Preparing 'Arizona' sheet...
  Creating new sheet: Arizona
  ✓ Sheet 'Arizona' created with headers

[1/30] Apache Junction, Arizona
  Scrolling through Apache Junction...
    Found 28 listings
    ✓ Extracted 28 businesses

[2/30] Avondale, Arizona
  Scrolling through Avondale...
    Found 35 listings
    ✓ Extracted 35 businesses

[5/30] Casa Grande, Arizona
  
  📤 Uploading 147 records to 'Arizona' sheet...
  ✓ Successfully uploaded!

... (continues for all 30 Arizona cities)

============================================================
SUMMARY
============================================================
State: Arizona
Total Businesses Scraped: 987
Cities Processed: 30/30

✓ Data saved to Google Sheet: 'Arizona'
View here: https://docs.google.com/spreadsheets/d/129MVddG50LZo794VRyW4HkmrK4ymfFGf8RwycPEPFKo/edit
============================================================
```

---

## 📍 Expected Results

**For Arizona (30 cities):**
- Time: ~30-60 minutes
- Results: ~900-1,200 property management companies
- Data: Automatically added to "Arizona" sheet in Google Sheets
- Fields: Business Name, Phone, Website, Rating, Review, Type, Location

---

## 🔄 For Other States

To scrape a different state (California, Texas, etc.):

1. Edit `scraper.py`
2. Change line ~250:
   ```python
   STATE = "Arizona"
   ```
   to:
   ```python
   STATE = "California"
   ```
3. Change the city list to match (copy from `all_cities_594.txt`)
4. Run the script

A new sheet named "California" will be created automatically with all city data.

---

## ⚠️ Troubleshooting

**"ModuleNotFoundError: No module named 'selenium'"**
- Run: `pip install -r requirements.txt`

**"Chrome driver not found"**
- The script auto-downloads it
- First run may take longer

**"Google Sheets API Error"**
- Check that credential.json exists
- Make sure it's in the same folder as scraper.py

**Chrome window opens but nothing loads**
- Some networks block Google Maps
- Try with a VPN or proxy

---

## 📋 File List

```
D:\ai project\google-maps-scraper\
├── RUN.bat                    ← Click to run (Windows Batch)
├── RUN.ps1                    ← Click to run (PowerShell)
├── START_HERE.md              ← You are here
├── scraper.py                 ← Main script
├── credential.json            ← API credentials (keep secret!)
├── requirements.txt           ← Python packages
├── SETUP_AND_RUN.md           ← Detailed setup guide
└── all_cities_594.txt         ← All US cities (for future use)
```

---

## 🎯 Ready?

**Just run:** `RUN.bat` or `RUN.ps1`

That's it! The scraper will:
1. Authenticate with Google Sheets API
2. Search Google Maps for each Arizona city
3. Scroll through all available results
4. Extract: Name, Phone, Rating, Review, Type, Location
5. **Upload directly to your Google Sheet in real-time**

---

## Questions?

Check `SETUP_AND_RUN.md` for detailed troubleshooting
