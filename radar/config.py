"""Static configuration for collectors. Edit here, not in collector code."""

import os

# Where the digest links to. Set these for your own setup, or override with env vars.
# TRACKER_URL is the page you flip a row to "approved" on; REPO_URL is where RADAR.md lives.
# Empty means "no tracker": RADAR.md then says approval is manual instead of linking anywhere.
TRACKER_URL = os.environ.get("JOB_RADAR_TRACKER_URL", "")
REPO_URL = os.environ.get("JOB_RADAR_REPO_URL", "https://github.com/OWNER/REPO")

# Greenhouse boards to poll: board token -> display company name.
GREENHOUSE_BOARDS = {
    "daangn": "당근",
    "anthropic": "Anthropic",
    "scaleai": "Scale AI",
    "databricks": "Databricks",
}
# Non-Korean greenhouse boards: keep only early-career titles (or Korea locations).
GREENHOUSE_EARLY_RE = r"new\s*grad|university|early[- ]career|junior|intern|residen|entry|graduate|fellow|associate|\b(20\d\d)\b"
GREENHOUSE_KR_BOARDS = {"daangn"}

# Global tech job boards: (display name, ats, board token). Verified live 2026-09-07.
ATS_BOARDS = [
    ("Moloco", "greenhouse", "moloco"),
    ("Coupang", "greenhouse", "coupang"),
    ("Anthropic", "greenhouse", "anthropic"),
    ("Databricks", "greenhouse", "databricks"),
    ("Scale AI", "greenhouse", "scaleai"),
    ("Stripe", "greenhouse", "stripe"),
    ("Figma", "greenhouse", "figma"),
    ("Vercel", "greenhouse", "vercel"),
    ("Waymo", "greenhouse", "waymo"),
    ("Verkada", "greenhouse", "verkada"),
    ("Sigma Computing", "greenhouse", "sigmacomputing"),
    ("Nuro", "greenhouse", "nuro"),
    ("Faire", "greenhouse", "faire"),
    ("OpenAI", "ashby", "openai"),
    ("Cohere", "ashby", "cohere"),
    ("Perplexity", "ashby", "perplexity"),
    ("Sierra", "ashby", "sierra"),
    ("Ramp", "ashby", "ramp"),
    ("Decagon", "ashby", "decagon"),
    ("Suno", "ashby", "suno"),
    ("Sendbird", "greenhouse", "sendbird"),
    ("Palantir", "lever", "palantir"),
]

# Per-source cap on new candidates per run (sources return newest first). Overflow keys are recorded as seen (grade "-").
# 40 was too tight for a 공채 season: linkareer alone returns ~108 rows in September.
# collect.priority() decides what survives the cap, so raising it costs noise, not signal.
MAX_PER_SOURCE = 70

# LinkedIn guest search queries: (keywords, location, experience filter). f_E=2 entry level, 3 associate.
LINKEDIN_QUERIES = [
    ("AI engineer", "South Korea", "2"),
    ("machine learning engineer", "South Korea", "2"),
    ("data engineer", "South Korea", "2"),
    ("AI engineer", "South Korea", "3"),
    ("forward deployed engineer", "South Korea", ""),
    ("machine learning engineer new grad", "United States", "2"),
    ("research assistant machine learning", "Canada", ""),
]

# Wanted job_group_id 518 = 개발. years=0..2.
WANTED_PARAMS = {"job_group_id": 518, "job_sort": "job.latest_order", "years": [0, 1, 2], "limit": 50, "offset": 0, "country": "kr"}

# Jumpit career filter: 0 = 신입, 1..2 years.
JUMPIT_PARAMS = {"sort": "reg_dt", "highlight": "false", "page": 1, "career": [0, 1, 2]}

# Saramin category keyword ids: 84 백엔드/서버, 2232 AI·ML? — use a list of job-category list pages (exp_cd=1 신입).
SARAMIN_URLS = [
    "https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_kewd=84&exp_cd=1&search_done=y&panel_count=y",
    "https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_kewd=2232&exp_cd=1&search_done=y&panel_count=y",
    "https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_kewd=108&exp_cd=1&search_done=y&panel_count=y",
]

# Simplify categories to keep (README section anchors).
SIMPLIFY_SECTIONS = ["Software Engineering", "Data Science, AI & Machine Learning"]

# Gmail senders that carry job alerts (used by the routine prompt, not by code).
GMAIL_ALERT_SENDERS = [
    "saramin.co.kr", "jobkorea.co.kr", "linkareer.com", "catch.co.kr", "wanted.co.kr",
    "jumpit.co.kr", "jobalerts-noreply@linkedin.com", "incruit.com", "jobplanet.co.kr", "rememberapp.co.kr",
    "careers.kakao.com", "programmers.co.kr", "rocketpunch.com",
]
