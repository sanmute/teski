import sqlite3, re
TRUST = {"ocw.mit.edu":3, "khanacademy.org":3, "3blue1brown.com":2, "en.wikipedia.org":1}

def search_docs(q:str, topic:str|None=None, limit=5, db="app.db"):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    base = "SELECT url, title, text, domain FROM docs WHERE docs MATCH ?"
    query = q
    if topic:
        base += " AND topic = ?"
        cur.execute(base + " LIMIT ?", (query, topic, limit*3))
    else:
        cur.execute(base + " LIMIT ?", (query, limit*3))
    rows = cur.fetchall()
    scored=[]
    for url, title, text, domain in rows:
        trust = TRUST.get(domain, 0)
        title_hit = 2 if re.search(r"(practice|problems|notes|lecture|example)", title, re.I) else 0
        length_penalty = 0 if len(text)<4000 else -1
        s = trust + title_hit + length_penalty
        scored.append((s, {"url":url,"title":title,"domain":domain,"why":"matched "+q}))
    scored.sort(key=lambda x: -x[0])
    out=[x[1] for x in scored[:limit]]
    conn.close()
    return out