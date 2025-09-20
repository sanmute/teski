import asyncio, re, time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import trafilatura
from datetime import datetime
import sqlite3
import httpx

WHITELIST = {
  "khanacademy.org": {"depth": 1, "allow": [r"/math/"]},
  "ocw.mit.edu": {"depth": 1, "allow": [r"/courses/.*(lecture|resources|problem|exam)"]},
  "en.wikipedia.org": {"depth": 1, "allow": [r"/wiki/"]},
  "3blue1brown.com": {"depth": 1, "allow": [r"/lessons/"]},
}
UA = "DeadlineAgent/0.1 (+https://example.com)"

def allow_url(u:str, rules)->bool:
    path = urlparse(u).path or "/"
    for pat in rules.get("allow", []):
        if re.search(pat, path):
            return True
    return False

async def fetch(client, url):
    try:
        r = await client.get(url, headers={"User-Agent": UA}, timeout=10)
        if r.status_code != 200 or "text/html" not in r.headers.get("content-type",""):
            return None, r
        return r.text, r
    except Exception:
        return None, None

def extract_links(html, base):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"])
        if href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        links.add(href.split("#")[0])
    return list(links)

def extract_main_text(html, url):
    out = trafilatura.extract(html, include_comments=False, include_tables=False, url=url)
    if not out:
        return None, None
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else url
    return title, out

def reading_minutes(text:str)->int:
    words = len(text.split())
    return max(1, int(words/200))

def init_db(db_path="app.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        url TEXT PRIMARY KEY,
        domain TEXT,
        topic TEXT,
        fetched_at TEXT,
        etag TEXT,
        last_modified TEXT,
        status INTEGER
    );
    """)
    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS docs
    USING fts5(url, title, text, domain, topic, created_at UNINDEXED, tokenize='porter');
    """)
    conn.commit()
    conn.close()

import aiosqlite

async def crawl_domain(start_urls: list[str], topic: str, db_path="app.db", max_pages=20):
    init_db(db_path)  # Ensure tables exist
    parsed = urlparse(start_urls[0])
    domain = parsed.netloc
    rules = WHITELIST.get(domain, {"depth": 1})
    seen, queue = set(), [(u, 0) for u in start_urls]
    stored = 0

    async with httpx.AsyncClient(follow_redirects=True) as client, aiosqlite.connect(db_path) as conn:
        cur = await conn.cursor()
        while queue and stored < max_pages:
            url, depth = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            if not allow_url(url, rules):
                continue
            html, resp = await fetch(client, url)
            if not html:
                continue
            title, text = extract_main_text(html, url)
            if not text:
                continue
            if len(text) < 600:
                continue

            try:
                await cur.execute("DELETE FROM docs WHERE url=?", (url,))
                await cur.execute("""
                INSERT INTO docs(rowid, url, title, text, domain, topic, created_at)
                VALUES ((SELECT rowid FROM docs WHERE url=?),?,?,?,?,?)
                """, (url, url, title, text, domain, topic, datetime.utcnow().isoformat()))
                await cur.execute("""
                INSERT INTO urls(url, domain, topic, fetched_at, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET fetched_at=excluded.fetched_at, status=excluded.status
                """, (url, domain, topic, datetime.utcnow().isoformat(), 200))
                await conn.commit()
                stored += 1
            except aiosqlite.Error as e:
                print(f"Database error: {e}")

            if depth < rules.get("depth", 1):
                for link in extract_links(html, url):
                    if urlparse(link).netloc == domain:
                        queue.append((link, depth + 1))
            await asyncio.sleep(0.2)  # Be polite
    return stored