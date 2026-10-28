"""One-time migration of existing brief pages to the redesigned layout.

For every brief in articles_data.json whose page still uses the old layout, this
re-renders the page with brief_renderer.py and records the brief's headline in
articles_data.json (the homepage and Thoughts page show it). Pages already in the
new layout are left alone, so running it again is safe.

Usage: python rebuild_briefs.py
"""
import json
import os

from brief_renderer import extract_legacy_body, headline_of, render_brief_page

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "articles_data.json")


def main():
    with open(DATA, encoding="utf-8") as f:
        archive = json.load(f)

    # Headlines first, so related-brief cards on every page can show them
    bodies = {}
    for brief in archive:
        path = os.path.join(BASE, brief["url"])
        if not os.path.exists(path):
            print(f"Missing page, skipped: {brief['url']}")
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            body = extract_legacy_body(f.read())
        if body:
            bodies[brief["url"]] = body
            brief["headline"] = headline_of(body, brief.get("title", ""))

    for brief in archive:
        body = bodies.get(brief["url"])
        if not body:
            continue
        with open(os.path.join(BASE, brief["url"]), "w", encoding="utf-8") as f:
            f.write(render_brief_page(brief, body, archive))

    with open(DATA, "w") as f:
        json.dump(archive, f, indent=2)
    print(f"Re-rendered {len(bodies)} of {len(archive)} brief pages")


if __name__ == "__main__":
    main()
