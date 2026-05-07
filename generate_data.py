#!/usr/bin/env python3
"""
Dev Pulse — Live Engineering News Generator
Fetches specialized news for software engineers across 6 categories using NewsAPI.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

NEWS_API_KEY = os.getenv('NEWS_API_KEY')
DATA_DIR = Path(__file__).parent / "data"

# Specialized queries for each engineer-focused category
CATEGORIES = {
    'ai-coding': {
        'query': '"GitHub Copilot" OR "Claude Code" OR "Cursor IDE" OR "Windsurf" OR "Codeium" OR "AI coding assistant" OR "Copilot CLI"',
        'limit': 8
    },
    'testing': {
        'query': '("AI testing" OR "test automation" OR "Playwright" OR "Selenium" OR "Cypress" OR "self-healing tests" OR "visual regression") AND (software OR engineering)',
        'limit': 6
    },
    'microservices': {
        'query': '"microservices" OR "service mesh" OR "Istio" OR "Linkerd" OR "OpenTelemetry" OR "API gateway" OR "distributed systems"',
        'limit': 6
    },
    'fintech': {
        'query': '("Stripe" OR "Mastercard" OR "Visa" OR "Adyen" OR "PayPal" OR "FedNow" OR "real-time payments" OR "PCI DSS" OR "tokenization") AND (engineering OR developer OR API OR security)',
        'limit': 6
    },
    'devprod': {
        'query': '"developer productivity" OR "platform engineering" OR "Backstage" OR "DORA metrics" OR "internal developer platform" OR "CI/CD"',
        'limit': 6
    },
    'security': {
        'query': '"supply chain attack" OR "npm vulnerability" OR "PyPI package" OR "CVE" OR "secrets management" OR "prompt injection" OR "AI security"',
        'limit': 8
    }
}

def fetch_category_news(category_key, query, limit):
    """Fetch news for a single category"""
    if not NEWS_API_KEY:
        print(f"⚠️  NEWS_API_KEY not set, skipping {category_key}")
        return []

    try:
        # Get articles from last 7 days for fresher content
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': limit,
            'from': from_date,
            'apiKey': NEWS_API_KEY
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        articles = data.get('articles', [])

        items = []
        for article in articles:
            if not article.get('title') or article.get('title') == '[Removed]':
                continue

            published_at = article.get('publishedAt', '')
            try:
                ts = datetime.fromisoformat(published_at.replace('Z', '+00:00')).isoformat()
            except Exception:
                ts = datetime.now().isoformat()

            items.append({
                'title': article.get('title', '')[:150],
                'source': article.get('source', {}).get('name', 'Unknown'),
                'category': category_key,
                'excerpt': (article.get('description') or article.get('content') or '')[:280],
                'url': article.get('url', '#'),
                'image': article.get('urlToImage'),
                'date': datetime.now().strftime('%b %d, %I:%M %p'),
                'timestamp': ts,
                'published_at': published_at
            })

        print(f"✅ {category_key}: fetched {len(items)} articles")
        return items

    except Exception as e:
        print(f"❌ {category_key}: {e}")
        return []

def generate_news():
    """Fetch news across all 6 engineering categories"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_articles = []
    for category_key, config in CATEGORIES.items():
        articles = fetch_category_news(category_key, config['query'], config['limit'])
        all_articles.extend(articles)

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique.append(article)

    # Sort by published date (newest first)
    unique.sort(key=lambda x: x.get('published_at', ''), reverse=True)

    # Save to data/news.json
    output_file = DATA_DIR / "news.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Total: {len(unique)} unique articles saved to {output_file}")

    # Print breakdown by category
    breakdown = {}
    for article in unique:
        cat = article['category']
        breakdown[cat] = breakdown.get(cat, 0) + 1

    print("\n📂 Breakdown by category:")
    for cat, count in sorted(breakdown.items()):
        print(f"   {cat}: {count}")

    return unique

if __name__ == "__main__":
    print("🚀 Dev Pulse — fetching live engineering news...\n")
    generate_news()
    print("\n✅ Done!")
