"""Posts a push's changes to PlainSight's Discord channel (#plainsight-updates): each commit that
touched the site, the scripts or the worker, by its title. Docs, tests and workflows aren't posted.
Run by .github/workflows/changelog.yml on a push to main, with the channel's webhook in the
DISCORD_CHANGELOG secret."""
import json
import os
import urllib.request

CODE = ("site/", "scripts/", "worker/")
SITE = "https://grahamirwin.github.io/PlainSight/"


def changes(event):
    """The push's commits that changed code, oldest first."""
    return [c for c in event.get("commits", []) if c.get("distinct", True)
            and any(f.startswith(CODE) for k in ("added", "modified", "removed") for f in c.get(k, []))]


def message(event):
    commits = changes(event)
    if not commits:
        return None
    text = "\n".join("• " + c["message"].split("\n", 1)[0].strip() for c in commits)
    if len(text) > 3800:  # Discord takes 4,096 characters
        text = text[:3800].rsplit("\n", 1)[0] + "\n…"
    return {"embeds": [{"title": "PlainSight update", "url": SITE, "color": 0xA8834A,
                        "description": f"{text}\n\n[The changes in the code]({event['compare']})",
                        "timestamp": commits[-1]["timestamp"]}],
            "allowed_mentions": {"parse": []}}


if __name__ == "__main__":
    hook = os.environ.get("DISCORD_CHANGELOG")
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        body = message(json.load(f))
    if not hook or not body:
        print("Nothing to post" if hook else "No DISCORD_CHANGELOG secret: nothing posted")
    else:
        req = urllib.request.Request(hook, json.dumps(body).encode(),
                                     {"Content-Type": "application/json", "User-Agent": "PlainSight changelog"})
        urllib.request.urlopen(req, timeout=30).close()
        print(f"Posted {len(body['embeds'][0]['description'].splitlines()) - 2} change(s)")
