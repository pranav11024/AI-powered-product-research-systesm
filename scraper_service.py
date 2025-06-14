from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin, urlparse
import re

app = Flask(__name__)

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

@app.route('/scrape_product', methods=['POST'])
def scrape_product():
    try:
        data = request.json
        url = data.get('url')
        source = data.get('source', 'generic')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Generic scraping logic - customize based on source
        product_data = {
            'url': url,
            'source': source,
            'scraped_at': time.time()
        }
        
        # Extract basic information
        title_selectors = ['h1', '.product-title', '#product-title', '.title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                product_data['name'] = title_elem.get_text(strip=True)
                break
        
        # Extract price
        price_selectors = ['.price', '.product-price', '.current-price', '[data-testid="price"]']
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    product_data['price'] = float(price_match.group())
                break
        
        # Extract description
        desc_selectors = ['.description', '.product-description', '.product-details']
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                product_data['description'] = desc_elem.get_text(strip=True)[:500]
                break
        
        # Extract image
        img_selectors = ['.product-image img', '.main-image img', 'img[data-testid="product-image"]']
        for selector in img_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src')
                if img_src:
                    product_data['image_url'] = urljoin(url, img_src)
                break
        
        # Add delay to be respectful
        time.sleep(random.uniform(1, 3))
        
        return jsonify(product_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scrape_reviews', methods=['POST'])
def scrape_reviews():
    try:
        data = request.json
        url = data.get('url')
        max_reviews = data.get('max_reviews', 50)
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        reviews = []
        
        # Generic review extraction - customize based on source
        review_selectors = ['.review', '.review-item', '[data-testid="review"]']
        
        for selector in review_selectors:
            review_elements = soup.select(selector)[:max_reviews]
            
            for review_elem in review_elements:
                review_data = {}
                
                # Extract reviewer name
                name_elem = review_elem.select_one('.reviewer-name, .review-author, .name')
                if name_elem:
                    review_data['reviewer_name'] = name_elem.get_text(strip=True)
                
                # Extract rating
                rating_elem = review_elem.select_one('.rating, .stars, [data-testid="rating"]')
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+)', rating_text)
                    if rating_match:
                        review_data['rating'] = int(rating_match.group(1))
                
                # Extract review text
                text_elem = review_elem.select_one('.review-text, .review-content, .comment')
                if text_elem:
                    review_data['review_text'] = text_elem.get_text(strip=True)
                
                # Extract date
                date_elem = review_elem.select_one('.review-date, .date')
                if date_elem:
                    review_data['review_date'] = date_elem.get_text(strip=True)
                
                if review_data.get('review_text'):
                    reviews.append(review_data)
            
            if reviews:
                break
        
        time.sleep(random.uniform(1, 3))
        
        return jsonify({'reviews': reviews})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)