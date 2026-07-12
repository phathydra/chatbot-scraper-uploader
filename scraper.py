from pathlib import Path
import os

import requests
from markdownify import markdownify as md

import time

# Pagination size
PAGE_SIZE = 30

# Zendesk API endpoints
ARTICLES_URL = "https://support.optisigns.com/api/v2/help_center/articles"

DATA_DIR = Path(os.getenv("DATA_DIR", "."))

# Directory to store generated Markdown files
OUTPUT_DIR = DATA_DIR / "knowledge_base"

def fetch_articles():
    """
    Fetch articles
    """
    articles = []

    url = ARTICLES_URL
    params = {"page[size]": PAGE_SIZE}

    while url:
        start = time.perf_counter()

        response = requests.get(
            url,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        new_articles = data.get("articles", [])
        articles.extend(new_articles)

        duration = time.perf_counter() - start

        print(f"Fetched page in {duration:.2f} seconds | "
          f"Added: {len(new_articles)} articles | "
          f"Total so far: {len(articles)}\n")

        if data.get("meta", {}).get("has_more"):
            url = data["links"]["next"]
            params = None
        else:
            url = None

    return articles


def convert_to_markdown(article):
    """
    Convert an article's HTML content to Markdown.
    """
    html = f"""
    <h1>{article["title"]}</h1>
    <p>Source: {article["html_url"]}</p>
    <p>Article ID: {article["id"]}</p>
    <p>Updated at: {article["updated_at"]}</p>
    {article.get("body") or ""}
    """
    return md(html, heading_style="ATX").strip() + "\n"


def get_filename(article):
    """
    Generate the output filename based on article id
    """
    slug = str(article["id"])
    return f"{slug}.md"

def save_markdown(article, markdown):
    """
    Save markdown and return its Path
    """
    start = time.perf_counter()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename = get_filename(article)
    file_path = OUTPUT_DIR / filename

    file_path.write_text(
        markdown,
        encoding="utf-8",
    )

    duration = time.perf_counter() - start

    print(f"Saved: {file_path.name} | "
          f"Time: {duration:.3f}s")

    return file_path
