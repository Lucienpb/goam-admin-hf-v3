"""
User Profile Page for GOAM Admin
Allows:
- Viewing account details
- Updating profile info
- Changing password
- Viewing personal GOAM stats
- Uploading a profile photo
"""

import streamlit as st
import os
from datetime import datetime
import pandas as pd

from auth.auth import load_users, save_users, verify_password, change_password
from backend.goam_loader import GOAMLoader
from backend.goam_calculator import GOAMCalculator
from utils.github_storage import save_user_record

PHOTO_DIR = "data/profile_photos"


# ---------------------------------------------------------
# LOAD USER STATS FROM GOAM SCORES
# ---------------------------------------------------------
def _load_user_stats(email):
    try:
        # Load GOAM scores
        goam_scores = GOAMLoader.load_json_scores("data/goam_scores.json")
        season_df = GOAMCalculator.build_from_json(goam_scores)

        # Load players.json
        players = GOAMLoader.load_json("data/players.json")
    except Exception:
        return None

    if season_df.empty or not players:
        return None

    # Find player by email (case-insensitive)
    player = next((p for p in players if p.get("email", "").lower() == email.lower()), None)
    if not player:
        return None

    player_name = player.get("name")
    if not player_name:
        return None

    # LOWERCASE comparison for matching names
    user_rounds = season_df[season_df["Name"].str.lower() == player_name.lower()]

    if user_rounds.empty:
        return None

    avg_ips = round(user_rounds["IPS"].mean(), 0)
    avg_strokes = round(user_rounds["Strokes"].mean(), 0)
    games_played = len(user_rounds)

    return {
        "avg_ips": avg_ips,
        "avg_strokes": avg_strokes,
        "games_played": games_played,
        "membership": player.get("membership"),
        "team": player.get("team"),
        "handicap_index": player.get("handicap_index")
    }

# ---------------------------------------------------------
# PROFILE PHOTO HELPERS
# ---------------------------------------------------------
def _get_photo_path(email):
    os.makedirs(PHOTO_DIR, exist_ok=True)
    return os.path.join(PHOTO_DIR, f"{email}.jpg")


def _load_profile_photo(email):
    path = _get_photo_path(email)
    return path if os.path.exists(path) else None


def _save_profile_photo(email, uploaded_file):
    path = _get_photo_path(email)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


# ---------------------------------------------------------
# MAIN PROFILE PAGE
# ---------------------------------------------------------
def show_profile_page(email: str):
    st.title("👤 My Profile")

    users = load_users()
    email_norm = email.strip().lower()

    if email_norm not in users:
        st.error("User not found")
        return

    user = users[email_norm]

    # ====================================================================
    # PERSONAL GOAM STATS
    # ====================================================================
    st.subheader("📊 My GOAM Stats")

    stats = _load_user_stats(email_norm)

    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Membership No.", stats["membership"])
        col2.metric("Avg IPS", stats["avg_ips"])
        col3.metric("Avg Strokes", stats["avg_strokes"])
        col4.metric("Games Played", stats["games_played"])
    else:
        st.info("No GOAM rounds found for your profile yet.")

    st.markdown("---")

    # ====================================================================
    # PROFILE PHOTO
    # ====================================================================
    st.subheader("📸 Profile Photo")

    existing_photo = _load_profile_photo(email_norm)

    if existing_photo:
        st.image(existing_photo, width=180)
    else:
        st.info("No profile photo uploaded yet.")

    uploaded = st.file_uploader("Upload a profile photo", type=["jpg", "jpeg", "png"])

    if uploaded:
        saved_path = _save_profile_photo(email_norm, uploaded)
        st.success("Photo updated successfully.")
        st.image(saved_path, width=180)

    st.markdown("---")

    # ====================================================================
    # ACCOUNT OVERVIEW
    # ====================================================================
    st.subheader("Account Information")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Email:** {email_norm}")
        st.write(f"**Role:** {user.get('role', 'member').capitalize()}")
        st.write(f"**Verified:** {'Yes' if user.get('verified') else 'No'}")

    with col2:
        st.write(f"**Account Created:** {user.get('created_at', 'N/A')}")
        st.write(f"**Last Updated:** {user.get('updated_at', 'N/A')}")

    st.markdown("---")

    # ====================================================================
    # UPDATE PROFILE DETAILS
    # ====================================================================
    st.subheader("Update Profile Details")

    name = st.text_input("Full Name", value=user.get("name", ""))
    phone = st.text_input("Phone Number", value=user.get("phone", ""))

    if st.button("Save Profile", use_container_width=True):
        user["name"] = name
        user["phone"] = phone
        user["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        users[email_norm] = user
        save_users(users)
    
        # ------------------------------------------------------------
        # NEW: Push updated user record to GitHub
        # ------------------------------------------------------------

        try:
            save_user_record(email_norm, user)
            st.session_state["users"][email_norm] = user
        except Exception as e:
            st.error(f"Failed to sync profile to GitHub: {e}")
            return

    st.success("Profile updated successfully!")
    st.rerun()


    st.markdown("---")

    # ====================================================================
    # CHANGE PASSWORD
    # ====================================================================
    st.subheader("Change Password")

    current_pw = st.text_input("Current Password", type="password")
    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm New Password", type="password")

    if st.button("Update Password", use_container_width=True):

        if not verify_password(current_pw, user["password_hash"]):
            st.error("Current password is incorrect")
            return

        if not new_pw:
            st.error("New password cannot be empty")
            return

        if new_pw != confirm_pw:
            st.error("New passwords do not match")
            return

        if len(new_pw) < 8:
            st.error("Password must be at least 8 characters")
            return

        success, msg = change_password(email_norm, current_pw, new_pw)

        if success:
            # ------------------------------------------------------------
            # NEW: Sync updated password to GitHub
            # ------------------------------------------------------------
            from utils.github_storage import save_user_record
            try:
                # Reload users.json because change_password() already updated it
                updated_users = load_users()
                updated_user = updated_users[email_norm]
        
                save_user_record(email_norm, updated_user)
                st.session_state["users"][email_norm] = updated_user
        
            except Exception as e:
                st.error(f"Password updated locally but failed to sync to GitHub: {e}")
                return
        
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

