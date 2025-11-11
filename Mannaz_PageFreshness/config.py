"""
CONFIGURATION FILE FOR MANNAZ PAGE FRESHNESS MONITOR
Edit this file with your settings
"""

# BASE SETTINGS
BASE_URL = "https://www.mannaz.com/"

# USER-SPECIFIC PATHS
# Change this to your OneDrive folder location
USER_BASE_PATH = r"C:\Users\tmo\OneDrive - Mannaz\Desktop\Mannaz Artikler/Mannaz_pagefreshness"

# GOOGLE INSIGHTS FILE
# Path to your Google Insights Excel file
GOOGLE_INSIGHTS_PATH = USER_BASE_PATH + r"\Scripts\Program folder\Google-Insights.xlsx"

# OUTPUT SETTINGS
# The script will create these folders if they don't exist
DATA_FOLDER = USER_BASE_PATH + r"\Mannaz_PageFreshness\data"
REPORTS_FOLDER = USER_BASE_PATH + r"\Mannaz_PageFreshness\reports"
LOGS_FOLDER = USER_BASE_PATH + r"\Mannaz_PageFreshness\logs"

# SCRAPING SETTINGS
SCRAPE_ENTIRE_SITE = True  # True = all pages, False = only articles
MAX_PAGES_TO_CRAWL = 500   # Maximum pages to crawl (safety limit)
DELAY_BETWEEN_REQUESTS = 0.5  # Seconds to wait between requests

# REPORTING SETTINGS
SEND_EMAIL_REPORT = False  # Set to True if you want email reports
EMAIL_TO = "tmo@mannaz.com"  # Change to actual email

# PAGE TYPE DETECTION
# These patterns help identify page types from URLs
PAGE_TYPES = {
    "/artikler/": "Article",
    "/articles/": "Article", 
    "/kurser/": "Course",
    "/courses/": "Course",
    "/om-mannaz/": "About",
    "/about/": "About",
    "/kontakt/": "Contact",
    "/contact/": "Contact",
}

# TESTING MODE
# Set to True when testing - limits to 50 pages and doesn't archive
TESTING_MODE = True  # Change to False for production