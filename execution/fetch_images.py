import argparse
import json
import os
import urllib.request

# In a real environment, you'd load this from .env or OS environment
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "DEMO_KEY")

def fetch_images(query, count=5):
    """
    Fetches image URLs from Unsplash based on a search query.
    """
    print(f"Fetching {count} images for query: '{query}'")
    
    if UNSPLASH_ACCESS_KEY == "DEMO_KEY" or not UNSPLASH_ACCESS_KEY:
        # Return mock data if no key is provided to avoid failing in the demo
        print("Warning: No UNSPLASH_ACCESS_KEY found. Returning mock image data.")
        mock_images = [
            {"id": f"mock_{i}", "url": f"https://source.unsplash.com/random/800x600/?{urllib.parse.quote(query)}&sig={i}", "description": f"Mock image for {query}"}
            for i in range(count)
        ]
        return json.dumps({"status": "success", "images": mock_images}, indent=2)

    try:
        # Actual Unsplash API implementation
        url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(query)}&per_page={count}"
        req = urllib.request.Request(url, headers={
            'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        images = []
        for item in data.get('results', []):
            images.append({
                "id": item['id'],
                "url": item['urls']['regular'],
                "description": item['alt_description'] or item['description']
            })
            
        return json.dumps({"status": "success", "images": images}, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch images from Unsplash API.")
    parser.add_argument("query", help="Search query for images")
    parser.add_argument("--count", type=int, default=5, help="Number of images to fetch")
    args = parser.parse_args()
    
    output = fetch_images(args.query, args.count)
    print(output)
