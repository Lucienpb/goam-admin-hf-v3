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
# Load JSON file from GitHub (ORIGINAL FUNCTION)
# UPDATED: now returns (data, sha)
# ------------------------------------------------------------
def github_load_json(path):
    """
    Loads a JSON file from the GitHub repo.
    Returns (data, sha) or (None, None) if file does not exist.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"

    print("DEBUG REPO:", repr(GITHUB_REPO))
    print("DEBUG PATH:", repr(path))
    print("DEBUG URL:", url)

    try:
        data = _github_request("GET", url)
    except RuntimeError:
        return None, None  # File does not exist

    if "content" not in data:
        return None, None

    decoded = base64.b64decode(data["content"]).decode("utf-8")

    try:
        json_data = json.loads(decoded)
    except Exception:
        return None, None

    return json_data, data.get("sha")


# ------------------------------------------------------------
# Save JSON file to GitHub (ORIGINAL FUNCTION)
# UPDATED: now accepts optional sha + message
# ------------------------------------------------------------
def github_save_json(path, obj, sha=None, message=None):
    """
    Saves a JSON file to GitHub.
    Automatically handles SHA for updates.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"

    print("DEBUG URL:", url)
    print("DEBUG REPO:", GITHUB_REPO)

    content_str = json.dumps(obj, indent=2)
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    if message is None:
        message = f"Update {path}"

    payload = {
        "message": message,
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    _github_request("PUT", url, json=payload)

    return True


# ============================================================
# NEW SECTION — REQUIRED FOR YOUR APP ARCHITECTURE
# ============================================================

# ------------------------------------------------------------
# NEW: Load ALL app data after login
# ------------------------------------------------------------
def load_all_app_data():
    """
    Loads all required JSON files after login.
    Returns a dict: { filename: {data, sha} }
    """
    files = [
        "data/course_data.json",
        "data/goam_scores.json",
        "data/pairings.json",
        "data/players.json",
        "data/users.json",
    ]

    loaded = {}

    for f in files:
        data, sha = github_load_json(f)
        loaded[f] = {"data": data, "sha": sha}

    return loaded


# ------------------------------------------------------------
# NEW: Save JSON from Data Manager (Excel upload)
# ------------------------------------------------------------
def save_json_with_sha(path, new_data):
    """
    Used by Data Manager after Excel upload.
    Loads SHA, overwrites file, pushes to GitHub.
    """
    _, sha = github_load_json(path)

    github_save_json(
        path,
        new_data,
        sha=sha,
        message=f"Data Manager update for {path}"
    )

    return True


# ------------------------------------------------------------
# NEW: Save a single user's updated record
# ------------------------------------------------------------
def save_user_record(username, updated_record):
    """
    Updates only one user's record inside users.json.
    """
    path = "data/users.json"

    users, sha = github_load_json(path)

    if users is None:
        raise RuntimeError("users.json could not be loaded from GitHub")

    users[username] = updated_record

    github_save_json(
        path,
        users,
        sha=sha,
        message=f"Update user {username} via profile page"
    )

    return True
