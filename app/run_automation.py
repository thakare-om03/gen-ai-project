import json
import os
import schedule
import time
from datetime import datetime
import pandas as pd
from chains import Chain
from portfolio import Portfolio
from job_automation import JobAutomation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_settings():
    """Load automation settings from JSON file"""
    try:
        if os.path.exists("automation_settings.json"):
            settings = pd.read_json("automation_settings.json", orient="records").iloc[0].to_dict()
            return settings
        else:
            print("No automation settings found. Please configure in the web UI first.")
            return None
    except Exception as e:
        print(f"Error loading settings: {e}")
        return None

def run_automation():
    """Run the job automation once"""
    print(f"[{datetime.now()}] Running job automation...")
    
    # Load settings
    settings = load_settings()
    if not settings:
        return
    
    # Parse settings
    keywords_list = [kw.strip() for kw in settings["keywords"].split(",")]
    sites_list = [site.strip() for site in settings["sites"].split("\n") if site.strip()]
    emails_per_day = settings["emails_per_day"]
    
    # Initialize components
    chain = Chain()
    portfolio = Portfolio()
    portfolio.load_portfolio()
    
    # Initialize job automation
    job_auto = JobAutomation(
        target_sites=sites_list,
        job_keywords=keywords_list,
        max_jobs_per_day=emails_per_day,
        chain=chain,
        portfolio=portfolio
    )
    
    # Process jobs
    try:
        job_auto.process_jobs()
        print(f"[{datetime.now()}] Automation completed successfully!")
    except Exception as e:
        print(f"[{datetime.now()}] Error during automation: {e}")

def schedule_automation():
    """Schedule the automation based on settings"""
    settings = load_settings()
    if not settings:
        return
    
    # Get schedule time
    try:
        run_time = settings["run_time"]
        days = settings["days"]
        
        # Convert day names to schedule functions
        day_map = {
            "Monday": schedule.every().monday,
            "Tuesday": schedule.every().tuesday,
            "Wednesday": schedule.every().wednesday,
            "Thursday": schedule.every().thursday,
            "Friday": schedule.every().friday,
            "Saturday": schedule.every().saturday,
            "Sunday": schedule.every().sunday
        }
        
        # Schedule for each selected day
        for day in days:
            if day in day_map:
                day_map[day].at(run_time).do(run_automation)
        
        print(f"Automation scheduled to run at {run_time} on {', '.join(days)}")
        
        # Run the scheduling loop
        while True:
            schedule.run_pending()
            time.sleep(60)
    except Exception as e:
        print(f"Error scheduling automation: {e}")
        run_automation()  # Run once if scheduling fails

if __name__ == "__main__":
    # Check if we should run once or schedule
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--once":
        run_automation()
    else:
        schedule_automation()