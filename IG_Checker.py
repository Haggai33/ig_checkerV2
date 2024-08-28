import streamlit as st
import re
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import time
import csv
from datetime import datetime
import logging
import os
import chardet


def setup_logging():
    log_filename = datetime.now().strftime("instagram_check_%Y%m%d_%H%M%S.log")
    log_filepath = os.path.join(os.path.expanduser("~"), "Downloads", log_filename)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_filepath),
                            logging.StreamHandler()
                        ])


def load_ig_users_from_csv(file_path):
    ig_users_from_csv = []
    valid_count = 0
    empty_count = 0
    error_count = 0

    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        file_encoding = result['encoding']

    try:
        with open(file_path, mode='r', encoding=file_encoding) as file:
            reader = csv.DictReader(file)
            reader.fieldnames = [name.lower() for name in reader.fieldnames]
            column_name = "ig user"

            if column_name not in reader.fieldnames:
                raise ValueError("Column 'ig user' not found in the CSV file")

            for row in reader:
                try:
                    ig_user = row.get(column_name)
                    if ig_user and ig_user.strip():
                        ig_users_from_csv.append(ig_user.strip())
                        valid_count += 1
                    else:
                        empty_count += 1
                except Exception as e:
                    error_count += 1
    except Exception as e:
        st.error(f"Error reading file: {e}")

    return ig_users_from_csv, valid_count, empty_count, error_count


def extract_artist_and_usernames(input_text):
    lines = input_text.split("\n")
    artist_user_pairs = []

    for i in range(1, len(lines)):
        if lines[i].startswith('@'):
            artist_name = lines[i - 1].strip()
            ig_user = lines[i].strip().lstrip('@')
            artist_user_pairs.append((artist_name, ig_user))

    return artist_user_pairs


def check_instagram_profiles(ig_users):
    driver = webdriver.Chrome()
    profile_status = {}
    base_url = "https://www.instagram.com/"

    status_placeholder = st.empty()  # Placeholder for status update
    results_placeholder = st.empty()  # Placeholder for results display

    results_text = ""

    total_users = len(ig_users)
    for i, username in enumerate(ig_users, start=1):
        status_placeholder.text(f"Processing {i}/{total_users} users... Checking: {username}")

        try:
            url = base_url + username
            driver.get(url)
            time.sleep(2)
            page_source = driver.page_source
            if "Sorry, this page isn't available." in page_source:
                profile_status[username] = "Not Valid"
            else:
                profile_status[username] = "Valid"
        except WebDriverException:
            profile_status[username] = "Not Valid"
        except Exception:
            profile_status[username] = "Not Valid"

        # Update results in the placeholder
        results_text += f"{username:<30} | {profile_status[username]}\n"
        results_placeholder.text_area("Processed Users", results_text, height=300)

    driver.quit()
    return profile_status


def format_results_for_display(profile_status):
    valid_data = []
    invalid_data = []
    valid_count = 0
    invalid_count = 0

    for username, is_valid in profile_status.items():
        if is_valid == "Valid":
            valid_data.append(f"{username}")
            valid_count += 1
        else:
            invalid_data.append(f"{username}")
            invalid_count += 1

    total_checked = valid_count + invalid_count
    summary = f"Total Checked: {total_checked}\nValid: {valid_count}\nNot Valid: {invalid_count}"

    return "\n".join(valid_data + invalid_data), "\n".join(invalid_data), "\n".join(valid_data), summary


def export_to_csv(profile_status, file_path):
    csv_output = "IG User,Status,Timestamp\n"
    for username, is_valid in profile_status.items():
        csv_output += f"{username},{is_valid},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    csv_file_path = os.path.join(file_path, "instagram_profiles.csv")
    with open(csv_file_path, "w") as f:
        f.write(csv_output)

    return csv_file_path


def export_to_text(profile_status, file_path):
    text_output = ""
    for username, is_valid in profile_status.items():
        text_output += f"{username} | {is_valid} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    text_file_path = os.path.join(file_path, "instagram_profiles.txt")
    with open(text_file_path, "w") as f:
        f.write(text_output)

    return text_file_path


def handle_csv_upload(file):
    user_home = os.path.expanduser("~")
    download_folder = os.path.join(user_home, "Downloads")

    ig_users, _, _, _ = load_ig_users_from_csv(file)
    profile_status = check_instagram_profiles(ig_users)
    all_data, invalid_data, valid_data, summary = format_results_for_display(profile_status)

    csv_path = export_to_csv(profile_status, download_folder)
    text_path = export_to_text(profile_status, download_folder)

    return all_data, invalid_data, valid_data, summary, csv_path, text_path


def handle_text_input(input_text):
    user_home = os.path.expanduser("~")
    download_folder = os.path.join(user_home, "Downloads")

    artist_user_pairs = extract_artist_and_usernames(input_text)
    ig_users = [username for artist, username in artist_user_pairs]
    profile_status = check_instagram_profiles(ig_users)
    all_data, invalid_data, valid_data, summary = format_results_for_display(profile_status)

    csv_path = export_to_csv(profile_status, download_folder)
    text_path = export_to_text(profile_status, download_folder)

    return all_data, invalid_data, valid_data, summary, csv_path, text_path


# ממשק המשתמש של Streamlit
st.title("Instagram Profile Checker")
st.markdown("**Developed by Chagai Yechiel**")

tab1, tab2 = st.tabs(["Manual Input", "Upload CSV"])

with tab1:
    input_text = st.text_area("Enter Artists and Usernames", placeholder="Artist Name\n@username\n...")
    if st.button("Submit"):
        all_data, invalid_data, valid_data, summary, csv_path, text_path = handle_text_input(input_text)
        st.write("Summary")
        st.text(summary)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("All Results")
            st.text(all_data)
        with col2:
            st.write("Invalid Results")
            st.text(invalid_data)
        with col3:
            st.write("Valid Results")
            st.text(valid_data)
        st.download_button("Download CSV", open(csv_path, "rb"), "instagram_profiles.csv")
        st.download_button("Download Text", open(text_path, "rb"), "instagram_profiles.txt")

with tab2:
    uploaded_file = st.file_uploader("Upload CSV file with IG Users")
    if st.button("Upload and Process"):
        if uploaded_file is not None:
            all_data, invalid_data, valid_data, summary, csv_path, text_path = handle_csv_upload(uploaded_file)
            st.write("Summary")
            st.text(summary)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("All Results")
                st.text(all_data)
            with col2:
                st.write("Invalid Results")
                st.text(invalid_data)
            with col3:
                st.write("Valid Results")
                st.text(valid_data)
            st.download_button("Download CSV", open(csv_path, "rb"), "instagram_profiles.csv")
            st.download_button("Download Text", open(text_path, "rb"), "instagram_profiles.txt")
        else:
            st.error("Please upload a CSV file.")
