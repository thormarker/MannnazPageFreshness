import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import html
import time
import os
from urllib.parse import urljoin, urlparse

BASE = "https://www.mannaz.com/"
OUT_CSV = "mannaz_articles.csv"

# ============================================================================
# URL DISCOVERY METHODS
# ============================================================================

def discover_via_sitemap():
    """Discover URLs using sitemap.xml"""
    print("Method: Sitemap discovery")
    
    def get_sitemaps():
        try:
            robots = requests.get(BASE + "robots.txt", timeout=10).text
            sitemaps = [line.split(":", 1)[1].strip() for line in robots.splitlines() 
                       if line.lower().startswith("sitemap:")]
            if not sitemaps:
                sitemaps = [BASE + "sitemap.xml"]
            return sitemaps
        except Exception as e:
            print(f"Error fetching robots.txt: {e}")
            return [BASE + "sitemap.xml"]
    
    def extract_from_sitemap(sitemap_url, depth=0):
        if depth > 3:  # Prevent infinite recursion
            return []
        
        urls = []
        try:
            print(f"  {'  ' * depth}Checking: {sitemap_url}")
            xml = BeautifulSoup(requests.get(sitemap_url, timeout=10).text, "xml")
            
            # Check for nested sitemaps
            sitemap_locs = xml.find_all("sitemap")
            if sitemap_locs:
                for sitemap_loc in sitemap_locs:
                    loc = sitemap_loc.find("loc")
                    if loc:
                        urls.extend(extract_from_sitemap(loc.text.strip(), depth + 1))
            
            # Get URLs from current sitemap
            for loc in xml.find_all("loc"):
                url = loc.text.strip()
                if "/artikler/" in url or "/articles/" in url:
                    urls.append(url)
        except Exception as e:
            print(f"  {'  ' * depth}Error: {e}")
        
        return urls
    
    sitemaps = get_sitemaps()
    all_urls = []
    for sm in sitemaps:
        all_urls.extend(extract_from_sitemap(sm))
    
    return sorted(set(all_urls))

def discover_via_crawl(start_url=None, max_pages=100):
    """Discover URLs by crawling the website (alternative method)"""
    print("Method: Web crawling")
    
    if start_url is None:
        start_url = BASE + "artikler/"
    
    visited = set()
    to_visit = {start_url}
    article_urls = set()
    
    # Add multiple entry points for better coverage
    entry_points = [
        BASE + "artikler/",
        BASE + "articles/",
        BASE + "da/artikler/",
        BASE + "en/articles/",
    ]
    
    for entry in entry_points:
        to_visit.add(entry)
    
    while to_visit and len(visited) < max_pages:
        current = to_visit.pop()
        if current in visited:
            continue
        
        print(f"  Crawling: {current} ({len(visited)}/{max_pages})")
        visited.add(current)
        
        try:
            response = requests.get(current, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find all links
            for link in soup.find_all("a", href=True):
                url = urljoin(current, link["href"])
                
                # Only process URLs from the same domain
                if not url.startswith(BASE):
                    continue
                
                # Clean URL (remove fragments and query params for deduplication)
                url = url.split("#")[0].split("?")[0].rstrip("/")
                
                # If it's an article, add to results
                if any(pattern in url for pattern in ["/artikler/", "/articles/"]):
                    # Avoid pagination and category pages
                    if not any(avoid in url for avoid in ["/page/", "/artikler/artikler", "/articles/articles"]):
                        article_urls.add(url)
                
                # If it looks like a listing page, queue it for crawling
                elif any(x in url for x in ["/artikler", "/articles", "/blog", "/inspiration"]):
                    if url not in visited and len(to_visit) < max_pages * 2:
                        to_visit.add(url)
            
            time.sleep(0.5)  # Be polite
            
        except Exception as e:
            print(f"  Error crawling {current}: {e}")
    
    print(f"  Found {len(article_urls)} unique article URLs")
    return sorted(article_urls)

def discover_via_hybrid(max_crawl_pages=200):
    """Combine sitemap and crawling for maximum coverage"""
    print("Method: Hybrid (Sitemap + Crawling)")
    
    all_urls = set()
    
    # Step 1: Get URLs from sitemap
    print("\n  Phase 1: Sitemap discovery...")
    sitemap_urls = set(discover_via_sitemap())  # Convert to set
    all_urls.update(sitemap_urls)
    print(f"  Sitemap found: {len(sitemap_urls)} URLs")
    
    # Step 2: Crawl for additional URLs
    print("\n  Phase 2: Web crawling for missed content...")
    crawl_urls = set(discover_via_crawl(max_pages=max_crawl_pages))  # Convert to set
    new_from_crawl = crawl_urls - all_urls
    all_urls.update(new_from_crawl)
    print(f"  Crawling found: {len(new_from_crawl)} additional URLs")
    
    print(f"\n  Total unique URLs: {len(all_urls)}")
    return sorted(all_urls)
    """Load URLs from a text file (one URL per line)"""
    print(f"Method: Loading from file '{url_file}'")
    
    try:
        with open(url_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return sorted(set(urls))
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

# ============================================================================
# METADATA EXTRACTION
# ============================================================================

def extract_meta(url):
    """Extract metadata from article page"""
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Determine language from URL
        language = ""
        if "/da/" in url.lower():
            language = "DA"
        elif "/en/" in url.lower():
            language = "EN"
        else:
            # Fallback: check if it's Danish or English based on domain structure
            if "/artikler/" in url.lower():
                language = "DA"
            elif "/articles/" in url.lower():
                language = "EN"
        
        # Extract title
        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        else:
            title = url.split("/")[-1].replace("-", " ").title()
        
        # Extract date created (published)
        date_created = ""
        date_pub_meta = (
            soup.find("meta", attrs={"property": "article:published_time"}) or
            soup.find("meta", attrs={"name": "date"}) or
            soup.find("meta", attrs={"property": "og:published_time"}) or
            soup.find("meta", attrs={"name": "publishdate"})
        )
        if date_pub_meta and date_pub_meta.has_attr("content"):
            date_created = date_pub_meta["content"][:10]
        
        # Extract date modified
        date_modified = ""
        date_mod_meta = (
            soup.find("meta", attrs={"property": "article:modified_time"}) or
            soup.find("meta", attrs={"property": "og:updated_time"}) or
            soup.find("meta", attrs={"name": "last-modified"})
        )
        if date_mod_meta and date_mod_meta.has_attr("content"):
            date_modified = date_mod_meta["content"][:10]
        
        # Extract tags
        tags = []
        
        keywords_meta = soup.find("meta", attrs={"name": "keywords"})
        if keywords_meta and keywords_meta.has_attr("content"):
            tags.extend([t.strip() for t in keywords_meta["content"].split(",")])
        
        article_tags = soup.find_all("meta", attrs={"property": "article:tag"})
        for tag in article_tags:
            if tag.has_attr("content"):
                tags.append(tag["content"].strip())
        
        tag_elements = soup.find_all(class_=lambda x: x and any(
            term in x.lower() for term in ["tag", "category", "label", "keyword"]
        ))
        for elem in tag_elements:
            tag_text = elem.get_text(strip=True)
            if tag_text and len(tag_text) < 50:
                tags.append(tag_text)
        
        tags = list(set([t for t in tags if t]))
        tags_str = "; ".join(tags) if tags else ""
        
        return {
            "url": url,
            "language": language,
            "title": title,
            "date_created": date_created,
            "date_modified": date_modified,
            "tags": tags_str,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"  Error: {e}")
        return {
            "url": url,
            "language": "",
            "title": "",
            "date_created": "",
            "date_modified": "",
            "tags": "",
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# ============================================================================
# DATA MERGING AND MANAGEMENT
# ============================================================================

def load_existing_data(csv_path):
    """Load existing scraped data"""
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            print(f"Loaded {len(df)} existing records from {csv_path}")
            return df
        except Exception as e:
            print(f"Error loading existing data: {e}")
            return pd.DataFrame()
    else:
        print("No existing data found")
        return pd.DataFrame()

def merge_data(existing_df, new_df, merge_strategy="update"):
    """
    Merge new data with existing data
    
    Args:
        existing_df: Existing DataFrame
        new_df: New DataFrame with scraped data
        merge_strategy: How to handle duplicates
            - "skip": Keep existing data, ignore new data for duplicate URLs
            - "update": Update existing records with new data
            - "append": Keep both old and new (creates duplicates)
    """
    if existing_df.empty:
        return new_df
    
    print(f"\nMerging strategy: {merge_strategy}")
    
    # Ensure 'url' column exists and is used as key
    if 'url' not in existing_df.columns or 'url' not in new_df.columns:
        print("Warning: 'url' column missing. Cannot merge properly.")
        return pd.concat([existing_df, new_df], ignore_index=True)
    
    if merge_strategy == "skip":
        # Keep existing, only add truly new URLs
        existing_urls = set(existing_df['url'].values)
        new_only = new_df[~new_df['url'].isin(existing_urls)]
        print(f"  Added {len(new_only)} new records")
        print(f"  Skipped {len(new_df) - len(new_only)} existing records")
        return pd.concat([existing_df, new_only], ignore_index=True)
    
    elif merge_strategy == "update":
        # Update existing records with new data, add new records
        merged = existing_df.copy()
        
        for _, new_row in new_df.iterrows():
            url = new_row['url']
            mask = merged['url'] == url
            
            if mask.any():
                # Update existing record
                for col in new_df.columns:
                    if col != 'url' and new_row[col]:  # Don't overwrite with empty values
                        merged.loc[mask, col] = new_row[col]
            else:
                # Add new record
                merged = pd.concat([merged, new_row.to_frame().T], ignore_index=True)
        
        print(f"  Updated/added {len(new_df)} records")
        return merged
    
    elif merge_strategy == "append":
        # Keep everything (allows duplicates)
        print(f"  Appended {len(new_df)} records (duplicates possible)")
        return pd.concat([existing_df, new_df], ignore_index=True)
    
    else:
        print(f"Unknown strategy '{merge_strategy}', defaulting to 'update'")
        return merge_data(existing_df, new_df, "update")

def merge_with_external_source(df, external_csv, key_column="url"):
    """
    Merge scraped data with external data source
    
    Args:
        df: Current DataFrame
        external_csv: Path to external CSV file
        key_column: Column to use as merge key (default: "url")
    """
    try:
        external_df = pd.read_csv(external_csv, encoding='utf-8')
        print(f"\nMerging with external source: {external_csv}")
        print(f"  External records: {len(external_df)}")
        
        if key_column not in df.columns or key_column not in external_df.columns:
            print(f"Error: Key column '{key_column}' not found in both datasets")
            return df
        
        # Perform outer join to keep all records
        merged = pd.merge(df, external_df, on=key_column, how='outer', 
                         suffixes=('', '_external'))
        
        print(f"  Merged result: {len(merged)} total records")
        return merged
        
    except Exception as e:
        print(f"Error merging with external source: {e}")
        return df

# ============================================================================
# CSV EXPORT
# ============================================================================

def save_csv(df, output_file):
    """Save dataframe to CSV with proper formatting"""
    if df.empty:
        print("No data to save to CSV")
        return
    
    try:
        # Select and order columns for export
        export_columns = ['url', 'language', 'title', 'date_created', 'date_modified', 'tags', 'scraped_at']
        
        # Only include columns that exist in the dataframe
        available_columns = [col for col in export_columns if col in df.columns]
        df_export = df[available_columns].copy()
        
        # Ensure all columns are strings to avoid comparison issues
        for col in df_export.columns:
            df_export[col] = df_export[col].astype(str)
            # Replace 'nan' string with empty string
            df_export[col] = df_export[col].replace('nan', '')
        
        # Save to CSV
        df_export.to_csv(output_file, index=False, encoding='utf-8')
        print(f"CSV saved: {output_file} ({len(df_export)} records)")
        
        # Show summary statistics
        if 'language' in df_export.columns:
            lang_counts = df_export[df_export['language'] != '']['language'].value_counts()
            if not lang_counts.empty:
                print(f"  Languages: {dict(lang_counts)}")
        
        if 'date_created' in df_export.columns:
            dates_with_data = df_export[df_export['date_created'] != '']
            if not dates_with_data.empty:
                try:
                    print(f"  Date range: {dates_with_data['date_created'].min()} to {dates_with_data['date_created'].max()}")
                except:
                    pass  # Skip if comparison fails
        
        if 'tags' in df_export.columns:
            with_tags = df_export[df_export['tags'] != ''].shape[0]
            print(f"  Articles with tags: {with_tags}/{len(df_export)}")
        
    except Exception as e:
        print(f"Error saving CSV: {e}")

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main():
    print("=" * 70)
    print("MANNAZ ARTICLE SCRAPER - Flexible Mode")
    print("=" * 70)
    
    # Step 1: Choose URL discovery method
    print("\nURL Discovery Methods:")
    print("  1. Sitemap (recommended)")
    print("  2. Web crawling (slower, may find more)")
    print("  3. Hybrid (sitemap + crawling - BEST coverage)")
    print("  4. Manual URL list from file")
    print("  5. Skip discovery (use existing data only)")
    
    choice = input("\nChoose method (1-5): ").strip()
    
    urls = []
    if choice == "1":
        urls = discover_via_sitemap()
    elif choice == "2":
        max_pages = input("Max pages to crawl (default 100): ").strip()
        max_pages = int(max_pages) if max_pages else 100
        urls = discover_via_crawl(max_pages=max_pages)
    elif choice == "3":
        max_pages = input("Max pages to crawl (default 200): ").strip()
        max_pages = int(max_pages) if max_pages else 200
        urls = discover_via_hybrid(max_crawl_pages=max_pages)
    elif choice == "5":
        print("Skipping URL discovery")
    else:
        print("Invalid choice, using sitemap")
        urls = discover_via_sitemap()
    
    print(f"\nDiscovered {len(urls)} URLs")
    
    # Step 2: Check for existing data
    existing_df = load_existing_data(OUT_CSV)
    
    if not existing_df.empty and urls:
        print("\nExisting data found. How to handle new URLs?")
        print("  1. Skip URLs already in database")
        print("  2. Update existing records with fresh data")
        print("  3. Append all (keep duplicates)")
        
        strategy_choice = input("Choose (1-3, default=1): ").strip()
        strategy_map = {"1": "skip", "2": "update", "3": "append", "": "skip"}
        merge_strategy = strategy_map.get(strategy_choice, "skip")
        
        # Filter URLs if skipping
        if merge_strategy == "skip" and 'url' in existing_df.columns:
            existing_urls = set(existing_df['url'].values)
            new_urls = [u for u in urls if u not in existing_urls]
            print(f"Filtering: {len(urls)} total → {len(new_urls)} new URLs")
            urls = new_urls
    else:
        merge_strategy = "update"
    
    # Step 3: Scrape new URLs
    if urls:
        print(f"\nScraping {len(urls)} articles...")
        rows = []
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            rows.append(extract_meta(url))
            time.sleep(0.5)
        
        new_df = pd.DataFrame(rows)
        
        # Merge with existing data
        final_df = merge_data(existing_df, new_df, merge_strategy)
    else:
        final_df = existing_df
    
    # Step 4: Optional external merge
    if not final_df.empty:
        external_merge = input("\nMerge with external CSV? (y/n): ").strip().lower()
        if external_merge == 'y':
            external_file = input("Enter external CSV path: ").strip()
            if os.path.exists(external_file):
                final_df = merge_with_external_source(final_df, external_file)
            else:
                print(f"File not found: {external_file}")
    
    # Step 5: Save results
    if not final_df.empty:
        # Sort by date
        if 'date_created' in final_df.columns:
            final_df = final_df.sort_values("date_created", ascending=False)
        
        # Save to CSV
        save_csv(final_df, OUT_CSV)
    else:
        print("\nNo data to save")
    
    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()