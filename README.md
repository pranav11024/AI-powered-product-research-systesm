# Product Research & Analysis System (n8n + AI/ML)

A fully local, AI-powered product research platform that integrates web scraping, price tracking, review sentiment analysis, product clustering, and an interactive dashboard — all orchestrated with [n8n](https://n8n.io/). No cloud services required.

---

## Features

| Module            | Capabilities                                                                 |
|-------------------|------------------------------------------------------------------------------|
| Data Ingestion     | Scrape product data and reviews from websites, import via API or CSV/JSON   |
| AI/ML Analysis     | Sentiment analysis, keyword extraction, price trend forecasting, clustering  |
| Orchestration      | Automated pipelines using n8n workflows                                      |
| Storage            | PostgreSQL with schema for products, reviews, analytics, trends             |
| Visualization      | Real-time dashboard with interactive charts and tables                      |
| Local Deployment   | Offline-ready, no external services, minimal resource usage                 |

---

## Prerequisites

- Windows 10/11
- Node.js v16+
- PostgreSQL
- Python 3.8+
- Git

---

## Setup Instructions

### 1. Install Required Packages

```bash
npm install -g n8n

pip install -r requirements.txt
```
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"
2. Initialize the Database
Use psql to run the provided schema script (see product_research_system.md) to create:

products

reviews

price_history

product_analytics

search_trends

3. Configure Services
ml_service.py: Flask-based ML/NLP service

scraper_service.py: Product/review scraper

api_server.py: REST API + dashboard backend

dashboard.html: UI for insights

product_research_workflow.json: n8n workflow for automation

4. Launch the System
Run the Windows startup script:

c
Copy
Edit
start_services.bat
This starts:

ML Service (http://127.0.0.1:5000)

Scraper Service (http://127.0.0.1:5001)

API Server & Dashboard (http://127.0.0.1:8000)

n8n Editor (http://127.0.0.1:5678)

Dashboard Access
Dashboard: http://127.0.0.1:8000

n8n Editor: http://127.0.0.1:5678

Adding Products via API
bash
Copy
Edit
curl -X POST http://127.0.0.1:8000/api/products/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample Product",
    "brand": "Sample Brand",
    "category": "Electronics",
    "price": 99.99,
    "url": "https://example.com/product",
    "description": "Sample product description"
  }'



├── ml_service.py                  # ML & NLP backend
├── scraper_service.py             # Product and review scraper
├── api_server.py                  # Dashboard + REST API
├── dashboard.html                 # Frontend dashboard
├── product_research_workflow.json# n8n automation workflow
├── start_services.bat            # Windows startup script
├── requirements.txt              # Python package dependencies
└── README.md                     # Project documentation
