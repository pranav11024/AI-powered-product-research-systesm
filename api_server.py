from flask import Flask, request, jsonify, render_template_string
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="product_research",
        user="postgres",
        password="postgres",  # Replace with your PostgreSQL password
        cursor_factory=RealDictCursor
    )

@app.route('/')
def dashboard():
    with open('dashboard.html', 'r') as f:
        return f.read()

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute("SELECT COUNT(*) as total_products FROM products")
        total_products = cursor.fetchone()['total_products']
        
        cursor.execute("SELECT COUNT(*) as total_reviews FROM reviews")
        total_reviews = cursor.fetchone()['total_reviews']
        
        cursor.execute("SELECT AVG(rating) as avg_rating FROM reviews WHERE rating IS NOT NULL")
        avg_rating = cursor.fetchone()['avg_rating'] or 0
        
        # Sentiment analysis
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
                COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral,
                COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative,
                COUNT(*) as total
            FROM reviews WHERE sentiment_label IS NOT NULL
        """)
        sentiment_data = cursor.fetchone()
        
        positive_percentage = 0
        if sentiment_data['total'] > 0:
            positive_percentage = (sentiment_data['positive'] / sentiment_data['total']) * 100
        
        # Price trend data (last 6 months)
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', recorded_at) as month,
                AVG(price) as avg_price
            FROM price_history 
            WHERE recorded_at >= NOW() - INTERVAL '6 months'
            GROUP BY DATE_TRUNC('month', recorded_at)
            ORDER BY month
        """)
        price_trend = cursor.fetchall()
        
        # Category distribution
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM products 
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        category_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'totalProducts': total_products,
            'totalReviews': total_reviews,
            'avgRating': float(avg_rating),
            'positiveSentiment': positive_percentage,
            'sentimentData': {
                'positive': sentiment_data['positive'],
                'neutral': sentiment_data['neutral'],
                'negative': sentiment_data['negative']
            },
            'priceData': {
                'labels': [item['month'].strftime('%b') for item in price_trend],
                'values': [float(item['avg_price']) if item['avg_price'] else 0 for item in price_trend]
            },
            'categoryData': {
                'labels': [item['category'] for item in category_data],
                'values': [item['count'] for item in category_data]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/products')
def get_dashboard_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, p.name, p.price, p.image_url, p.category,
                AVG(r.rating) as avg_rating,
                COUNT(r.id) as review_count,
                AVG(r.sentiment_score) as avg_sentiment
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            GROUP BY p.id, p.name, p.price, p.image_url, p.category
            ORDER BY p.updated_at DESC
            LIMIT 20
        """)
        
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert to list of dictionaries and handle None values
        result = []
        for product in products:
            result.append({
                'id': product['id'],
                'name': product['name'],
                'price': float(product['price']) if product['price'] else None,
                'image_url': product['image_url'],
                'category': product['category'],
                'avg_rating': float(product['avg_rating']) if product['avg_rating'] else 0,
                'review_count': product['review_count'],
                'avg_sentiment': float(product['avg_sentiment']) if product['avg_sentiment'] else 0
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/product/<int:product_id>')
def get_product_details(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get product details
        cursor.execute("""
            SELECT p.*, 
                   AVG(r.rating) as avg_rating,
                   COUNT(r.id) as review_count,
                   AVG(r.sentiment_score) as avg_sentiment
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.id = %s
            GROUP BY p.id
        """, (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get recent reviews
        cursor.execute("""
            SELECT reviewer_name, rating, review_text, sentiment_label, 
                   sentiment_score, review_date
            FROM reviews
            WHERE product_id = %s
            ORDER BY scraped_at DESC
            LIMIT 10
        """, (product_id,))
        
        reviews = cursor.fetchall()
        
        # Get price history
        cursor.execute("""
            SELECT price, recorded_at
            FROM price_history
            WHERE product_id = %s
            ORDER BY recorded_at DESC
            LIMIT 30
        """, (product_id,))
        
        price_history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'product': dict(product),
            'reviews': [dict(review) for review in reviews],
            'priceHistory': [dict(ph) for ph in price_history]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/add', methods=['POST'])
def add_product():
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO products (name, brand, category, price, url, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('name'),
            data.get('brand'),
            data.get('category'),
            data.get('price'),
            data.get('url'),
            data.get('description')
        ))
        
        product_id = cursor.fetchone()['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'id': product_id, 'message': 'Product added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/generate', methods=['POST'])
def generate_analysis():
    try:
        data = request.json
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'error': 'Product ID is required'}), 400
        
        # Call ML service to generate insights
        import requests
        response = requests.post('http://127.0.0.1:5000/generate_insights', 
                               json={'product_id': product_id})
        
        if response.status_code == 200:
            insights = response.json()
            
            # Save insights to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO product_analytics 
                (product_id, avg_rating, total_reviews, recommendation_score, analyzed_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (product_id) DO UPDATE SET
                avg_rating = EXCLUDED.avg_rating,
                total_reviews = EXCLUDED.total_reviews,
                recommendation_score = EXCLUDED.recommendation_score,
                analyzed_at = EXCLUDED.analyzed_at
            """, (
                product_id,
                insights.get('avg_rating', 0),
                insights.get('review_count', 0),
                insights.get('avg_sentiment', 0)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify(insights)
        else:
            return jsonify({'error': 'Failed to generate insights'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)