#main.py

import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
import os
import webbrowser
import urllib.parse
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from job_automation import JobAutomation

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="Cold Email Generator",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better formatting
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #1976D2;
        background-color: #F5F7F9;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .email-container {
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 5px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
        white-space: pre-line;
        font-family: Arial, sans-serif;
        line-height: 1.6;
    }
    .card {
        padding: 1.5rem;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
    }
    .copy-btn {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'step' not in st.session_state:
        st.session_state.step = 1  # Start at step 1 - API Key
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv("GROQ_API_KEY", "")
    
    if 'portfolio_df' not in st.session_state:
        # Try to load existing portfolio
        try:
            st.session_state.portfolio_df = pd.read_csv("my_portfolio.csv")
        except:
            # Create empty portfolio dataframe
            st.session_state.portfolio_df = pd.DataFrame(columns=["Techstack", "Links"])
    
    if 'generated_email' not in st.session_state:
        st.session_state.generated_email = ""
        
    if 'job_details' not in st.session_state:
        st.session_state.job_details = None

def set_step(step):
    st.session_state.step = step

def open_email_client(subject, body, recipient=""):
    """Open default email client with the generated email"""
    subject_encoded = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body)
    mailto_link = f"mailto:{recipient}?subject={subject_encoded}&body={body_encoded}"
    webbrowser.open(mailto_link)

def main():
    # Initialize session state
    init_session_state()
    
    # App header
    st.markdown('<div class="main-header">📧 Cold Email Generator</div>', unsafe_allow_html=True)
    st.markdown("Generate personalized cold emails for business opportunities based on job listings")
    
    # Progress bar to show steps
    progress_percent = (st.session_state.step - 1) / 4  # Value between 0 and 1
    st.progress(progress_percent)
    
    # Step indicator - make sure we're accessing a valid index
    steps = ["API Key Setup", "Portfolio Management", "Job Selection", "Email Generation", "Email Review and Send"]
    current_step_idx = min(st.session_state.step - 1, len(steps) - 1)  # Prevent index out of bounds
    st.write(f"Step {st.session_state.step} of 5: **{steps[current_step_idx]}**")
    
    # Step 1: API Key Setup
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">Step 1: API Key Setup</div>', unsafe_allow_html=True)
        
        api_key = os.getenv("GROQ_API_KEY") or st.session_state.api_key
        
        if not api_key:
            st.warning("⚠️ No API key found. Please enter your GROQ API key to continue.")
            api_key = st.text_input("Enter your GROQ API key:", type="password")
            if api_key:
                st.session_state.api_key = api_key
                st.success("API key saved successfully! You can now proceed to the next step.")
                
        else:
            st.success("✅ API key is set. You're ready to proceed!")
            
        # Check if we can proceed to the next step
        if st.session_state.api_key:
            if st.button("Next: Manage Portfolio"):
                set_step(2)
                st.rerun()
    
    # Step 2: Portfolio Management
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">Step 2: Portfolio Management</div>', unsafe_allow_html=True)
        
        portfolio_tabs = st.tabs(["Current Portfolio", "Upload CSV", "Manual Entry"])
        
        with portfolio_tabs[0]:
            st.subheader("Current Portfolio Items")
            
            # Show current portfolio
            st.dataframe(st.session_state.portfolio_df, use_container_width=True)
            
            if st.button("Save and Use Current Portfolio"):
                try:
                    st.session_state.portfolio_df.to_csv("my_portfolio.csv", index=False)
                    # Initialize portfolio for next step
                    portfolio = Portfolio()
                    portfolio.data = st.session_state.portfolio_df
                    portfolio.reset_collection()
                    portfolio.load_portfolio()
                    
                    st.success("Portfolio saved successfully!")
                    set_step(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving portfolio: {str(e)}")
        
        with portfolio_tabs[1]:
            st.subheader("Upload Portfolio CSV")
            st.markdown("Upload a CSV file with columns: 'Techstack', 'Links'")
            
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.dataframe(df, use_container_width=True)
                    
                    if st.button("Use This Portfolio"):
                        st.session_state.portfolio_df = df
                        df.to_csv("my_portfolio.csv", index=False)
                        
                        # Initialize portfolio for next step
                        portfolio = Portfolio()
                        portfolio.data = df
                        portfolio.reset_collection()
                        portfolio.load_portfolio()
                        
                        st.success("Portfolio updated successfully!")
                        set_step(3)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error processing uploaded file: {str(e)}")
        
        with portfolio_tabs[2]:
            st.subheader("Add Portfolio Item")
            
            # Form for adding new portfolio item
            with st.form("portfolio_form"):
                techstack = st.text_input("Technologies (comma-separated):")
                link = st.text_input("Portfolio Link:")
                
                submitted = st.form_submit_button("Add to Portfolio")
                if submitted and techstack and link:
                    # Add to dataframe
                    new_row = pd.DataFrame({"Techstack": [techstack], "Links": [link]})
                    st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, new_row], ignore_index=True)
                    st.success("Item added to portfolio!")
                    st.session_state.portfolio_df.to_csv("my_portfolio.csv", index=False)
                    
                    # Initialize portfolio for next step
                    portfolio = Portfolio()
                    portfolio.data = st.session_state.portfolio_df
                    portfolio.reset_collection()
                    portfolio.load_portfolio()
        
        # Navigation buttons            
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to API Setup"):
                set_step(1)
                st.rerun()
        with col2:
            if st.button("Next: Job Selection →"):
                # Make sure portfolio exists
                if len(st.session_state.portfolio_df) > 0:
                    set_step(3)
                    st.rerun()
                else:
                    st.error("Please add at least one portfolio item before proceeding.")
    
    # Step 3: Job Selection
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">Step 3: Job Selection</div>', unsafe_allow_html=True)
        
        selection_tabs = st.tabs(["Enter Job URL", "Search Jobs"])
        
        with selection_tabs[0]:
            st.subheader("Enter Job URL")
            
            # Job URL input
            job_url = st.text_input("Enter job listing URL:", 
                                    value="https://in.indeed.com/viewjob?jk=6d389a44877a2bd2&from=shareddesktop_copy")
            
            if st.button("Process Job URL"):
                if job_url:
                    with st.spinner("Processing job URL..."):
                        try:
                            # Initialize components
                            chain = Chain(api_key=st.session_state.api_key)
                            portfolio = Portfolio()
                            portfolio.load_portfolio()
                            
                            # Fetch and process job data
                            loader = WebBaseLoader([job_url])
                            data = clean_text(loader.load().pop().page_content)
                            
                            # Extract job details
                            jobs = chain.extract_jobs(data)
                            
                            if jobs:
                                st.session_state.job_details = jobs[0]  # Use the first job
                                st.success("Job details extracted successfully!")
                                set_step(4)
                                st.rerun()
                            else:
                                st.error("No job details could be extracted from the provided URL.")
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
                else:
                    st.error("Please enter a job URL.")
        
        with selection_tabs[1]:
            st.subheader("Search for Jobs")
            
            # Job search form
            with st.form("job_search_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    keywords = st.text_input("Search Keywords:", 
                                            value="python, machine learning, AI, data science")
                
                with col2:
                    max_results = st.number_input("Maximum Results:", min_value=1, max_value=20, value=5)
                
                sites = st.text_area("Job Sites (one URL per line):", 
                                    value="https://jobs.linkedin.com/jobs/search?keywords=software%20consulting\nhttps://www.indeed.com/jobs?q=AI%20consulting")
                
                search_submitted = st.form_submit_button("Search Jobs")
            
            if search_submitted:
                with st.spinner("Searching for jobs..."):
                    try:
                        # Parse inputs
                        keywords_list = [kw.strip() for kw in keywords.split(",")]
                        sites_list = [site.strip() for site in sites.split("\n") if site.strip()]
                        
                        # Initialize job automation
                        job_auto = JobAutomation(
                            target_sites=sites_list,
                            job_keywords=keywords_list,
                            max_jobs_per_day=max_results
                        )
                        
                        # Get job listings
                        all_job_urls = []
                        for site in sites_list:
                            job_urls = job_auto.scrape_job_listings(site)
                            all_job_urls.extend(job_urls)
                        
                        # Filter relevant jobs
                        relevant_jobs = job_auto.filter_relevant_jobs(all_job_urls)
                        
                        # Store in session state
                        st.session_state.search_results = relevant_jobs
                        
                        st.success(f"Found {len(relevant_jobs)} relevant job listings!")
                    except Exception as e:
                        st.error(f"Error searching for jobs: {str(e)}")
            
            # Display search results
            if 'search_results' in st.session_state and st.session_state.search_results:
                st.subheader("Search Results")
                
                for i, job_url in enumerate(st.session_state.search_results):
                    with st.expander(f"Job {i+1}: {job_url}"):
                        st.write(f"URL: {job_url}")
                        
                        if st.button("Select This Job", key=f"select_job_{i}"):
                            with st.spinner("Processing job..."):
                                try:
                                    # Initialize components
                                    chain = Chain(api_key=st.session_state.api_key)
                                    
                                    # Fetch and process job data
                                    loader = WebBaseLoader([job_url])
                                    data = clean_text(loader.load().pop().page_content)
                                    
                                    # Extract job details
                                    jobs = chain.extract_jobs(data)
                                    
                                    if jobs:
                                        st.session_state.job_details = jobs[0]  # Use the first job
                                        st.success("Job details extracted successfully!")
                                        set_step(4)
                                        st.rerun()
                                    else:
                                        st.error("No job details could be extracted from the provided URL.")
                                except Exception as e:
                                    st.error(f"An error occurred: {str(e)}")
        
        # Navigation buttons
        if st.button("← Back to Portfolio Management"):
            set_step(2)
            st.rerun()
    
    # Step 4: Email Generation
    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">Step 4: Email Generation</div>', unsafe_allow_html=True)
        
        # Check if we have job details
        if not st.session_state.job_details:
            st.error("No job details found. Please go back and select a job.")
            if st.button("← Back to Job Selection"):
                set_step(3)
                st.rerun()
            return
        
        # Show job details
        with st.expander("Job Details", expanded=True):
            st.json(st.session_state.job_details)
        
        # Email generation settings
        st.subheader("Email Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Your Company Name:", value="TCS")
            sender_name = st.text_input("Your Name:", value="Om Thakare")
        
        with col2:
            email_length = st.select_slider(
                "Email Length:",
                options=["Short", "Medium", "Long"],
                value="Medium"
            )
        
        # Generate button
        if st.button("Generate Email"):
            with st.spinner("Generating email..."):
                try:
                    # Initialize components
                    chain = Chain(api_key=st.session_state.api_key)
                    portfolio = Portfolio()
                    portfolio.load_portfolio()
                    
                    # Get portfolio matches
                    skills = st.session_state.job_details.get('skills', [])
                    links = portfolio.query_links(skills)
                    
                    # Generate email with improved formatting instruction
                    email = chain.write_mail(
                        st.session_state.job_details, 
                        links, 
                        email_length, 
                        company_name, 
                        sender_name
                    )
                    
                    # Save the generated email
                    st.session_state.generated_email = email
                    
                    # Extract subject from the email (assuming first line is subject)
                    email_lines = email.strip().split('\n')
                    subject = ""
                    body = email
                    
                    if email_lines and email_lines[0].startswith("Subject:"):
                        subject = email_lines[0].replace("Subject:", "").strip()
                        body = "\n".join(email_lines[1:])
                    
                    st.session_state.email_subject = subject
                    st.session_state.email_body = body
                    
                    set_step(5)
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        
        # Navigation button
        if st.button("← Back to Job Selection"):
            set_step(3)
            st.rerun()
    
    # Step 5: Email Review and Send
    elif st.session_state.step == 5:
        st.markdown('<div class="step-header">Step 5: Email Review and Send</div>', unsafe_allow_html=True)
        
        # Display the generated email
        st.subheader("Generated Email")
        
        if st.session_state.generated_email:
            # Format email properly with line breaks preserved
            st.markdown(f'<div class="email-container">{st.session_state.generated_email}</div>', unsafe_allow_html=True)
            
            # Copy to clipboard
            st.code(st.session_state.generated_email)
            
            # Email client integration
            st.subheader("Send Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Open in Email Client"):
                    open_email_client(
                        st.session_state.email_subject, 
                        st.session_state.email_body
                    )
                    st.success("Opening email client...")
            
            with col2:
                if st.button("Generate Another Email"):
                    # Reset job details
                    st.session_state.job_details = None
                    st.session_state.generated_email = ""
                    set_step(3)
                    st.rerun()
        else:
            st.error("No email has been generated. Please go back and generate an email.")
        
        # Navigation button - FIX: Change step to 4 instead of 5
        if st.button("← Back to Email Settings"):
            set_step(4)  # Corrected to go back to step 4
            st.rerun()

if __name__ == "__main__":
    main()