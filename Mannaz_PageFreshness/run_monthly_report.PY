"""
MANNAZ PAGE FRESHNESS - MONTHLY REPORT GENERATOR
Run this script to generate monthly freshness reports
"""

import os
import sys
import pandas as pd
from datetime import datetime
import shutil
from pathlib import Path
import logging
import time

# Import configuration
try:
    import config
except ImportError:
    print("ERROR: config.py not found!")
    print("Please create config.py in the same folder as this script.")
    input("Press Enter to exit...")
    sys.exit(1)

# Import scraper functions
try:
    from scraper import discover_via_sitemap, extract_meta
except ImportError:
    print("ERROR: scraper.py not found!")
    print("Please ensure scraper.py is in the same folder as this script.")
    input("Press Enter to exit...")
    sys.exit(1)


def setup_logging():
    """Setup logging for the automation"""
    log_file = os.path.join(
        config.LOGS_FOLDER,
        f"report_{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    
    os.makedirs(config.LOGS_FOLDER, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        config.DATA_FOLDER,
        os.path.join(config.DATA_FOLDER, "archives"),
        os.path.join(config.DATA_FOLDER, "current"),
        os.path.join(config.DATA_FOLDER, "comparisons"),
        config.REPORTS_FOLDER,
        os.path.join(config.REPORTS_FOLDER, "monthly"),
        os.path.join(config.REPORTS_FOLDER, "dashboard"),
        config.LOGS_FOLDER
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_all_urls():
    """Get all URLs from sitemap"""
    logger = logging.getLogger(__name__)
    
    if config.SCRAPE_ENTIRE_SITE:
        logger.info("Discovering ALL pages from sitemap...")
    else:
        logger.info("Discovering only articles...")
    
    urls = discover_via_sitemap()
    
    # Filter for articles only if needed
    if not config.SCRAPE_ENTIRE_SITE:
        urls = [u for u in urls if '/artikler/' in u or '/articles/' in u]
    
    if config.TESTING_MODE:
        logger.info(f"TESTING MODE: Limiting to 50 pages")
        urls = urls[:50]
    
    return urls


def classify_freshness(date_created, date_modified, scraped_at):
    """Classify page freshness based on how recently it was modified"""
    try:
        scraped_date = pd.to_datetime(scraped_at, errors='coerce')
        if pd.isna(scraped_date):
            return "No date available"
        
        # Use modified date if available, otherwise use created date
        reference_date = None
        if date_modified and date_modified != "":
            reference_date = pd.to_datetime(date_modified, errors='coerce')
        
        if pd.isna(reference_date) and date_created and date_created != "":
            reference_date = pd.to_datetime(date_created, errors='coerce')
        
        if pd.isna(reference_date):
            return "No date available"
        
        # Calculate months difference
        months_diff = (scraped_date.year - reference_date.year) * 12 + (scraped_date.month - reference_date.month)
        
        if months_diff < 6:
            return "Fresh"
        elif months_diff < 12:
            return "Rotting"
        else:
            return "Outdated"
    except:
        return "Error in classification"


def scrape_current_state():
    """Scrape current state of all pages"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("STARTING MONTHLY SCRAPE")
    logger.info("=" * 70)
    
    # Get URLs
    urls = get_all_urls()
    logger.info(f"Found {len(urls)} URLs to scrape")
    
    # Scrape each URL
    rows = []
    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] {url}")
        try:
            rows.append(extract_meta(url))
            time.sleep(config.DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Add freshness classification
    df['freshness'] = df.apply(
        lambda row: classify_freshness(
            row.get('date_created'),
            row.get('date_modified'),
            row.get('scraped_at')
        ),
        axis=1
    )
    
    # Add path column
    df['path'] = df['url'].str.replace("https://www.mannaz.com", "", regex=False)
    
    # Save current state
    current_file = os.path.join(
        config.DATA_FOLDER,
        "current",
        "mannaz_pages_current.csv"
    )
    df.to_csv(current_file, index=False, encoding='utf-8')
    logger.info(f"Current state saved: {current_file}")
    
    return df, current_file


def archive_current_month(current_file):
    """Archive the current month's data"""
    logger = logging.getLogger(__name__)
    
    if config.TESTING_MODE:
        logger.info("TESTING MODE: Skipping archive")
        return None
    
    # Create month folder
    month_folder = os.path.join(
        config.DATA_FOLDER,
        "archives",
        datetime.now().strftime('%Y-%m')
    )
    os.makedirs(month_folder, exist_ok=True)
    
    # Copy current to archive
    archive_file = os.path.join(
        month_folder,
        f"mannaz_pages_{datetime.now().strftime('%Y-%m')}.csv"
    )
    
    shutil.copy2(current_file, archive_file)
    logger.info(f"Archived to: {archive_file}")
    
    return archive_file


def get_previous_month_data():
    """Get previous month's data for comparison"""
    logger = logging.getLogger(__name__)
    
    archives_folder = os.path.join(config.DATA_FOLDER, "archives")
    
    if not os.path.exists(archives_folder):
        logger.info("No previous data found (first run)")
        return None
    
    # Get all archive folders
    archive_folders = sorted([
        f for f in os.listdir(archives_folder)
        if os.path.isdir(os.path.join(archives_folder, f))
    ], reverse=True)
    
    if len(archive_folders) == 0:
        logger.info("No previous month data available")
        return None
    
    # Get the most recent archive
    prev_month_folder = archive_folders[0]
    prev_month_file = os.path.join(
        archives_folder,
        prev_month_folder,
        f"mannaz_pages_{prev_month_folder}.csv"
    )
    
    if os.path.exists(prev_month_file):
        logger.info(f"Loading previous month: {prev_month_folder}")
        return pd.read_csv(prev_month_file)
    
    return None


def identify_change(prev_status, curr_status):
    """Identify the type of freshness change"""
    if pd.isna(prev_status) or prev_status == "":
        return "New page"
    if pd.isna(curr_status) or curr_status == "":
        return "Removed page"
    if prev_status == curr_status:
        return "No change"
    
    # Track degradation
    if prev_status == "Fresh" and curr_status == "Rotting":
        return "Fresh → Rotting ⚠️"
    if prev_status == "Fresh" and curr_status == "Outdated":
        return "Fresh → Outdated 🚨"
    if prev_status == "Rotting" and curr_status == "Outdated":
        return "Rotting → Outdated 🚨"
    
    # Track improvement
    if prev_status == "Rotting" and curr_status == "Fresh":
        return "Rotting → Fresh ✅"
    if prev_status == "Outdated" and curr_status == "Fresh":
        return "Outdated → Fresh ✅"
    if prev_status == "Outdated" and curr_status == "Rotting":
        return "Outdated → Rotting ✅"
    
    return f"{prev_status} → {curr_status}"


def compare_months(current_df, previous_df):
    """Compare current and previous month to find freshness changes"""
    logger = logging.getLogger(__name__)
    
    if previous_df is None:
        logger.info("No comparison possible (first run)")
        return None
    
    logger.info("Comparing months for freshness changes...")
    
    # Merge on URL
    comparison = pd.merge(
        current_df[['url', 'path', 'title', 'freshness', 'date_modified']],
        previous_df[['url', 'freshness']],
        on='url',
        how='outer',
        suffixes=('_current', '_previous')
    )
    
    # Identify changes
    comparison['status_change'] = comparison.apply(
        lambda row: identify_change(row['freshness_previous'], row['freshness_current']),
        axis=1
    )
    
    # Filter only pages with changes
    changes = comparison[comparison['status_change'] != 'No change'].copy()
    
    # Save comparison
    comparison_file = os.path.join(
        config.DATA_FOLDER,
        "comparisons",
        f"comparison_{datetime.now().strftime('%Y-%m')}.csv"
    )
    changes.to_csv(comparison_file, index=False, encoding='utf-8')
    
    logger.info(f"Found {len(changes)} pages with freshness changes")
    logger.info(f"Comparison saved: {comparison_file}")
    
    return changes


def generate_html_report(current_df, changes_df):
    """Generate HTML dashboard report"""
    logger = logging.getLogger(__name__)
    
    logger.info("Generating HTML report...")
    
    # Calculate statistics
    total_pages = len(current_df)
    fresh_count = len(current_df[current_df['freshness'] == 'Fresh'])
    rotting_count = len(current_df[current_df['freshness'] == 'Rotting'])
    outdated_count = len(current_df[current_df['freshness'] == 'Outdated'])
    
    # Changes summary
    if changes_df is not None and not changes_df.empty:
        new_pages = len(changes_df[changes_df['status_change'] == 'New page'])
        fresh_to_rotting = len(changes_df[changes_df['status_change'].str.contains('Fresh → Rotting', na=False)])
        rotting_to_outdated = len(changes_df[changes_df['status_change'].str.contains('Rotting → Outdated', na=False)])
        improvements = len(changes_df[changes_df['status_change'].str.contains('✅', na=False)])
    else:
        new_pages = fresh_to_rotting = rotting_to_outdated = improvements = 0
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mannaz Page Freshness Report - {datetime.now().strftime('%B %Y')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
        }}
        .fresh {{ color: #10b981; }}
        .rotting {{ color: #f59e0b; }}
        .outdated {{ color: #ef4444; }}
        .improved {{ color: #3b82f6; }}
        
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f9fafb;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f9fafb;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Mannaz Page Freshness Report</h1>
        <p>Monthly Report for {datetime.now().strftime('%B %Y')}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Pages</div>
            <div class="stat-value">{total_pages}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Fresh</div>
            <div class="stat-value fresh">{fresh_count}</div>
            <div class="stat-label">{round(fresh_count/total_pages*100, 1) if total_pages > 0 else 0}%</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Rotting</div>
            <div class="stat-value rotting">{rotting_count}</div>
            <div class="stat-label">{round(rotting_count/total_pages*100, 1) if total_pages > 0 else 0}%</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Outdated</div>
            <div class="stat-value outdated">{outdated_count}</div>
            <div class="stat-label">{round(outdated_count/total_pages*100, 1) if total_pages > 0 else 0}%</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🔄 Changes This Month</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">New Pages</div>
                <div class="stat-value">{new_pages}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Fresh → Rotting</div>
                <div class="stat-value rotting">{fresh_to_rotting}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Rotting → Outdated</div>
                <div class="stat-value outdated">{rotting_to_outdated}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Updated Pages</div>
                <div class="stat-value improved">{improvements}</div>
            </div>
        </div>
    </div>
"""
    
    # Add changes table if available
    if changes_df is not None and not changes_df.empty:
        html_content += """
    <div class="section">
        <h2>📝 Detailed Changes</h2>
        <table>
            <thead>
                <tr>
                    <th>Page Title</th>
                    <th>Path</th>
                    <th>Change</th>
                    <th>Last Modified</th>
                </tr>
            </thead>
            <tbody>
"""
        for _, row in changes_df.head(100).iterrows():
            title = str(row.get('title', 'N/A'))[:80]
            path = row.get('path', 'N/A')
            change = row.get('status_change', 'N/A')
            modified = row.get('date_modified', 'N/A')
            
            html_content += f"""
                <tr>
                    <td>{title}</td>
                    <td><a href="https://www.mannaz.com{path}" target="_blank">{path}</a></td>
                    <td>{change}</td>
                    <td>{modified}</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    # Save report
    report_file = os.path.join(
        config.REPORTS_FOLDER,
        "monthly",
        f"Report_{datetime.now().strftime('%Y-%m')}.html"
    )
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Report saved: {report_file}")
    
    return report_file


def main():
    """Main automation workflow"""
    logger = setup_logging()
    
    logger.info("=" * 70)
    logger.info("MANNAZ PAGE FRESHNESS - MONTHLY REPORT")
    logger.info("=" * 70)
    
    try:
        # Setup
        setup_directories()
        
        # Scrape current state
        current_df, current_file = scrape_current_state()
        
        # Get previous month for comparison
        previous_df = get_previous_month_data()
        
        # Compare months
        changes_df = compare_months(current_df, previous_df)
        
        # Archive current month
        archive_current_month(current_file)
        
        # Generate report
        report_file = generate_html_report(current_df, changes_df)
        
        logger.info("=" * 70)
        logger.info("REPORT COMPLETE!")
        logger.info(f"Open report: {report_file}")
        logger.info("=" * 70)
        
        # Open report in browser
        import webbrowser
        webbrowser.open(f'file:///{report_file}')
        
    except Exception as e:
        logger.error(f"Error in automation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()