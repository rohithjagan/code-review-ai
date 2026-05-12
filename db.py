import sqlite3
import json
from datetime import datetime

DATABASE = 'code_reviews.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_full_name TEXT,
            pr_number INTEGER,
            pr_title TEXT,
            author TEXT,
            action TEXT,
            timestamp TEXT,
            suggestions_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_review(repo_full_name, pr_number, pr_title, author, action, suggestions):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reviews (repo_full_name, pr_number, pr_title, author, action, timestamp, suggestions_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (repo_full_name, pr_number, pr_title, author, action, 
          datetime.utcnow().isoformat(), json.dumps(suggestions)))
    conn.commit()
    conn.close()

def get_all_reviews():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT repo_full_name, pr_number, pr_title, author, timestamp, suggestions_json FROM reviews ORDER BY timestamp ASC')
    rows = c.fetchall()
    conn.close()
    reviews = []
    for row in rows:
        reviews.append({
            'repo_full_name': row[0],
            'pr_number': row[1],
            'pr_title': row[2],
            'author': row[3],
            'timestamp': row[4],
            'suggestions': json.loads(row[5])
        })
    return reviews

def get_aggregated_stats():
    """Return stats for dashboard: category counts, severity counts, trend over time."""
    reviews = get_all_reviews()
    category_counts = {}
    severity_counts = {}
    trend_data = []  # list of { date: 'YYYY-MM-DD', count: N }

    for review in reviews:
        date_str = review['timestamp'][:10]  # just the date part
        suggestions = review['suggestions']
        if not suggestions:
            continue
        for s in suggestions:
            cat = s.get('category', 'unknown')
            sev = s.get('severity', 'low')
            category_counts[cat] = category_counts.get(cat, 0) + 1
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    # Build trend: count per day
    date_counts = {}
    for review in reviews:
        date_str = review['timestamp'][:10]
        suggestions = review['suggestions']
        date_counts[date_str] = date_counts.get(date_str, 0) + len(suggestions)
    for date, count in sorted(date_counts.items()):
        trend_data.append({'date': date, 'count': count})
    
    return {
        'category_counts': category_counts,
        'severity_counts': severity_counts,
        'trend': trend_data,
        'total_reviews': len(reviews),
        'total_suggestions': sum(len(r['suggestions']) for r in reviews)
    }