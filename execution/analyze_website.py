import argparse
import sys
import json
import urllib.request
from urllib.parse import urlparse
import re

def analyze_website(url):
    """
    Analyzes a website for basic text content and CSS references.
    In a full implementation, this would use BeautifulSoup, Playwright, etc.
    """
    try:
        # Basic URL validation
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = 'https://' + url

        print(f"Analyzing {url}...")
        
        # In a real scenario, use requests and bs4
        # For this script, we'll simulate output or use urllib simply
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Rough extraction of title
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        title = title_match.group(1) if title_match else "No Title Found"

        # Look for hex color codes in the HTML
        colors = list(set(re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}(?:\b|[^a-zA-Z0-9])', html)))
        colors = [c.strip('^a-zA-Z0-9') for c in colors][:10]  # Just take up to 10

        result = {
            "status": "success",
            "url": url,
            "title": title.strip(),
            "extracted_colors_hex": colors,
            "html_length": len(html),
            "recommendation": "Use these colors to map competitor palette. Analyze title to determine positioning."
        }
        
        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a website for design elements.")
    parser.add_argument("url", help="The URL of the website to analyze")
    args = parser.parse_args()
    
    output = analyze_website(args.url)
    print(output)
