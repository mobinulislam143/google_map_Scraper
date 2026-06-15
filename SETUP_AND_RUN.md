# Setup and Run Instructions

## Prerequisites
- Python 3.8+
- ChromeDriver (for Selenium)
- credential.json (Google Sheets API)
- Google Sheet created and shared

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Verify Files in Folder

Make sure your folder has:
```
google-maps-scraper/
├── scraper.py              (the main script)
├── requirements.txt        (dependencies)
├── credential.json         (Google API credentials)
├── SETUP_AND_RUN.md       (this file)
```

## Step 3: Install ChromeDriver

**Option A: Automatic (Recommended)**
```bash
pip install webdriver-manager
```

Then modify scraper.py line 100:
```python
# Change this:
driver = webdriver.Chrome(options=chrome_options)

# To this:
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
```

**Option B: Manual**
1. Download from: https://chromedriver.chromium.org/
2. Place `chromedriver.exe` in same folder as scraper.py

## Step 4: Verify Google Sheets Credentials

1. Your credential.json should be in the same folder
2. Spreadsheet ID in script: `129MVddG50LZo794VRyW4HkmrK4ymfFGf8RwycPEPFKo`
3. Sheet name: `Sheet1` (default)

## Step 5: Run the Scraper

**From PowerShell/Terminal:**
```bash
python scraper.py
```

**Expected Output:**
```
Initializing Google Sheets API...

[1/30] Scraping Apache Junction, Arizona...
  Scrolling through results for Apache Junction...
  Found 25 listings
  Extracted 25 businesses

[2/30] Scraping Avondale, Arizona...
...
```

## Step 6: Check Google Sheet

Go to your sheet: https://docs.google.com/spreadsheets/d/129MVddG50LZo794VRyW4HkmrK4ymfFGf8RwycPEPFKo/edit

New rows will be added automatically as scraper runs!

---

## What the Script Does

1. ✓ Searches Google Maps for "property management company in {city} {state}"
2. ✓ Scrolls through ALL available results (50+ per city)
3. ✓ Extracts: Name, Phone, Rating, Review, Type, Full Address
4. ✓ Appends directly to your Google Sheet in real-time
5. ✓ Uploads in batches every 5 cities

## Expected Results per City

- **Arizona:** 30 cities
- **Results per city:** 20-40 businesses
- **Total for Arizona:** ~900-1,200 records
- **Time:** ~30-60 minutes
- **Your Google Sheet:** Automatically populated

## Troubleshooting

### "ModuleNotFoundError: No module named 'selenium'"
```bash
pip install selenium
```

### "ChromeDriver not found"
Install webdriver-manager:
```bash
pip install webdriver-manager
```

### "Google Sheets API Error"
- Check credential.json exists
- Verify spreadsheet ID matches
- Make sure credential has Sheets API permission

### "Connection timeout on Google Maps"
- Script has built-in waits
- If still timing out, increase `time.sleep()` values
- Or use proxy service

## Advanced: Scrape All 50 States

To scrape all 594 cities instead of just Arizona:

Replace the ARIZONA_CITIES list at the bottom of scraper.py with ALL_CITIES from `all_cities_594.txt`

Expected time: 10-20 hours (depends on your internet/CPU)

---

## Key Features

✓ Real-time upload to Google Sheets  
✓ Automatic scrolling for max results  
✓ Rate-limited (doesn't trigger Google's blocks)  
✓ Error handling (skips cities with issues)  
✓ Batch processing (efficient uploads)  

---

## Questions?

Check GitHub: https://github.com/gosom/google-maps-scraper
