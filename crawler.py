from background import *
import sys, requests, traceback, re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import threading

r_count = 0
sys.setrecursionlimit(500)


def crawl(url, prev_url=None):
  global r_count
  r_count += 1
  try:
    # simple guard against too-deep recursion
    if r_count > 490:
      return

    try:
      resp = requests.get(url, timeout=10)
    except Exception:
      if prev_url:
        resp = requests.get(urljoin(prev_url, url), timeout=10)
      else:
        return

    if resp.status_code == 404:
      return

    page_soup = BeautifulSoup(resp.content, "html.parser")
    title = page_soup.title.string.strip() if page_soup.title and page_soup.title.string else url
    text = page_soup.get_text(separator=' ', strip=True)

    # store title for display and full text for indexing
    data[url] = title
    try:
      docs[url] = text
    except Exception:
      pass

    print(f"Indexed {url} as {title}")

    links = page_soup.find_all("a", href=True)

    for link in links:
      href = link.get("href")
      if not href:
        continue
      # skip non-http links and fragments
      if href.startswith("mailto:") or href.startswith("javascript:") or href.startswith("#"):
        continue
      abs_url = urljoin(url, href)
      if abs_url not in data:
        crawl(abs_url, url)

  except Exception:
    traceback.print_exc()
  finally:
    r_count -= 1


def start_crawler():
  with open("./storage/start_links.txt") as file:
    for link in file.read().splitlines():
      threading.Thread(target=crawl, args=(link,), daemon=True).start()