from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import psycopg2
import json
from datetime import datetime, timedelta
import re
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="product_research",
        user="postgres",
        password="your_password"  # Replace with your PostgreSQL password
    )

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

@app.route('/analyze_sentiment', methods=['POST'])
def analyze_sentiment():
    try:
        data = request.json
        text = data.get('text', '')
        
        # TextBlob sentiment
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        # NLTK VADER sentiment
        vader_scores = sia.polarity_scores(text)
        
        # Combined sentiment score
        combined_score = (polarity + vader_scores['compound']) / 2
        
        # Determine sentiment label
        if combined_score > 0.1:
            sentiment = 'positive'
        elif combined_score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return jsonify({
            'sentiment_score': round(combined_score, 2),
            'sentiment_label': sentiment,
            'confidence': abs(combined_score)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/extract_features', methods=['POST'])
def extract_features():
    try:
        data = request.json
        reviews = data.get('reviews', [])
        
        if not reviews:
            return jsonify({'features': []})
        
        # Combine all reviews
        all_text = ' '.join(reviews)
        
        # Extract features using TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=20,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform([all_text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get top features
        feature_scores = list(zip(feature_names, scores))
        feature_scores.sort(key=lambda x: x[1], reverse=True)
        
        return jsonify({
            'features': [{'feature': f[0], 'score': round(f[1], 3)} for f in feature_scores[:10]]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict_price_trend', methods=['POST'])
def predict_price_trend():
    try:
        data = request.json
        product_id = data.get('product_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get price history
        cursor.execute("""
            SELECT price, recorded_at 
            FROM price_history 
            WHERE product_id = %s 
            ORDER BY recorded_at
        """, (product_id,))
        
        price_data = cursor.fetchall()
        
        if len(price_data) < 3:
            return jsonify({'trend': 'insufficient_data', 'prediction': None})
        
        # Prepare data for prediction
        df = pd.DataFrame(price_data, columns=['price', 'date'])
        df['days'] = (df['date'] - df['date'].min()).dt.days
        
        # Linear regression for trend prediction
        X = df[['days']].values
        y = df['price'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next 30 days
        future_days = df['days'].max() + 30
        predicted_price = model.predict([[future_days]])[0]
        
        # Determine trend
        slope = model.coef_[0]
        if slope > 0.1:
            trend = 'increasing'
        elif slope < -0.1:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'trend': trend,
            'prediction': round(predicted_price, 2),
            'confidence': min(0.95, abs(slope) * 10)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cluster_products', methods=['POST'])
def cluster_products():
    try:
        data = request.json
        category = data.get('category', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get products in category
        cursor.execute("""
            SELECT id, name, description, price 
            FROM products 
            WHERE category = %s AND description IS NOT NULL
        """, (category,))
        
        products = cursor.fetchall()
        
        if len(products) < 3:
            return jsonify({'clusters': []})
        
        # Prepare text data
        df = pd.DataFrame(products, columns=['id', 'name', 'description', 'price'])
        descriptions = df['description'].fillna('').tolist()
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(descriptions)
        
        # K-means clustering
        n_clusters = min(5, len(products) // 2)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        # Group products by cluster
        cluster_groups = {}
        for i, cluster_id in enumerate(clusters):
            if cluster_id not in cluster_groups:
                cluster_groups[cluster_id] = []
            cluster_groups[cluster_id].append({
                'id': products[i][0],
                'name': products[i][1],
                'price': float(products[i][3]) if products[i][3] else 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'clusters': cluster_groups})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_insights', methods=['POST'])
def generate_insights():
    try:
        data = request.json
        product_id = data.get('product_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get product details
        cursor.execute("""
            SELECT p.name, p.category, p.price, p.description,
                   COUNT(r.id) as review_count,
                   AVG(r.rating) as avg_rating,
                   AVG(r.sentiment_score) as avg_sentiment
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.id = %s
            GROUP BY p.id, p.name, p.category, p.price, p.description
        """, (product_id,))
        
        product_data = cursor.fetchone()
        
        if not product_data:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get recent reviews for analysis
        cursor.execute("""
            SELECT review_text, sentiment_label, rating
            FROM reviews
            WHERE product_id = %s
            ORDER BY scraped_at DESC
            LIMIT 50
        """, (product_id,))
        
        reviews = cursor.fetchall()
        
        # Generate insights
        insights = {
            'product_name': product_data[0],
            'category': product_data[1],
            'price': float(product_data[2]) if product_data[2] else 0,
            'review_count': product_data[4],
            'avg_rating': round(float(product_data[5]), 2) if product_data[5] else 0,
            'avg_sentiment': round(float(product_data[6]), 2) if product_data[6] else 0,
            'insights': []
        }
        
        # Add specific insights based on data
        if product_data[4] > 100:
            insights['insights'].append("High review volume indicates strong market presence")
        
        if product_data[5] and float(product_data[5]) > 4.0:
            insights['insights'].append("Excellent customer satisfaction with high ratings")
        elif product_data[5] and float(product_data[5]) < 3.0:
            insights['insights'].append("Below average ratings suggest quality concerns")
        
        if product_data[6] and float(product_data[6]) > 0.3:
            insights['insights'].append("Positive sentiment indicates customer satisfaction")
        elif product_data[6] and float(product_data[6]) < -0.3:
            insights['insights'].append("Negative sentiment indicates customer dissatisfaction")
        
        # Analyze review patterns
        if reviews:
            positive_reviews = sum(1 for r in reviews if r[1] == 'positive')
            negative_reviews = sum(1 for r in reviews if r[1] == 'negative')
            
            if positive_reviews > negative_reviews * 2:
                insights['insights'].append("Strong positive review momentum")
            elif negative_reviews > positive_reviews:
                insights['insights'].append("Concerning negative review trend")
        
        cursor.close()
        conn.close()
        
        return jsonify(insights)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)