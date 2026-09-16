from background import *
import math, re, html


STOPWORDS = set([
  'the','and','is','in','it','of','to','a','an','for','on','with','by','from','that','this',
  'be','are','as','at','or','we','you','your','our'
])


def _tokenize(text):
  if not text:
    return []
  tokens = re.findall(r"[a-z0-9]+", text.lower())
  return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def _build_index(docs):
  # docs: mapping url -> text
  tf = {}            # url -> {term: count}
  df = {}            # term -> doc frequency
  N = 0
  for url, text in docs.items():
    N += 1
    terms = _tokenize(str(text) + ' ' + url)
    counts = {}
    for t in terms:
      counts[t] = counts.get(t, 0) + 1
    tf[url] = counts
    for t in counts.keys():
      df[t] = df.get(t, 0) + 1

  idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}
  return tf, idf


def _score_documents(query, docs):
  q_terms = _tokenize(query)
  if not q_terms:
    return []

  tf, idf = _build_index(docs)

  scores = {}
  for url, counts in tf.items():
    score = 0.0
    for term in q_terms:
      if term in counts:
        # tf weight (log normalization) * idf
        tf_w = 1 + math.log(counts[term])
        score += tf_w * idf.get(term, 0.0)

    # small boost if the full query appears in title or url
    fulltext = (str(docs.get(url, '')) + ' ' + str(url)).lower()
    if query.lower().strip() in fulltext:
      score *= 1.6

    # prefer shorter titles slightly (more focused)
    title_len = len(str(docs.get(url, ''))) + 1
    score = score / math.log(title_len + 2)

    if score > 0:
      scores[url] = score

  # fallback: if no positive scores, perform fuzzy substring match
  if not scores:
    for url, text in docs.items():
      if all(term in (text + ' ' + url).lower() for term in q_terms):
        scores[url] = 0.5

  ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
  return ranked


def results(query):
  query = (query or '').strip()
  # prefer full-page text index `docs` populated by the crawler; fall back to `data` titles
  docs_to_search = docs if 'docs' in globals() and docs else data
  ranked = _score_documents(query, docs_to_search)
  return results_page(ranked, query)


def _short_domain(url):
  m = re.search(r"https?://([^/]+)", url)
  return m.group(1) if m else url


def results_page(ranked_sites, query):
  # ranked_sites: list of (url, score)
  safe_query = html.escape(query or '')
  if not ranked_sites:
    body = f"<p class=\"muted\">No results found for <strong>{safe_query}</strong>.</p>"
  else:
    items = []
    for url, score in ranked_sites[:50]:
      title = html.escape(data.get(url, url))
      short = html.escape(_short_domain(url))
      items.append(f"""
      <article class="result">
        <a class="result-title" href="{html.escape(url)}">{title}</a>
        <div class="result-url">{short}</div>
      </article>
      """)

    body = "\n".join(items)

  html_page = f"""
  <!doctype html>
  <html>
  <head>
    <meta charset=\"utf-8\"> 
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Search results for {safe_query}</title>
    <style>
    :root {{ --bg: #f7f9fc; --panel: #ffffff; --text: #1f2937; --muted: #6b7280; --accent: #2563eb; --accent-dark: #1d4ed8; --border: #e5e7eb; }}
    body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(180deg, var(--bg) 0%, #f1f5f9 100%); color:var(--text); padding:24px; }}
    .shell {{ max-width:960px; margin:0 auto; background:var(--panel); border:1px solid var(--border); border-radius:20px; padding:28px; box-shadow: 0 18px 50px rgba(15,23,42,0.06); }}
    .brand {{ display:flex; align-items:center; gap:10px; color:var(--accent); font-weight:700; text-transform:uppercase; font-size:0.9rem; }}
    .brand-dot {{ width:12px; height:12px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 4px rgba(37,99,235,0.12); }}
    form {{ display:flex; gap:10px; margin-top:18px; padding:10px; border-radius:999px; border:1px solid var(--border); background:#fbfdff; }}
    .search-input {{ flex:1; border:none; outline:none; font-size:1rem; padding:8px 6px; background:transparent; }}
    .search-btn {{ border:none; background:var(--accent); color:#fff; padding:10px 16px; border-radius:999px; cursor:pointer; font-weight:600; }}
    .results-count {{ margin-top:18px; color:var(--muted); }}
    .result {{ padding:18px; border-radius:12px; border:1px solid var(--border); margin-top:12px; background:#fff; }}
    .result-title {{ font-size:1.05rem; color:var(--accent-dark); font-weight:600; text-decoration:none; }}
    .result-url {{ color:var(--muted); margin-top:6px; font-size:0.9rem; }}
    .muted {{ color:var(--muted); }}
    </style>
  </head>
  <body>
    <main class=\"shell\">
    <div class=\"brand\"><span class=\"brand-dot\"></span><span>Search Engine</span></div>
    <form id=\"searchForm\" action=\"/search\" method=\"get\">
      <input name=\"query\" value=\"{safe_query}\" class=\"search-input\" placeholder=\"Search the web\"> 
      <button class=\"search-btn\" type=\"submit\">Search</button>
    </form>
    <div class=\"results-count\">{len(ranked_sites)} results</div>
    <section class=\"results\">{body}</section>
    </main>
  </body>
  </html>
  """

  return html_page