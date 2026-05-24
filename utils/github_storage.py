import os
import json
import base64
import requests

# ------------------------------------------------------------
# GitHub Repo Configuration
# ------------------------------------------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "Lucienpb/goam-admin-hf-v2"
GITHUB_BRANCH = "main"

if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN is missing in Hugging Face Secrets")

if not GITHUB_REPO:
    raise RuntimeError("GITHUB_REPO is missing in Hugging Face Secrets")

# ------------------------------------------------------------
# Internal helper: GitHub API request
# ------------------------------------------------------------
def _github_request(method, url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    headers["Accept"] = "application/vnd.github+json"

    response = requests.request(method, url, headers=headers, **kwargs)

    if response.status_code >= 400:
        raise RuntimeError(
            f"GitHub API error {response.status_code}: {response.text}"
        )

    return response.json()


# ------------------------------------------------------------
# Load JSON file from GitHub
# ------------------------------------------------------------
def github_load_json(path):
    """
    Loads a JSON file from the GitHub repo.
    Returns Python dict/list or None if file does not exist.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"
    print("DEBUG URL:", url)
    print("DEBUG REPO:", GITHUB_REPO)

    try:
        data = _github_request("GET", url)
    except RuntimeError:
        return None  # File does not exist

    if "content" not in data:
        return None

    decoded = base64.b64decode(data["content"]).decode("utf-8")

    try:
        return json.loads(decoded)
    except Exception:
        return None


# ------------------------------------------------------------
# Save JSON file to GitHub (create or update)
# ------------------------------------------------------------
def github_save_json(path, obj):
    """
    Saves a JSON file to GitHub.
    Automatically handles SHA for updates.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    print("DEBUG URL:", url)
    print("DEBUG REPO:", GITHUB_REPO)
    # Convert object to JSON string
    content_str = json.dumps(obj, indent=2)
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    # Check if file exists to get SHA
    sha = None
    try:
        existing = _github_request("GET", url)
        sha = existing.get("sha")
    except RuntimeError:
        pass  # File does not exist yet

    payload = {
        "message": f"Update {path}",
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    _github_request("PUT", url, json=payload)

    return True

