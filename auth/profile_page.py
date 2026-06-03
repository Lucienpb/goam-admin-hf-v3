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

from auth.auth import load_users, save_users, verify_password, change_password
from backend.goam_calculator import GOAMCalculator
from utils.github_storage import save_user_record

PHOTO_DIR = "data/profile_photos"


# ---------------------------------------------------------
# LOAD USER STATS FROM GOAM SCORES
# ---------------------------------------------------------
def _load_user_stats(player_name: str):
    try:
        from backend.goam_loader import GOAMLoader
        goam_scores = GOAMLoader.load_json_scores("data/goam_scores.json")
        season_df = GOAMCalculator.build_from_json(goam_scores)
    except Exception:
        return None

    if season_df.empty or not player_name:
        return None

    # Filter by player name
    user_rounds = season_df[season_df["Name"].str.lower() == player_name.lower()]
    if user_rounds.empty:
        return None

    # Basic stats
    avg_ips = round(user_rounds["IPS"].mean(), 1)
    avg_strokes = round(user_rounds["Strokes"].mean(), 1)
    games_played = len(user_rounds)

    # Games won (highest IPS per round)
    games_won = sum(user_rounds["IPS"] == user_rounds.groupby("Course")["IPS"].transform("max"))

    # OX Nau count (lowest IPS per round)
    ox_count = sum(user_rounds["IPS"] == user_rounds.groupby("Course")["IPS"].transform("min"))

    # Log position (by total IPS across season)
    leaderboard = (
        season_df.groupby("Name")["IPS"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    leaderboard["Position"] = range(1, len(leaderboard) + 1)

    row = leaderboard[leaderboard["Name"].str.lower() == player_name.lower()]
    log_position = int(row["Position"].iloc[0]) if not row.empty else None

    return {
        "avg_ips": avg_ips,
        "avg_strokes": avg_strokes,
        "games_played": games_played,
        "games_won": games_won,
        "ox_count": ox_count,
        "log_position": log_position,
    }


# ---------------------------------------------------------
# PROFILE PHOTO HELPERS
# ---------------------------------------------------------
def _get_photo_path(email: str) -> str:
    os.makedirs(PHOTO_DIR, exist_ok=True)
    return os.path.join(PHOTO_DIR, f"{email}.jpg")


def _load_profile_photo(email: str):
    path = _get_photo_path(email)
    return path if os.path.exists(path) else None


def _save_profile_photo(email: str, uploaded_file):
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

    # Get player name from session state (set during login)
    player_name = st.session_state.get("player_name")
    
    if player_name:
        stats = _load_user_stats(player_name)

        if stats:
            st.markdown(
                f"""
📊 **IPS: Avg.** {stats['avg_ips']}  
📉 **Strokes: Avg.** {stats['avg_strokes']}  
🎯 **Games Played:** {stats['games_played']}  
🏆 **Games Won:** {stats['games_won']}  
📈 **Log Position:** {stats['log_position']}  
🐂 **OX Nau:** {stats['ox_count']}
"""
            )
        else:
            st.info("No GOAM rounds found for your profile yet.")
    else:
        st.warning("Player name not found. Please login again.")

    # DEBUG
    with st.expander("🔍 Debug - Player Session Info"):
        st.json({
            "email": st.session_state.get("email"),
            "player_name": st.session_state.get("player_name"),
            "role": st.session_state.get("role"),
        })

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
    
        try:
            # Save to GitHub user.json
            save_user_record(email_norm, user)
            st.session_state["users"][email_norm] = user
        except Exception as e:
            st.error(f"Failed to sync profile to GitHub: {e}")
            return
    
        st.success("Profile updated successfully!")
        st.stop()

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
            try:
                updated_users = load_users()
                updated_user = updated_users[email_norm]
        
                # Save to GitHub user.json
                save_user_record(email_norm,updated_user)
                st.session_state["users"][email_norm] = updated_user
        
            except Exception as e:
                st.error(f"Password updated locally but failed to sync to GitHub: {e}")
                return
        
            st.success(msg)
            st.stop()
        else:
            st.error(msg)
