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
# Strategy: scope each query with technical/engineering context to filter noise
CATEGORIES = {
    'ai-coding': {
        'query': '("GitHub Copilot" OR "Claude Code" OR "Cursor" OR "Windsurf" OR "Codeium" OR "AI coding assistant" OR "Copilot CLI" OR "AI pair programming") AND (developer OR coding OR programming OR IDE OR software)',
        'limit': 8
    },
    'testing': {
        'query': '("test automation" OR "AI testing" OR "Playwright" OR "Cypress" OR "self-healing tests" OR "visual regression testing" OR "end-to-end testing") AND (software OR developer OR engineering OR QA)',
        'limit': 6
    },
    'microservices': {
        'query': '("microservices" OR "service mesh" OR "Istio" OR "Linkerd" OR "OpenTelemetry" OR "API gateway" OR "Kubernetes" OR "distributed systems") AND (architecture OR engineering OR developer OR cloud)',
        'limit': 6
    },
    'fintech': {
        'query': '("Stripe API" OR "payment infrastructure" OR "FedNow" OR "real-time payments" OR "PCI DSS" OR "tokenization" OR "3D Secure" OR "payment processing") AND (engineering OR developer OR API OR security OR technical)',
        'limit': 6
    },
    'devprod': {
        'query': '("developer productivity" OR "platform engineering" OR "Backstage" OR "DORA metrics" OR "internal developer platform" OR "CI/CD pipeline" OR "GitHub Actions") AND (software OR engineering OR developer OR DevOps)',
        'limit': 6
    },
    'security': {
        'query': '("supply chain attack" OR "npm vulnerability" OR "PyPI package" OR "CVE" OR "secrets management" OR "prompt injection" OR "AI security" OR "zero-day") AND (developer OR software OR security OR vulnerability)',
        'limit': 8
    }
}

# Filter out articles whose title doesn't actually contain technical/engineering terms
RELEVANCE_KEYWORDS = {
    'ai-coding': ['copilot', 'claude', 'cursor', 'windsurf', 'codeium', 'ai', 'code', 'coding', 'developer', 'programming', 'ide', 'llm', 'chatgpt', 'github'],
    'testing': ['test', 'qa', 'playwright', 'cypress', 'selenium', 'automation', 'regression', 'quality'],
    'microservices': ['microservice', 'service', 'mesh', 'istio', 'linkerd', 'kubernetes', 'k8s', 'api', 'gateway', 'opentelemetry', 'observability', 'distributed', 'cloud', 'docker', 'container'],
    'fintech': ['payment', 'stripe', 'mastercard', 'visa', 'adyen', 'paypal', 'fednow', 'pci', 'tokenization', '3ds', 'fintech', 'finance', 'banking'],
    'devprod': ['developer', 'productivity', 'platform', 'backstage', 'dora', 'ci/cd', 'devops', 'pipeline', 'engineering', 'github actions'],
    'security': ['security', 'vulnerability', 'cve', 'attack', 'breach', 'exploit', 'malware', 'npm', 'pypi', 'supply chain', 'prompt injection', 'zero-day', 'hack']
}

def is_relevant(article, category):
    """Check if article title actually contains category-relevant keywords"""
    keywords = RELEVANCE_KEYWORDS.get(category, [])
    if not keywords:
        return True
    text = (article.get('title', '') + ' ' + (article.get('description') or '')).lower()
    return any(kw in text for kw in keywords)

def fetch_category_news(category_key, query, limit):
    """Fetch news for a single category"""
    if not NEWS_API_KEY:
        print(f"⚠️  NEWS_API_KEY not set, skipping {category_key}")
        return []

    try:
        # Get articles from last 7 days for fresher content
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        url = "https://newsapi.org/v2/everything"
        # Fetch more than limit to leave room for relevance filtering
        params = {
            'q': query,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': min(limit * 3, 30),
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

            # Filter out articles that don't match category-specific keywords
            if not is_relevant(article, category_key):
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

        # Trim to requested limit after relevance filtering
        items = items[:limit]
        print(f"✅ {category_key}: fetched {len(items)} relevant articles")
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

    # Deduplicate by URL AND normalized title (handles regional duplicates
    # like me.pcmag.com vs uk.pcmag.com sharing the same article)
    import re
    seen_urls = set()
    seen_titles = set()
    unique = []
    for article in all_articles:
        url = article['url']
        # Normalize title: lowercase, collapse whitespace, strip punctuation
        norm_title = re.sub(r'[^\w\s]', '', (article['title'] or '').lower()).strip()
        norm_title = re.sub(r'\s+', ' ', norm_title)

        if url in seen_urls or norm_title in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(norm_title)
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
