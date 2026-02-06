"""
Flask Job Board - Display scraped jobs from multiple sources
"""
from flask import Flask, render_template, request, jsonify
import json
import re
import math
import os
from html import unescape
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime

app = Flask(__name__)

# Path to scraped jobs JSON (inside jobs_flask folder)
JOBS_FILE = Path(__file__).parent / 'scraped_jobs.json'

JOBS_PER_PAGE = 20

# Work arrangement keywords
ARRANGEMENT_KEYWORDS = {
    'remote': ['remote', 'work from home', 'wfh', 'anywhere'],
    'hybrid': ['hybrid'],
    'onsite': ['onsite', 'on-site', 'on site', 'in-office', 'in office'],
}

# Job type keywords
TYPE_KEYWORDS = {
    'full-time': ['full-time', 'full time', 'fulltime'],
    'part-time': ['part-time', 'part time', 'parttime'],
    'contract': ['contract'],
    'freelance': ['freelance', 'gig'],
}


_SALARY_NUM_RE = re.compile(r'[\$]?\s*([\d,]+(?:\.\d+)?)')

# Salary range brackets (monthly USD estimates)
SALARY_RANGES = {
    'under500': (0, 500),
    '500to1000': (500, 1000),
    '1000to2000': (1000, 2000),
    '2000to5000': (2000, 5000),
    '5000plus': (5000, float('inf')),
}


def parse_salary_monthly(job):
    """Extract a monthly USD estimate from salary string. Returns None if unparseable."""
    raw = (job.get('salary') or '').strip()
    if not raw:
        return None
    low = raw.lower()

    # Skip non-numeric salaries
    if low in ('tbd', 'n/a', 'doe', 'any', 'negotiable', 'project-based') or 'based on' in low or 'competitive' in low:
        return None

    # Find all numbers
    nums = []
    for n in _SALARY_NUM_RE.findall(raw):
        n = n.replace(',', '').strip()
        if n:
            try:
                nums.append(float(n))
            except ValueError:
                continue
    if not nums:
        return None

    # Use the average if there's a range
    avg = sum(nums) / len(nums)

    # Detect period and normalize to monthly
    if any(kw in low for kw in ('/hr', '/hour', 'per hour', 'hourly', 'hour')):
        return avg * 160  # ~40hrs/week * 4 weeks
    elif any(kw in low for kw in ('/yr', '/year', 'annual', 'yearly')):
        return avg / 12
    elif any(kw in low for kw in ('/w', '/week', 'weekly', 'per week')):
        return avg * 4
    elif any(kw in low for kw in ('/mo', '/month', 'monthly', 'per month')):
        return avg

    # Guess based on magnitude
    if avg > 10000:
        return avg / 12  # Likely annual
    elif avg < 50:
        return avg * 160  # Likely hourly
    else:
        return avg  # Assume monthly


def detect_arrangement(job):
    """Detect work arrangement from job fields."""
    text = ' '.join([
        job.get('location') or '',
        job.get('title') or '',
        job.get('category') or '',
        job.get('type') or '',
    ]).lower()
    for arrangement, keywords in ARRANGEMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return arrangement
    return ''


def detect_job_type(job):
    """Detect job type from job fields."""
    text = ' '.join([
        job.get('category') or '',
        job.get('type') or '',
        job.get('title') or '',
    ]).lower()
    for jtype, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return jtype
    return ''


def parse_date(job):
    """Parse posted_date into a naive datetime for sorting. Returns None if unparseable."""
    raw = (job.get('posted_date') or job.get('date_posted') or '').strip()
    if not raw:
        return None
    # ISO 8601: "2026-02-03T14:00:06+00:00"
    try:
        dt = datetime.fromisoformat(raw)
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        pass
    # RFC 2822: "Wed, 12 Nov 2025 08:56:02 +0000" (WeWorkRemotely)
    try:
        dt = parsedate_to_datetime(raw)
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError, IndexError):
        pass
    # Short date: "Feb 4, 2026" (OnlineJobs.ph)
    try:
        return datetime.strptime(raw, '%b %d, %Y')
    except (ValueError, TypeError):
        pass
    # Plain date: "2026-02-03"
    try:
        return datetime.strptime(raw, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def format_date(dt):
    """Format a datetime into a human-readable string like 'Feb 3, 2026'."""
    if dt is None:
        return ''
    return dt.strftime('%b %d, %Y').replace(' 0', ' ')


def load_jobs():
    """Load jobs from JSON file"""
    try:
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
            for idx, job in enumerate(jobs):
                normalize_job_text(job)
                job['id'] = idx
                job['_arrangement'] = detect_arrangement(job)
                job['_job_type'] = detect_job_type(job)
                job['_parsed_date'] = parse_date(job)
                job['_display_date'] = format_date(job['_parsed_date'])
                job['_salary_monthly'] = parse_salary_monthly(job)
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
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join([line for line in lines if line])


def normalize_job_text(job):
    """Normalize job text fields to avoid None and HTML artifacts."""
    for key in ("title", "description", "job_description", "company", "location", "salary", "type", "category"):
        if key in job:
            job[key] = clean_text(job.get(key))


def apply_filters(jobs, source_filter='', category_filter='', search_query='',
                  arrangement_filter='', job_type_filter='', sort_by='',
                  salary_filter=''):
    """Apply all filters and sorting to a job list."""
    filtered = jobs

    if source_filter:
        filtered = [j for j in filtered if j.get('source', '') == source_filter]

    if category_filter:
        filtered = [j for j in filtered
                    if j.get('category', '') == category_filter or j.get('type', '') == category_filter]

    if arrangement_filter:
        filtered = [j for j in filtered if j.get('_arrangement') == arrangement_filter]

    if job_type_filter:
        filtered = [j for j in filtered if j.get('_job_type') == job_type_filter]

    if salary_filter and salary_filter in SALARY_RANGES:
        lo, hi = SALARY_RANGES[salary_filter]
        filtered = [j for j in filtered
                    if j.get('_salary_monthly') is not None and lo <= j['_salary_monthly'] < hi]

    if search_query:
        q = search_query.lower()
        filtered = [j for j in filtered
                    if q in (j.get('title') or '').lower()
                    or q in (j.get('description') or '').lower()
                    or q in (j.get('job_description') or '').lower()]

    # Sorting (default to newest first)
    if sort_by == 'oldest':
        filtered.sort(key=lambda j: j.get('_parsed_date') or datetime.min)
    else:
        filtered.sort(key=lambda j: j.get('_parsed_date') or datetime.min, reverse=True)

    return filtered


@app.route('/')
def index():
    """Main page - display all jobs with filters and pagination"""
    jobs = load_jobs()

    source_filter = request.args.get('source', '')
    category_filter = request.args.get('category', '')
    search_query = request.args.get('search', '')
    arrangement_filter = request.args.get('arrangement', '')
    job_type_filter = request.args.get('job_type', '')
    salary_filter = request.args.get('salary', '')
    sort_by = request.args.get('sort', '')

    filtered_jobs = apply_filters(jobs, source_filter, category_filter, search_query,
                                  arrangement_filter, job_type_filter, sort_by, salary_filter)

    # Pagination
    total_filtered = len(filtered_jobs)
    total_pages = max(1, math.ceil(total_filtered / JOBS_PER_PAGE))
    current_page = request.args.get('page', 1, type=int)
    current_page = max(1, min(current_page, total_pages))
    start = (current_page - 1) * JOBS_PER_PAGE
    paginated_jobs = filtered_jobs[start:start + JOBS_PER_PAGE]

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
                         current_arrangement=arrangement_filter,
                         current_job_type=job_type_filter,
                         current_salary=salary_filter,
                         current_sort=sort_by,
                         current_page=current_page,
                         total_pages=total_pages)


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Job detail page"""
    jobs = load_jobs()
    if 0 <= job_id < len(jobs):
        return render_template('job_detail.html', job=jobs[job_id])
    return "Job not found", 404


def job_to_dict(job):
    """Prepare a job dict for JSON serialization (remove non-serializable fields)."""
    return {k: v for k, v in job.items() if k != '_parsed_date'}


@app.route('/api/job/<int:job_id>')
def api_job_detail(job_id):
    """API endpoint to get a single job as JSON"""
    jobs = load_jobs()
    if 0 <= job_id < len(jobs):
        return jsonify(job_to_dict(jobs[job_id]))
    return jsonify({'error': 'Job not found'}), 404


@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get jobs as JSON"""
    jobs = load_jobs()

    filtered = apply_filters(
        jobs,
        source_filter=request.args.get('source', ''),
        category_filter=request.args.get('category', ''),
        search_query=request.args.get('search', ''),
        arrangement_filter=request.args.get('arrangement', ''),
        job_type_filter=request.args.get('job_type', ''),
        sort_by=request.args.get('sort', ''),
        salary_filter=request.args.get('salary', ''),
    )

    return jsonify({
        'total': len(jobs),
        'filtered': len(filtered),
        'jobs': [job_to_dict(j) for j in filtered]
    })


@app.route('/refresh')
def refresh():
    """Information page about refreshing jobs"""
    last_updated = None
    if JOBS_FILE.exists():
        mod_time = os.path.getmtime(JOBS_FILE)
        last_updated = datetime.fromtimestamp(mod_time).strftime('%B %d, %Y at %I:%M %p')
    jobs = load_jobs()
    return render_template('refresh.html', last_updated=last_updated, total_jobs=len(jobs))


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
