# Mannaz Page Freshness Monitor

Automated tool to monitor and report on content freshness across the Mannaz website. Tracks when pages were last updated and classifies them as Fresh, Rotting, or Outdated.

## Features

- **Automated Scraping**: Discovers pages via sitemap or web crawling
- **Freshness Classification**: 
  - Fresh: Updated within 6 months
  - Rotting: Updated 6-12 months ago
  - Outdated: Not updated for 12+ months
- **Monthly Reports**: Excel and HTML reports with visualizations
- **Change Tracking**: Monitors content decay over time
- **Multi-language Support**: Handles Danish and English content

## Prerequisites

- Python 3.8 or higher
- Internet connection
- Excel (for viewing reports)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/mannaz-page-freshness.git
   cd mannaz-page-freshness
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure settings**
   ```bash
   cp config.example.py config.py
   ```
   
   Edit `config.py` with your paths:
   ```python
   USER_BASE_PATH = r"C:\Your\Path\Here"
   TESTING_MODE = True  # Set to False for production
   ```

## Quick Start

### Windows
Double-click `run_monthly_report.bat`

### Command Line
```bash
python run_monthly_report.py
```

## Configuration

Edit `config.py` to customize:

```python
# Scraping settings
SCRAPE_ENTIRE_SITE = True      # True = all pages, False = articles only
MAX_PAGES_TO_CRAWL = 500       # Safety limit
DELAY_BETWEEN_REQUESTS = 0.5   # Be polite to the server

# Testing mode (limits to 50 pages)
TESTING_MODE = True             # Change to False for production
```

## Project Structure

```
Mannaz_PageFreshness/
├── config.py              # Your configuration (not in repo)
├── config.example.py      # Configuration template
├── run_monthly_report.py  # Main script
├── scraper.py            # Web scraping logic
├── generate_excel_report.py  # Excel generation
├── data/                 # Scraped data (gitignored)
├── reports/              # Generated reports (gitignored)
└── logs/                 # Execution logs (gitignored)
```

## Usage

### First Run
The first run will:
1. Discover all pages from sitemap
2. Scrape metadata from each page
3. Generate baseline report
4. Save data to `data/current/`

### Subsequent Runs
Monthly runs will:
1. Scrape current state
2. Compare with previous month
3. Identify freshness changes
4. Generate comparison report
5. Archive historical data

### Reports Generated

1. **Excel Report**: `reports/monthly/Mannaz_Freshness_Report_YYYY-MM.xlsx`
   - Dashboard with charts
   - Updated articles list
   - Status changes
   - All pages overview

2. **HTML Report**: `reports/monthly/Report_YYYY-MM.html`
   - Web-based dashboard
   - Summary statistics
   - Change details

## Freshness Classification

| Status | Definition | Action Needed |
|--------|-----------|---------------|
| **Fresh** | Updated < 6 months ago | Monitor |
| **Rotting** | Updated 6-12 months ago | Review content |
| **Outdated** | Updated > 12 months ago | Update urgently |

## Testing

Run in testing mode (50 pages only):
```python
# In config.py
TESTING_MODE = True
```

Test Excel generation:
```bash
python test_excel.py
```

## Troubleshooting

### Common Issues

**"config.py not found"**
- Copy `config.example.py` to `config.py`
- Update paths in the file

**"No module named 'requests'"**
- Install dependencies: `pip install -r requirements.txt`

**"Permission denied" when saving files**
- Check write permissions on output folders
- Close Excel files if open

**Slow scraping**
- First run takes 10-30 minutes (normal)
- Adjust `DELAY_BETWEEN_REQUESTS` if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License Here - e.g., MIT]

## Contact

For questions or support:
- Open an issue on GitHub
- Contact: [your-email@mannaz.com]

## Changelog

### Version 1.0.0 (2025-11)
- Initial release
- Sitemap-based discovery
- Excel and HTML reporting
- Monthly change tracking
