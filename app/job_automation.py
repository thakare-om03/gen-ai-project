import schedule
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text

class JobAutomation:
    def __init__(self, target_sites, job_keywords, max_jobs_per_day=5, chain=None, portfolio=None):
        """
        Initialize the job automation system
        
        Args:
            target_sites (list): List of job site URLs to scrape
            job_keywords (list): List of keywords to filter jobs by
            max_jobs_per_day (int): Maximum number of emails to generate per day
            chain (Chain, optional): Chain instance for processing jobs
            portfolio (Portfolio, optional): Portfolio instance
        """
        self.target_sites = target_sites
        self.job_keywords = job_keywords
        self.max_jobs_per_day = max_jobs_per_day
        self.chain = chain or Chain()
        self.portfolio = portfolio or Portfolio()
        
        if portfolio is None:
            self.portfolio.load_portfolio()
            
        self.processed_jobs = self._load_processed_jobs()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
    def _load_processed_jobs(self):
        """Load list of already processed job URLs"""
        try:
            if os.path.exists('processed_jobs.csv'):
                df = pd.read_csv('processed_jobs.csv')
                return set(df['job_url'].tolist())
            return set()
        except Exception as e:
            print(f"Error loading processed jobs: {e}")
            return set()
            
    def _save_processed_job(self, job_url, email, job_data):
        """Save a record of processed job"""
        today = datetime.now().strftime('%Y-%m-%d')
        new_row = pd.DataFrame({
            'date': [today],
            'job_url': [job_url],
            'email': [email],
            'job_data': [str(job_data)]
        })
        
        if os.path.exists('processed_jobs.csv'):
            df = pd.read_csv('processed_jobs.csv')
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row
            
        df.to_csv('processed_jobs.csv', index=False)
        self.processed_jobs.add(job_url)
        
    def scrape_job_listings(self, site_url):
        """
        Scrape job listings from a target site
        
        Args:
            site_url (str): The URL to scrape for job listings
            
        Returns:
            list: List of job URLs found
        """
        try:
            response = requests.get(site_url, headers=self.headers, timeout=30)
            response.raise_for_status()  # Raise exception for bad status codes
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # List to store job links
            job_links = []
            
            # Site-specific scraping logic - this is a generic approach
            # LinkedIn jobs
            if 'linkedin.com' in site_url.lower():
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/jobs/view/' in href:
                        if not href.startswith(('http://', 'https://')):
                            href = f"https://www.linkedin.com{href}"
                        job_links.append(href)
            
            # Indeed jobs
            elif 'indeed.com' in site_url.lower():
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/viewjob?' in href or '/company/' in href:
                        if not href.startswith(('http://', 'https://')):
                            href = f"https://www.indeed.com{href}"
                        job_links.append(href)
            
            # Generic job links (fallback for other sites)
            else:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Filter for job links (customize this logic for each site)
                    if '/job/' in href or '/career/' in href or '/position/' in href or 'viewjob' in href:
                        if not href.startswith(('http://', 'https://')):
                            # Handle relative URLs
                            if href.startswith('/'):
                                base_url = '/'.join(site_url.split('/')[:3])  # Get domain part of URL
                                href = base_url + href
                            else:
                                href = f"{site_url.rstrip('/')}/{href.lstrip('/')}"
                        
                        job_links.append(href)
            
            # Remove duplicates and return
            return list(set(job_links))
            
        except requests.RequestException as e:
            print(f"Error scraping {site_url}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error scraping {site_url}: {e}")
            return []
            
    def filter_relevant_jobs(self, job_urls):
        """
        Filter jobs based on keywords and already processed URLs
        
        Args:
            job_urls (list): List of job URLs to filter
            
        Returns:
            list: Filtered list of job URLs
        """
        relevant_jobs = []
        count = 0
        
        for url in job_urls:
            # Skip already processed jobs
            if url in self.processed_jobs:
                continue
                
            try:
                # Load job page
                loader = WebBaseLoader([url])
                data = clean_text(loader.load().pop().page_content)
                
                # Check if any keywords match
                if any(keyword.lower() in data.lower() for keyword in self.job_keywords):
                    relevant_jobs.append(url)
                    count += 1
                    
                # Stop once we've found enough jobs
                if count >= self.max_jobs_per_day:
                    break
                    
                # Small delay to avoid overwhelming the servers
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error filtering job {url}: {e}")
                
        return relevant_jobs
    
    def process_jobs(self):
        """Process jobs and generate emails"""
        all_job_urls = []
        
        # Scrape all target sites
        for site in self.target_sites:
            job_urls = self.scrape_job_listings(site)
            all_job_urls.extend(job_urls)
            
        # Filter to relevant jobs
        relevant_jobs = self.filter_relevant_jobs(all_job_urls)
        
        print(f"Found {len(relevant_jobs)} new relevant jobs")
        
        # Process each job
        processed_count = 0
        for job_url in relevant_jobs:
            try:
                # Load and process job
                loader = WebBaseLoader([job_url])
                data = clean_text(loader.load().pop().page_content)
                
                # Extract job details
                jobs = self.chain.extract_jobs(data)
                
                for job in jobs:
                    skills = job.get('skills', [])
                    links = self.portfolio.query_links(skills)
                    email = self.chain.write_mail(job, links)
                    
                    # Save generated email and mark job as processed
                    self._save_processed_job(job_url, email, job)
                    
                    # Log success
                    print(f"Generated email for job: {job.get('role', 'Unknown Role')} at {job_url}")
                    
                    processed_count += 1
                    if processed_count >= self.max_jobs_per_day:
                        print(f"Reached daily limit of {self.max_jobs_per_day} jobs")
                        return
                    
            except Exception as e:
                print(f"Error processing job {job_url}: {e}")
    
    def run_daily(self, hour=9, minute=0):
        """Schedule the job to run daily at specified time"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.process_jobs)
        
        print(f"Job automation scheduled to run daily at {hour:02d}:{minute:02d}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

# Example usage in your main app
if __name__ == "__main__":
    target_sites = [
        "https://jobs.linkedin.com/jobs/search?keywords=software%20consulting",
        "https://www.indeed.com/jobs?q=AI%20consulting"
    ]
    
    job_keywords = [
        "python", "machine learning", "AI", "data science", 
        "software engineer", "developer", "consulting"
    ]
    
    automation = JobAutomation(
        target_sites=target_sites,
        job_keywords=job_keywords,
        max_jobs_per_day=3
    )
    
    # Run once immediately for testing
    automation.process_jobs()