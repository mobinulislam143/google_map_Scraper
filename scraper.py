#!/usr/bin/env python3
"""
Google Maps Scraper - Uses stable aria-label / data-item-id selectors
"""

import time
import re
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

SPREADSHEET_ID = "129MVddG50LZo794VRyW4HkmrK4ymfFGf8RwycPEPFKo"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheets_service():
    if not os.path.exists('credential.json'):
        print("\n❌ credential.json not found!")
        exit(1)
    try:
        creds = Credentials.from_service_account_file('credential.json', scopes=SCOPES)
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)


def create_sheet_if_not_exists(service, sheet_name):
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_exists = any(s['properties']['title'] == sheet_name for s in sheets)

        if not sheet_exists:
            print(f"  Creating sheet: {sheet_name}")
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
            ).execute()

            service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{sheet_name}!A:H',
                valueInputOption='USER_ENTERED',
                body={'values': [['Business_Name', 'Phone number', 'Website', 'Rating', 'Review', 'Type', 'Location', 'City']]}
            ).execute()
            print(f"  ✓ Sheet created")
    except Exception as e:
        print(f"  Sheet setup error: {e}")


def append_to_sheet(service, sheet_name, values):
    try:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{sheet_name}!A:H',
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        return True
    except Exception as e:
        print(f"  Sheet append error: {e}")
        return False


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return ' '.join(text.split()).strip()


# Map every non-English digit script to ASCII 0-9
_DIGIT_MAP = str.maketrans(
    '০১২৩৪৫৬৭৮৯'   # Bengali
    '٠١٢٣٤٥٦٧٨٩'   # Arabic-Indic
    '۰۱۲۳۴۵۶۷۸۹'   # Extended Arabic-Indic (Persian)
    '०१२३४५६७८९'   # Devanagari
    '੦੧੨੩੪੫੬੭੮੯'  # Gurmukhi
    '૦૧૨૩૪૫૬૭૮૯'  # Gujarati
    '൦൧൨൩൪൫൬൭൮൯'  # Malayalam
    '᠐᠑᠒᠓᠔᠕᠖᠗᠘᠙',  # Mongolian
    '0123456789' * 8
)

def to_english_digits(text):
    """Convert any non-ASCII digit script to English digits."""
    if not text:
        return text
    return text.translate(_DIGIT_MAP)


def create_driver():
    """Create a fresh Chrome driver."""
    chrome_options = Options()
    temp_profile = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    try:
        svc = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=svc, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver


def is_driver_alive(driver):
    try:
        _ = driver.current_url
        return True
    except:
        return False


def wait_for_panel_load(driver, timeout=10):
    """Wait until the detail panel h1 has text."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            h1s = driver.find_elements(By.CSS_SELECTOR, "h1")
            for h1 in h1s:
                if h1.text.strip():
                    return True
        except:
            pass
        time.sleep(0.4)
    return False


def extract_detail_panel_data(driver, debug=False):
    """Extract business data using stable Google Maps selectors."""
    try:
        if not wait_for_panel_load(driver):
            if debug:
                print("       [DEBUG] Panel did not load (no h1 text found)")
            return None

        data = {
            'name': '',
            'phone': '',
            'website': '',
            'rating': '',
            'review': '',
            'address': '',
            'type': 'Property management'
        }

        # --- Name: first non-empty h1 ---
        try:
            for h1 in driver.find_elements(By.CSS_SELECTOR, "h1"):
                name = clean_text(h1.text)
                if name:
                    data['name'] = name
                    break
        except:
            pass

        if not data['name'] or len(data['name']) < 2:
            if debug:
                print("       [DEBUG] No name found")
            return None

        # --- Phone: tel: href is most reliable ---
        try:
            tel = driver.find_element(By.CSS_SELECTOR, "a[href^='tel:']")
            data['phone'] = tel.get_attribute('href').replace('tel:', '').strip()
        except:
            try:
                for btn in driver.find_elements(By.CSS_SELECTOR, "button[data-tooltip]"):
                    tip = btn.get_attribute('data-tooltip') or ''
                    m = re.search(r'(\+?1?[\s\-]?\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4})', tip)
                    if m:
                        data['phone'] = m.group(1).strip()
                        break
            except:
                pass
            if not data['phone']:
                try:
                    body = driver.find_element(By.CSS_SELECTOR, "div[role='main']").text
                    m = re.search(r'\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}', body)
                    if m:
                        data['phone'] = m.group(0)
                except:
                    pass

        # --- Website: data-item-id="authority" ---
        try:
            el = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority']")
            href = el.get_attribute('href') or ''
            if not href:
                # the anchor might be inside
                a = el.find_element(By.TAG_NAME, 'a')
                href = a.get_attribute('href') or ''
            data['website'] = href[:200]
        except:
            try:
                skip = ['google.com', 'facebook.com', 'instagram.com',
                        'twitter.com', 'youtube.com', 'yelp.com', 'bbb.org', 'apple.com']
                for a in driver.find_elements(By.CSS_SELECTOR, "a[href^='http']"):
                    href = a.get_attribute('href') or ''
                    if href and not any(s in href.lower() for s in skip):
                        data['website'] = href[:200]
                        break
            except:
                pass

        # --- Rating: aria-label with "stars" ---
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, "span[aria-label]"):
                label = to_english_digits(el.get_attribute('aria-label') or '')
                m = re.search(r'(\d+\.?\d*)\s*star', label, re.I)
                if m:
                    data['rating'] = m.group(1)
                    break
        except:
            pass

        if not data['rating']:
            try:
                panel_text = to_english_digits(
                    driver.find_element(By.CSS_SELECTOR, "div[role='main']").text
                )
                for line in panel_text.split('\n')[1:10]:
                    line = line.strip()
                    if re.match(r'^\d\.\d', line):
                        data['rating'] = line[:20]
                        break
            except:
                pass

        # --- Address: data-item-id="address" or aria-label on copy button ---
        try:
            addr_el = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']")
            data['address'] = clean_text(addr_el.text)[:150]
        except:
            try:
                for btn in driver.find_elements(By.CSS_SELECTOR, "button[aria-label]"):
                    label = btn.get_attribute('aria-label') or ''
                    if (re.search(r'\d{5}', label) or
                            any(k in label for k in [' Ave', ' St', ' Rd', ' Blvd', ' Dr', ' Ln', ' Ct', ' Hwy'])):
                        data['address'] = clean_text(label)[:150]
                        break
            except:
                pass
            if not data['address']:
                try:
                    panel_text = driver.find_element(By.CSS_SELECTOR, "div[role='main']").text
                    for line in panel_text.split('\n'):
                        line = clean_text(line)
                        if re.search(r'\d{5}', line) or any(k in line for k in [' Ave', ' St', ' Rd', ' Blvd', ' Dr']):
                            data['address'] = line[:150]
                            break
                except:
                    pass

        # --- Type / Category ---
        try:
            panel_text = driver.find_element(By.CSS_SELECTOR, "div[role='main']").text
            type_kws = ['Property', 'Real Estate', 'Management', 'Apartment',
                        'Housing', 'Rental', 'Inspector', 'Realtor', 'Agent', 'Leasing']
            for line in panel_text.split('\n')[1:12]:
                line = clean_text(line)
                if any(k in line for k in type_kws) and 3 < len(line) < 80:
                    data['type'] = line
                    break
        except:
            pass

        # --- Review count: extract number inside parentheses e.g. "(1,234)" ---
        try:
            # aria-label on rating element often reads "4.5 stars 1,234 reviews"
            for el in driver.find_elements(By.CSS_SELECTOR, "span[aria-label]"):
                label = to_english_digits(el.get_attribute('aria-label') or '')
                m = re.search(r'([\d,]+)\s*review', label, re.I)
                if m:
                    data['review'] = m.group(1).replace(',', '')
                    break
        except:
            pass

        if not data['review']:
            try:
                panel_text = to_english_digits(
                    driver.find_element(By.CSS_SELECTOR, "div[role='main']").text
                )
                # Match patterns like "(1,234)" or "1,234 reviews"
                m = re.search(r'\(([\d,]+)\)', panel_text)
                if m:
                    data['review'] = m.group(1).replace(',', '')
                else:
                    m = re.search(r'([\d,]+)\s*reviews?', panel_text, re.I)
                    if m:
                        data['review'] = m.group(1).replace(',', '')
            except:
                pass

        if debug:
            print(f"       [DEBUG] Extracted: {data}")

        return data

    except Exception as e:
        if debug:
            print(f"       [DEBUG] Exception in extract: {e}")
        return None


def load_all_listings(driver, feed):
    """Scroll the feed until no new listings appear (loads the full result set)."""
    prev_count = 0
    no_change_rounds = 0

    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
        time.sleep(1.2)

        # Check for "end of results" marker
        try:
            end_marker = driver.find_element(By.CSS_SELECTOR, "span.HlvSq")
            if end_marker.is_displayed():
                break
        except:
            pass

        current = len(feed.find_elements(By.CSS_SELECTOR, 'a.hfpxzc'))
        if current == prev_count:
            no_change_rounds += 1
            if no_change_rounds >= 3:
                break
        else:
            no_change_rounds = 0
            prev_count = current

    return feed.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')


def scrape_city(driver, city, state):
    businesses = []

    try:
        search_query = f"property management company in {city} {state}"
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        print(f"  Searching {city}...")
        driver.get(url)
        time.sleep(5)

        try:
            feed = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
            )
        except:
            print(f"  No results feed for {city} — skipping")
            return []

        time.sleep(2)

        # --- Step 1: scroll until ALL listings are loaded ---
        print(f"  Loading all listings...")
        listing_links = load_all_listings(driver, feed)
        total = len(listing_links)
        print(f"  Found {total} listings. Extracting one by one...")

        if total == 0:
            return []

        extracted = 0
        seen_names = set()
        first_item = True

        # --- Step 2: click each listing and extract its detail panel ---
        for idx in range(total):
            try:
                # Re-fetch to avoid stale element references after panel opens/closes
                listing_links = feed.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
                if idx >= len(listing_links):
                    break

                link = listing_links[idx]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(0.4)

                try:
                    driver.execute_script("arguments[0].click();", link)
                except:
                    link.click()

                # Give the detail panel time to fully load
                time.sleep(3)

                data = extract_detail_panel_data(driver, debug=first_item)
                first_item = False

                # Accept ALL businesses — website/phone/rating are optional
                if data and data['name'] and data['name'] not in seen_names:
                    seen_names.add(data['name'])
                    businesses.append([
                        data['name'],
                        data['phone'],
                        data['website'],
                        to_english_digits(data['rating']),
                        data['review'],       # review count number e.g. "1234"
                        data['type'],
                        data['address'],      # Location column
                        city                  # City column
                    ])
                    extracted += 1
                    print(f"\n    ✓ [{extracted}/{total}] {data['name']}")
                    print(f"       Phone:   {data['phone'] or '—'}")
                    print(f"       Website: {data['website'] or '—'}")
                    print(f"       Rating:  {data['rating'] or '—'}")
                    print(f"       Address: {data['address'] or '—'}")

            except Exception as e:
                if 'invalid session' in str(e).lower() or 'no such window' in str(e).lower():
                    raise
                continue

        print(f"\n  ✓ Extracted {extracted}/{total} listings")
        return businesses

    except Exception as e:
        raise


def main():
    print("\n" + "=" * 70)
    print("GOOGLE MAPS SCRAPER")
    print("=" * 70)

    CITIES = [
        "Benton",
  "Bentonville",
  "Conway",
  "El Dorado",
  "Fayetteville",
  "Fort Smith",
  "Hot Springs",
  "Jacksonville",
  "Jonesboro",
  "Little Rock",
  "North Little Rock",
  "Pine Bluff",
  "Rogers",
  "Russellville",
  "Searcy",
  "Sherwood",
  "Springdale",
  "Texarkana",
  "Van Buren",
  "West Memphis"
    ]

    STATE = "Arkansas"
    sheets_service = get_sheets_service()
    create_sheet_if_not_exists(sheets_service, STATE)

    total = 0
    driver = create_driver()

    try:
        for i, city in enumerate(CITIES, 1):
            print(f"\n[{i}/{len(CITIES)}] {city}, {STATE}")

            # Restart driver if it died
            if not is_driver_alive(driver):
                print("  ⚠ Chrome crashed — restarting browser...")
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(2)
                driver = create_driver()

            try:
                businesses = scrape_city(driver, city, STATE)

                if businesses:
                    total += len(businesses)
                    print(f"  Uploading {len(businesses)} records...")
                    if append_to_sheet(sheets_service, STATE, businesses):
                        print(f"  ✓ Uploaded!")

            except Exception as e:
                err = str(e)
                if 'invalid session' in err.lower() or 'no such window' in err.lower() or 'chrome not reachable' in err.lower():
                    print(f"  ⚠ Browser session lost — restarting for next city...")
                    try:
                        driver.quit()
                    except:
                        pass
                    time.sleep(2)
                    driver = create_driver()
                else:
                    print(f"  ✗ Error in {city}: {err[:200]}")

    finally:
        try:
            driver.quit()
        except:
            pass

    print("\n" + "=" * 70)
    print(f"✓ COMPLETED - {total} businesses extracted")
    print(f"✓ View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
