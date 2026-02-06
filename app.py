"""
Flask Job Board - Display scraped jobs from multiple sources
"""
from flask import Flask, render_template, request, jsonify
import json
import re
import math
from html import unescape
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Path to scraped jobs JSON (inside jobs_flask folder)
JOBS_FILE = Path(__file__).parent / 'scraped_jobs.json'

JOBS_PER_PAGE = 20


def load_jobs():
    """Load jobs from JSON file"""
    try:
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
            # Add index to each job for easier reference
            for idx, job in enumerate(jobs):
                normalize_job_text(job)
                job['id'] = idx
            return jobs
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def get_unique_sources(jobs):
    """Get unique job sources for filtering"""
    sources = set()
    for job in jobs:
        if job.get('source'):
            sources.add(job.get('source'))
    return sorted(list(sources))


def get_unique_categories(jobs):
    """Get unique categories for filtering"""
    categories = set()
    for job in jobs:
        if job.get('category'):
            categories.add(job.get('category'))
        if job.get('type'):
            categories.add(job.get('type'))
    return sorted(list(categories))


_TAG_RE = re.compile(r"<[^>]+>")
_BR_RE = re.compile(r"<\\s*br\\s*/?\\s*>", re.IGNORECASE)


def clean_text(value):
    """Strip HTML tags and normalize whitespace."""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    text = _BR_RE.sub("\n", value)
    text = unescape(text)
    text = _TAG_RE.sub(" ", text)
    # Normalize each line but keep line breaks
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join([line for line in lines if line])


def normalize_job_text(job):
    """Normalize job text fields to avoid None and HTML artifacts."""
    for key in ("title", "description", "job_description", "company", "location", "salary", "type", "category"):
        if key in job:
            job[key] = clean_text(job.get(key))


@app.route('/')
def index():
    """Main page - display all jobs with filters and pagination"""
    jobs = load_jobs()

    # Get filter parameters
    source_filter = request.args.get('source', '')
    category_filter = request.args.get('category', '')
    search_query = request.args.get('search', '')

    # Apply filters
    filtered_jobs = jobs

    if source_filter:
        filtered_jobs = [job for job in filtered_jobs if job.get('source', '') == source_filter]

    if category_filter:
        filtered_jobs = [job for job in filtered_jobs
                        if job.get('category', '') == category_filter or job.get('type', '') == category_filter]

    if search_query:
        search_lower = search_query.lower()
        filtered_jobs = [job for job in filtered_jobs
                        if search_lower in (job.get('title') or '').lower()
                        or search_lower in (job.get('description') or '').lower()
                        or search_lower in (job.get('job_description') or '').lower()]

    # Pagination
    total_filtered = len(filtered_jobs)
    total_pages = max(1, math.ceil(total_filtered / JOBS_PER_PAGE))
    current_page = request.args.get('page', 1, type=int)
    current_page = max(1, min(current_page, total_pages))
    start = (current_page - 1) * JOBS_PER_PAGE
    end = start + JOBS_PER_PAGE
    paginated_jobs = filtered_jobs[start:end]

    # Get filter options
    sources = get_unique_sources(jobs)
    categories = get_unique_categories(jobs)

    return render_template('index.html',
                         jobs=paginated_jobs,
                         total_jobs=len(jobs),
                         filtered_count=total_filtered,
                         sources=sources,
                         categories=categories,
                         current_source=source_filter,
                         current_category=category_filter,
                         search_query=search_query,
                         current_page=current_page,
                         total_pages=total_pages)


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Job detail page"""
    jobs = load_jobs()

    if 0 <= job_id < len(jobs):
        job = jobs[job_id]
        return render_template('job_detail.html', job=job)
    else:
        return "Job not found", 404


@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get jobs as JSON"""
    jobs = load_jobs()

    source_filter = request.args.get('source', '')
    category_filter = request.args.get('category', '')
    search_query = request.args.get('search', '')

    filtered_jobs = jobs

    if source_filter:
        filtered_jobs = [job for job in filtered_jobs if job.get('source', '') == source_filter]

    if category_filter:
        filtered_jobs = [job for job in filtered_jobs
                        if job.get('category', '') == category_filter or job.get('type', '') == category_filter]

    if search_query:
        search_query = search_query.lower()
        filtered_jobs = [job for job in filtered_jobs
                        if search_query in (job.get('title') or '').lower()
                        or search_query in (job.get('description') or '').lower()]

    return jsonify({
        'total': len(jobs),
        'filtered': len(filtered_jobs),
        'jobs': filtered_jobs
    })


@app.route('/refresh')
def refresh():
    """Information page about refreshing jobs"""
    return render_template('refresh.html')


@app.template_filter('truncate_words')
def truncate_words(text, length=50):
    """Truncate text to specified number of words"""
    if not text:
        return ""
    words = text.split()
    if len(words) <= length:
        return text
    return ' '.join(words[:length]) + '...'


if __name__ == '__main__':
    print("=" * 60)
    print("JOB BOARD FLASK APP")
    print("=" * 60)
    print(f"Jobs file: {JOBS_FILE}")
    print(f"Total jobs available: {len(load_jobs())}")
    print("\nStarting Flask server...")
    print("Visit: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
