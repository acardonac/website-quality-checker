import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from datetime import datetime
import re

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_website_info(url):
    try:
        response = requests.get(url, timeout=5)
        info = {
            'status_code': response.status_code,
            'https': url.startswith('https'),
            'headers': dict(response.headers),
            'response_time': response.elapsed.total_seconds()
        }
        return True, info
    except requests.RequestException as e:
        return False, str(e)

def calculate_rating(checked_count, total_items):
    percentage = (checked_count / total_items) * 100
    if percentage >= 80:
        return "Highest", "🟢"
    elif percentage >= 60:
        return "High", "🟢"
    elif percentage >= 40:
        return "Medium", "🟡"
    elif percentage >= 20:
        return "Low", "🟠"
    else:
        return "Lowest", "🔴"

# Set page config
st.set_page_config(page_title="Website Quality Checker", layout="wide")

# Title and description
st.title("Website Quality Checker")
st.markdown("Evaluate website quality based on Google's Search Quality Guidelines")

# URL input section
url_input = st.text_input("Enter website URL to evaluate:", placeholder="https://example.com")

# Initialize session state for initial screening if not exists
if 'initial_screening' not in st.session_state:
    st.session_state.initial_screening = {
        'harmful_purpose': None,
        'potential_harm': None,
        'high_trust_needed': None
    }

# Website information display and initial screening
if url_input:
    if not url_input.startswith(('http://', 'https://')):
        url_input = 'https://' + url_input

    if is_valid_url(url_input):
        success, site_info = get_website_info(url_input)
        
        if success:
            # Basic Website Information
            st.markdown("## Website Analysis")
            col_basic, col_security, col_perf = st.columns(3)
            
            with col_basic:
                st.markdown("### Basic Information")
                st.markdown(f"**Domain:** {urlparse(url_input).netloc}")
                st.markdown(f"**Status:** {'🟢 Online' if site_info['status_code'] == 200 else '🔴 Issues'}")
                if 'last-modified' in site_info['headers']:
                    st.markdown(f"**Last Modified:** {site_info['headers']['last-modified']}")

            with col_security:
                st.markdown("### Security")
                st.markdown(f"**HTTPS:** {'🟢 Yes' if site_info['https'] else '🔴 No'}")
                if 'strict-transport-security' in site_info['headers']:
                    st.markdown("**HSTS:** 🟢 Enabled")
                if 'content-security-policy' in site_info['headers']:
                    st.markdown("**CSP:** 🟢 Enabled")

            with col_perf:
                st.markdown("### Performance")
                st.markdown(f"**Response Time:** {site_info['response_time']:.2f} seconds")
                if 'server' in site_info['headers']:
                    st.markdown(f"**Server:** {site_info['headers']['server']}")

            # Initial Screening Section
            st.markdown("## Initial Screening")
            st.markdown("Complete these critical checks before proceeding with detailed evaluation:")
            
            col_screen1, col_screen2 = st.columns(2)

            with col_screen1:
                st.markdown("### Critical Flags")
                st.session_state.initial_screening['harmful_purpose'] = st.radio(
                    "1. Purpose Assessment",
                    ["No", "Yes"],
                    help="Does the page have a harmful purpose or is it designed to deceive people about its true purpose?",
                    key='harmful_purpose'
                )
                
                st.session_state.initial_screening['potential_harm'] = st.radio(
                    "2. Potential Harm Assessment",
                    ["No", "Yes"],
                    help="Could this page cause harm to people, specific groups, or society? Does it contain harmfully misleading information?",
                    key='potential_harm'
                )

            with col_screen2:
                st.markdown("### Trust Requirements")
                st.session_state.initial_screening['high_trust_needed'] = st.radio(
                    "3. Trust Requirement Level",
                    ["No", "Yes"],
                    help="Is this page from a website that needs high level of trust? (e.g., online store, medical info, news about civic issues)",
                    key='high_trust_needed'
                )

            # Show warnings based on initial screening
            if st.session_state.initial_screening['harmful_purpose'] == "Yes" or \
               st.session_state.initial_screening['potential_harm'] == "Yes":
                st.error("⚠️ ALERT: Based on initial screening, this page requires a LOWEST quality rating. Proceed with full evaluation for documentation.")
            elif st.session_state.initial_screening['high_trust_needed'] == "Yes":
                st.warning("⚠️ Notice: This page requires additional scrutiny during evaluation due to its high trust requirements.")

            st.markdown("---")
        else:
            st.error(f"Could not access website: {site_info}")
    else:
        st.error("Please enter a valid URL")

# Define criteria categories
criteria = {
    "Purpose & E-E-A-T": [
        "Clear beneficial purpose or main content",
        "Appropriate E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)",
        "Website is well-maintained and regularly updated"
    ],
    "Content Quality": [
        "High-quality main content",
        "Accurate, factual information",
        "Descriptive, helpful title"
    ],
    "Website Reputation": [
        "Positive reputation for website/creator",
        "Satisfying amount of website information/contact info",
        "Clear who is responsible for content"
    ],
    "Design & Functionality": [
        "Functional page design and layout",
        "Mobile-friendly design",
        "Ads (if present) don't interfere with main content"
    ],
    "Security & Privacy": [
        "Secure transaction handling (if applicable)",
        "Clear privacy policy",
        "Uses HTTPS for secure connection"
    ]
}

# Initialize session state for checkboxes if not exists
if 'checked_items' not in st.session_state:
    st.session_state.checked_items = {}

# Initialize session state for notes if not exists
if 'notes' not in st.session_state:
    st.session_state.notes = ""

# Create columns for better layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## Detailed Evaluation")
    # Create checkboxes for each category
    for category, items in criteria.items():
        st.subheader(category)
        for item in items:
            key = f"{category}_{item}"
            checked = st.checkbox(item, key=key)
            st.session_state.checked_items[key] = checked
        st.markdown("---")

    # Add notes section
    st.subheader("Evaluation Notes")
    st.session_state.notes = st.text_area(
        "Add any additional observations or notes about the website:",
        value=st.session_state.notes,
        height=100
    )

with col2:
    # Calculate and display the current rating
    total_items = sum(len(items) for items in criteria.values())
    checked_count = sum(1 for value in st.session_state.checked_items.values() if value)
    
    rating, indicator = calculate_rating(checked_count, total_items)
    
    # Override rating if initial screening indicated Lowest
    if st.session_state.initial_screening.get('harmful_purpose') == "Yes" or \
       st.session_state.initial_screening.get('potential_harm') == "Yes":
        rating, indicator = "Lowest", "🔴"
    
    # Create a card-like container for the rating
    st.markdown("### Current Rating")
    rating_container = st.container()
    with rating_container:
        st.markdown(f"""
        <div style='padding: 20px; border-radius: 10px; background-color: #f0f2f6;'>
            <h2 style='margin:0;color:#000;font-size:25px;'>{indicator} {rating} Quality</h2>
            <p style='margin:5px 0 0 0;color:#000;'>{checked_count} of {total_items} criteria met</p>
            <p style='margin:5px 0 0 0;color:#000;'>Score: {(checked_count/total_items*100):.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

    # Add explanation of ratings
    st.markdown("### Rating Scale")
    st.markdown("""
    - 🟢 Highest: 80-100%
    - 🟢 High: 60-79%
    - 🟡 Medium: 40-59%
    - 🟠 Low: 20-39%
    - 🔴 Lowest: 0-19% or fails initial screening
    """)

# Add export results button
if st.button("Export Results"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = {
        "Evaluation Date": timestamp,
        "Website URL": url_input if url_input else "Not specified",
        "Initial Screening Results": st.session_state.initial_screening,
        "Quality Rating": rating,
        "Score": f"{(checked_count/total_items*100):.1f}%",
        "Criteria Met": f"{checked_count}/{total_items}",
        "Notes": st.session_state.notes,
        "Checked Items": {k: v for k, v in st.session_state.checked_items.items() if v}
    }
    st.json(results)

# Add reset button at the bottom
if st.button("Reset All"):
    st.session_state.checked_items = {}
    st.session_state.notes = ""
    st.session_state.initial_screening = {
        'harmful_purpose': None,
        'potential_harm': None,
        'high_trust_needed': None
    }
    if 'url_input' in st.session_state:
        del st.session_state.url_input
    st.experimental_rerun()
