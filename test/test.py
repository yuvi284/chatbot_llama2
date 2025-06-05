import requests
from bs4 import BeautifulSoup
import json

def scrape_zepto(query):
    # Updated URL with RSC parameter
    url = f"https://www.zeptonow.com/search?query={query}&_rsc=lyx1p"
    
    # Enhanced headers based on the request you shared
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.zeptonow.com/search?query={query}",
        "Sec-Ch-Ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=1, i",
        "Rsc": "1",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Request failed with status code: {response.status_code}")
            return []
        
        # Check if response contains JSON data
        if response.headers.get('content-type') == 'text/x-component':
            try:
                # The actual product data might be in the JSON payload
                data = json.loads(response.text)
                if 'products' in data:
                    return [{
                        "name": p.get('name', 'N/A'),
                        "price": p.get('price', {}).get('formatted', 'N/A'),
                        "quantity": p.get('weight', 'N/A')
                    } for p in data['products']]
            except json.JSONDecodeError:
                pass  # Not JSON, continue with HTML parsing
        
        # HTML parsing fallback
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        
        # Try to find script tags containing JSON data
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
                    products.extend([{
                        "name": item.get('name', 'N/A'),
                        "price": item.get('offers', {}).get('price', 'N/A'),
                        "quantity": item.get('description', 'N/A')
                    } for item in data])
            except json.JSONDecodeError:
                continue
        
        # If no JSON data found, try direct HTML parsing
        if not products:
            product_cards = soup.find_all('div', class_=lambda x: x and 'ProductCard' in x)
            for card in product_cards:
                try:
                    name = card.find('div', class_=lambda x: x and 'ProductName' in x).text.strip()
                    price = card.find('div', class_=lambda x: x and 'Price' in x).text.strip()
                    quantity = card.find('div', class_=lambda x: x and 'Weight' in x).text.strip() if card.find('div', class_=lambda x: x and 'Weight' in x) else "N/A"
                    products.append({"name": name, "price": price, "quantity": quantity})
                except Exception as e:
                    print(f"Error processing product card: {e}")
                    continue
        
        return products
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []

if __name__ == '__main__':
    query = "milk"
    results = scrape_zepto(query)
    
    print(f"\nFound {len(results)} products for '{query}':")
    for idx, product in enumerate(results, 1):
        print(f"{idx}. {product['name']} - {product['price']} ({product['quantity']})") 