import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
from urllib.parse import urljoin, quote
import csv
from datetime import datetime
import os

class IndianProductScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.products = []
        
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        text = text.replace('"', '\\"')
        text = text.replace('\n', ' ')
        return text[:200] if len(text) > 200 else text
    
    def extract_price(self, price_text):
        """Extract price from text"""
        if not price_text:
            return None
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        return float(price_match.group()) if price_match else None
    
    def scrape_snapdeal_products(self, categories, max_products=10):
        """Scrape products from Snapdeal"""
        print("Scraping Snapdeal...")
        
        category_urls = {
            'Electronics': 'https://www.snapdeal.com/products/mobiles-mobile-phones',
            'Fashion': 'https://www.snapdeal.com/products/mens-clothing',
            'Home': 'https://www.snapdeal.com/products/home-kitchen',
            'Books': 'https://www.snapdeal.com/products/books',
            'Sports': 'https://www.snapdeal.com/products/sports-fitness'
        }
        
        for category in categories:
            if category not in category_urls:
                continue
                
            try:
                response = self.session.get(category_urls[category], timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product containers
                products = soup.find_all('div', class_='product-tuple-listing')[:max_products//len(categories)]
                
                for product in products:
                    try:
                        # Extract product details
                        name_elem = product.find('p', class_='product-title')
                        price_elem = product.find('span', class_='lfloat product-price')
                        link_elem = product.find('a')
                        img_elem = product.find('img')
                        
                        if name_elem and price_elem and link_elem:
                            product_data = {
                                'name': self.clean_text(name_elem.get_text()),
                                'price': self.extract_price(price_elem.get_text()),
                                'url': urljoin('https://www.snapdeal.com', link_elem.get('href', '')),
                                'image_url': img_elem.get('src', '') if img_elem else '',
                                'category': category,
                                'brand': 'Unknown',
                                'source': 'Snapdeal',
                                'source_id': f"SD_{random.randint(100000, 999999)}"
                            }
                            
                            if product_data['name'] and product_data['price']:
                                self.products.append(product_data)
                                print(f"Added: {product_data['name']}")
                    
                    except Exception as e:
                        print(f"Error processing Snapdeal product: {e}")
                        continue
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error scraping Snapdeal category {category}: {e}")
    
    def scrape_paytmmall_products(self, categories, max_products=10):
        """Scrape products from Paytm Mall"""
        print("Scraping Paytm Mall...")
        
        # Paytm Mall search URLs
        search_terms = {
            'Electronics': 'mobile phone',
            'Fashion': 'mens shirt',
            'Home': 'kitchen appliances',
            'Books': 'fiction books',
            'Sports': 'fitness equipment'
        }
        
        for category in categories:
            if category not in search_terms:
                continue
                
            try:
                search_url = f"https://paytmmall.com/shop/search?q={quote(search_terms[category])}"
                response = self.session.get(search_url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product containers (Paytm Mall structure)
                products = soup.find_all('div', attrs={'data-testid': 'product-item'})[:max_products//len(categories)]
                
                for product in products:
                    try:
                        name_elem = product.find('h2') or product.find('a', class_='_3jz7')
                        price_elem = product.find('span', class_='_1kMS') or product.find('div', class_='_1kMS')
                        link_elem = product.find('a')
                        img_elem = product.find('img')
                        
                        if name_elem and price_elem:
                            product_data = {
                                'name': self.clean_text(name_elem.get_text()),
                                'price': self.extract_price(price_elem.get_text()),
                                'url': urljoin('https://paytmmall.com', link_elem.get('href', '')) if link_elem else '',
                                'image_url': img_elem.get('src', '') if img_elem else '',
                                'category': category,
                                'brand': 'Unknown',
                                'source': 'PaytmMall',
                                'source_id': f"PM_{random.randint(100000, 999999)}"
                            }
                            
                            if product_data['name'] and product_data['price']:
                                self.products.append(product_data)
                                print(f"Added: {product_data['name']}")
                    
                    except Exception as e:
                        print(f"Error processing Paytm Mall product: {e}")
                        continue
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error scraping Paytm Mall category {category}: {e}")
    
    def scrape_shopclues_products(self, categories, max_products=10):
        """Scrape products from ShopClues"""
        print("Scraping ShopClues...")
        
        category_urls = {
            'Electronics': 'https://www.shopclues.com/mobiles-tablets.html',
            'Fashion': 'https://www.shopclues.com/mens-clothing.html',
            'Home': 'https://www.shopclues.com/home-kitchen.html',
            'Books': 'https://www.shopclues.com/books-media.html',
            'Sports': 'https://www.shopclues.com/sports-fitness.html'
        }
        
        for category in categories:
            if category not in category_urls:
                continue
                
            try:
                response = self.session.get(category_urls[category], timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product containers
                products = soup.find_all('div', class_='column')[:max_products//len(categories)]
                
                for product in products:
                    try:
                        name_elem = product.find('h2') or product.find('a', class_='pname')
                        price_elem = product.find('span', class_='p_price') or product.find('div', class_='price')
                        link_elem = product.find('a')
                        img_elem = product.find('img')
                        
                        if name_elem and price_elem:
                            product_data = {
                                'name': self.clean_text(name_elem.get_text()),
                                'price': self.extract_price(price_elem.get_text()),
                                'url': urljoin('https://www.shopclues.com', link_elem.get('href', '')) if link_elem else '',
                                'image_url': img_elem.get('src', '') if img_elem else '',
                                'category': category,
                                'brand': 'Unknown',
                                'source': 'ShopClues',
                                'source_id': f"SC_{random.randint(100000, 999999)}"
                            }
                            
                            if product_data['name'] and product_data['price']:
                                self.products.append(product_data)
                                print(f"Added: {product_data['name']}")
                    
                    except Exception as e:
                        print(f"Error processing ShopClues product: {e}")
                        continue
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error scraping ShopClues category {category}: {e}")
    
    def add_sample_products(self):
        """Add sample Indian market products with realistic data"""
        sample_products = [
            {
                'name': 'Samsung Galaxy M32 128GB',
                'brand': 'Samsung',
                'category': 'Electronics',
                'price': 16999.0,
                'url': 'https://www.samsung.com/in/smartphones/galaxy-m/galaxy-m32/',
                'image_url': 'https://images.samsung.com/is/image/samsung/in-galaxy-m32-m325f-sm-m325flvginu-531345803',
                'source': 'Samsung',
                'source_id': 'SAM_M32_128'
            },
            {
                'name': 'Redmi Note 11 Pro 6GB RAM',
                'brand': 'Xiaomi',
                'category': 'Electronics',
                'price': 18999.0,
                'url': 'https://www.mi.com/in/redmi-note-11-pro/',
                'image_url': 'https://i01.appmifile.com/webfile/globalimg/products/pc/redmi-note-11-pro/',
                'source': 'Xiaomi',
                'source_id': 'MI_RN11P_6GB'
            },
            {
                'name': 'OnePlus Nord CE 2 Lite 5G',
                'brand': 'OnePlus',
                'category': 'Electronics',
                'price': 19999.0,
                'url': 'https://www.oneplus.in/nord-ce-2-lite-5g',
                'image_url': 'https://oasis.opstatics.com/content/dam/oasis/page/2022/na/nord-ce-2-lite/',
                'source': 'OnePlus',
                'source_id': 'OP_NCE2L_5G'
            },
            {
                'name': 'Realme 9 Pro+ 8GB RAM',
                'brand': 'Realme',
                'category': 'Electronics',
                'price': 24999.0,
                'url': 'https://www.realme.com/in/realme-9-pro-plus',
                'image_url': 'https://image01.realme.net/general/20220216/1645003037824.jpg',
                'source': 'Realme',
                'source_id': 'RM_9PP_8GB'
            },
            {
                'name': 'Boat Airdopes 141 Bluetooth Earbuds',
                'brand': 'Boat',
                'category': 'Electronics',
                'price': 1999.0,
                'url': 'https://www.boat-lifestyle.com/products/airdopes-141',
                'image_url': 'https://cdn.shopify.com/s/files/1/0057/8938/4802/products/airdopes-141_1.png',
                'source': 'Boat',
                'source_id': 'BOAT_AD141'
            },
            {
                'name': 'JBL C100SI Wired Earphones',
                'brand': 'JBL',
                'category': 'Electronics',
                'price': 699.0,
                'url': 'https://in.jbl.com/headphones/C100SI.html',
                'image_url': 'https://in.jbl.com/dw/image/v2/AAUJ_PRD/on/demandware.static/',
                'source': 'JBL',
                'source_id': 'JBL_C100SI'
            },
            {
                'name': 'Levi\'s Men\'s Regular Fit Jeans',
                'brand': 'Levis',
                'category': 'Fashion',
                'price': 2799.0,
                'url': 'https://www.levi.in/men/clothing/jeans',
                'image_url': 'https://lsco.scene7.com/is/image/lsco/levis-501-original-jeans',
                'source': 'Levis',
                'source_id': 'LEVIS_501_REG'
            },
            {
                'name': 'Nike Air Max 270 Running Shoes',
                'brand': 'Nike',
                'category': 'Sports',
                'price': 12995.0,
                'url': 'https://www.nike.com/in/t/air-max-270-mens-shoe',
                'image_url': 'https://static.nike.com/a/images/t_PDP_1728_v1/f_auto,q_auto:eco/awjogtdnqxniqqk0vf4d/air-max-270-mens-shoe.png',
                'source': 'Nike',
                'source_id': 'NIKE_AM270'
            },
            {
                'name': 'Prestige Deluxe Alpha Pressure Cooker 5L',
                'brand': 'Prestige',
                'category': 'Home',
                'price': 2890.0,
                'url': 'https://www.prestigesmartcooking.com/products/deluxe-alpha-pressure-cooker',
                'image_url': 'https://www.prestigesmartcooking.com/cdn/shop/products/deluxe-alpha.jpg',
                'source': 'Prestige',
                'source_id': 'PRES_DA_5L'
            },
            {
                'name': 'Himalaya Herbals Face Wash Neem',
                'brand': 'Himalaya',
                'category': 'Beauty',
                'price': 140.0,
                'url': 'https://www.himalayawellness.in/products/purifying-neem-face-wash',
                'image_url': 'https://www.himalayawellness.in/cdn/shop/products/Neem-Face-Wash.jpg',
                'source': 'Himalaya',
                'source_id': 'HIM_NEEM_FW'
            },
            {
                'name': 'Tata Tea Premium 1kg Pack',
                'brand': 'Tata',
                'category': 'Grocery',
                'price': 385.0,
                'url': 'https://www.tatacommerce.com/products/tata-tea-premium',
                'image_url': 'https://www.tatacommerce.com/media/catalog/product/t/a/tata-tea-premium.jpg',
                'source': 'Tata',
                'source_id': 'TATA_TEA_1KG'
            },
            {
                'name': 'Amul Butter 500g Pack',
                'brand': 'Amul',
                'category': 'Grocery',
                'price': 265.0,
                'url': 'https://www.amul.com/products/butter',
                'image_url': 'https://www.amul.com/includes/images/products/amul-butter.jpg',
                'source': 'Amul',
                'source_id': 'AMUL_BUT_500G'
            },
            {
                'name': 'Godrej AC 1.5 Ton 3 Star Split',
                'brand': 'Godrej',
                'category': 'Home',
                'price': 32990.0,
                'url': 'https://www.godrej.com/godrej-appliances/air-conditioners',
                'image_url': 'https://www.godrej.com/sites/default/files/godrej-ac-split.jpg',
                'source': 'Godrej',
                'source_id': 'GOD_AC_15T'
            },
            {
                'name': 'LG 32 inch Smart TV HD Ready',
                'brand': 'LG',
                'category': 'Electronics',
                'price': 18990.0,
                'url': 'https://www.lg.com/in/tvs/lg-32lm563bptc',
                'image_url': 'https://gscs.lge.com/gscs/images/tv/lg-smart-tv.jpg',
                'source': 'LG',
                'source_id': 'LG_32_SMART'
            },
            {
                'name': 'Puma Men\'s Running T-Shirt',
                'brand': 'Puma',
                'category': 'Sports',
                'price': 1299.0,
                'url': 'https://in.puma.com/men/clothing/t-shirts',
                'image_url': 'https://images.puma.com/image/upload/f_auto,q_auto,b_rgb:fafafa/global/running-tshirt.jpg',
                'source': 'Puma',
                'source_id': 'PUMA_RUN_TEE'
            }
        ]
        
        self.products.extend(sample_products)
        print(f"Added {len(sample_products)} sample products")
    
    def generate_curl_statements(self, output_file='indian_products_curl.txt'):
        """Generate curl statements for all products"""
        if not self.products:
            print("No products found. Adding sample products...")
            self.add_sample_products()
        
        curl_statements = []
        
        for product in self.products:
            # Ensure all required fields are present
            name = product.get('name', 'Unknown Product')
            brand = product.get('brand', 'Unknown')
            category = product.get('category', 'General')
            price = product.get('price', 0.0)
            url = product.get('url', 'https://example.com/product')
            image_url = product.get('image_url', 'https://via.placeholder.com/300x200')
            source = product.get('source', 'Unknown')
            source_id = product.get('source_id', f"PROD_{random.randint(100000, 999999)}")
            
            # Create curl statement in the exact format requested
            curl_statement = f'curl.exe --% -X POST http://127.0.0.1:8000/api/products/add -H "Content-Type: application/json" -d "{{\\"name\\":\\"{name}\\",\\"brand\\":\\"{brand}\\",\\"category\\":\\"{category}\\",\\"price\\":{price},\\"source\\":\\"{source}\\",\\"source_id\\":\\"{source_id}\\",\\"url\\":\\"{url}\\",\\"image_url\\":\\"{image_url}\\"}}"'
            
            curl_statements.append(curl_statement)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Indian Market Products Curl Statements\n")
            f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total products: {len(curl_statements)}\n\n")
            
            for i, statement in enumerate(curl_statements, 1):
                f.write(f"# Product {i}\n")
                f.write(statement + "\n\n")
        
        print(f"Generated {len(curl_statements)} curl statements in {output_file}")
        return output_file
    
    def run_scraper(self, num_products=20):
        """Main method to run the scraper"""
        categories = ['Electronics', 'Fashion', 'Home', 'Sports', 'Beauty']
        
        print(f"Starting Indian Product Scraper for {num_products} products...")
        
        # Try scraping from multiple sources
        try:
            self.scrape_snapdeal_products(categories, num_products//3)
        except Exception as e:
            print(f"Snapdeal scraping failed: {e}")
        
        try:
            self.scrape_shopclues_products(categories, num_products//3)
        except Exception as e:
            print(f"ShopClues scraping failed: {e}")
        
        # Add sample products to ensure we have enough data
        if len(self.products) < num_products:
            print(f"Only {len(self.products)} products scraped. Adding sample products...")
            self.add_sample_products()
        
        # Generate curl statements
        output_file = self.generate_curl_statements()
        
        print(f"\nScraping completed!")
        print(f"Total products collected: {len(self.products)}")
        print(f"Curl statements saved to: {output_file}")
        
        return output_file

def main():
    scraper = IndianProductScraper()
    
    # Get number of products from user
    try:
        num_products = int(input("Enter number of products to scrape (default 20): ") or "20")
    except ValueError:
        num_products = 20
    
    # Run scraper
    output_file = scraper.run_scraper(num_products)
    
    print(f"\n{'='*50}")
    print(f"Scraping completed successfully!")
    print(f"Output file: {output_file}")
    print(f"You can now run the curl statements to add products to your system.")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()