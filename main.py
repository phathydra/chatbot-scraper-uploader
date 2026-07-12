from pathlib import Path
import json
import os

from scraper import (
    fetch_articles,
    convert_to_markdown,
    get_filename,
    save_markdown
)

from uploader import (
    upload,
    remove
)

DATA_DIR = Path(os.getenv("DATA_DIR", "."))

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# Directory to store sync articles
STATE_FILE = DATA_DIR / "sync_state.json"

def load_state():
    """
    Load previous sync state

    Return empty state if first run
    """
    if not STATE_FILE.exists():
        return {"articles": {}}
    
    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)

def save_state(state):
    """
    Save state
    """
    temporary_file = STATE_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            indent=2,
            sort_keys=True
        )
    
    temporary_file.replace(STATE_FILE)

def classify_article(previous, current):
    """
    Decide an action to an article
    """
    if previous is None:
        return "added"
    
    if previous["updated_at"] != current["updated_at"]:
        return "updated"
    
    return "skipped"

def create_article_state(article, vector_store_file_id):
    """
    Create saved information for an article
    """
    return{
        "title": article["title"],
        "updated_at": article.get("updated_at", ""),
        "html_url": article["html_url"],
        "filename": get_filename(article),
        "vector_store_file_id": vector_store_file_id,
    }

def process_added_article(article, markdown, state):
    """
    Save and upload new article
    """
    article_id = str(article["id"])

    file_path = save_markdown(article, markdown)

    upload_result = upload(file_path)

    state["articles"][article_id] = (
        create_article_state(article, upload_result.id)
    )

    save_state(state)

    print(
        f"ADDED | "
        f"id= {article_id} | "
        f"title= {article['title']} | "
        f"OpenAI file= {upload_result.id}\n"
    )

def process_updated_article(article, markdown, previous, state):
    """
    Upload an article to newest version and remove old version on the vector store
    """
    article_id = str(article["id"])

    old_file_id = previous.get("vector_store_file_id")

    file_path = save_markdown(article, markdown)

    upload_result = upload(file_path)

    state["articles"][article_id] = (
        create_article_state(article, upload_result.id)
    )

    save_state(state)

    if old_file_id:
        remove(old_file_id)

    print(
        f"UPDATED | "
        f"id= {article_id} | "
        f"title= {article['title']} | "
        f"OpenAI file= {upload_result.id}\n"
    )

def synchronize():
    """
    Run the sync process
    """
    state = load_state()

    articles = fetch_articles()

    counts = {
        "added": 0,
        "updated": 0,
        "skipped": 0
    }

    print()
    print(
        f"Starting synchronization for "
        f"{len(articles)} articles."
    )
    print()

    for article in articles:
        article_id = str(article["id"])

        previous = state["articles"].get(article_id)

        action = classify_article(previous, article)

        counts[action] += 1

        if action == "skipped":
            continue

        markdown = convert_to_markdown(article)

        if action == "added":
            process_added_article(article, markdown, state)

        if action == "updated":
            process_updated_article(article, markdown, previous, state)

    print(
        "SYNC_RESULT "
        f"added={counts['added']} "
        f"updated={counts['updated']} "
        f"skipped={counts['skipped']}"
    )

    return counts

if __name__ == "__main__":
    try:
        synchronize()
    except Exception as error:
        print(
            f"SYNC_FAILED "
            f"error={type(error).__name__}: {error}"
        )
        raise