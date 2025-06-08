"""Resume collector for HH.ru API.

This module provides functionality to collect and parse resumes from HeadHunter.ru API.
It supports searching resumes by various criteria and collecting detailed resume information.

Example:
    collector = ResumeCollector()
    resumes = collector.collect_resumes(
        text="Python Developer",
        area=1,
        professional_roles=[96],
        refresh=True
    )
"""

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Union
import time
import os
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResumeCollector:
    """Collect resumes from HH.ru using Selenium web scraping."""

    def __init__(self):
        """Initialize the resume collector."""
        self._cache_dir = Path(__file__).parent.parent / "cache"
        self._cache_dir.mkdir(exist_ok=True)
        self.refresh = False
        self.session = requests.Session() # Keep session for potential other uses, though not for scraping
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; HH.ru/1.0; +https://hh.ru)',
            'Accept': '*/*'
        })
        self.__BASE_URL = "https://hh.ru"
        
        # Default credentials
        self.username = "a.raspoperova@cdek.ru"
        self.password = "Qwerty15243"

        # Initialize WebDriver - using Chrome for this example
        # You can choose other browsers like Firefox by changing webdriver.Chrome to webdriver.Firefox
        self.browser = webdriver.Chrome() 
        self.browser.maximize_window()
            self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with HH.ru using Selenium to log in."""
        try:
            logger.info("Attempting to log in to HH.ru...")
            self.browser.get(f"{self.__BASE_URL}/account/login")

            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )

            email_input = self.browser.find_element(By.NAME, "username")
            password_input = self.browser.find_element(By.NAME, "password")
            
            email_input.send_keys(self.username)
            password_input.send_keys(self.password)

            password_input.submit()

            # Wait for successful login (e.g., checking for a specific element on the dashboard)
            WebDriverWait(self.browser, 10).until(
                EC.url_to_be(self.__BASE_URL + '/applicant/resumes') or EC.url_to_be(self.__BASE_URL + '/')
            )
            logger.info("Successfully logged in to HH.ru")
            return True
        except Exception as e:
            logger.error(f"Failed to log in to HH.ru: {str(e)}")
            return False

    def _get_resumes(self, text: str, area: int, professional_roles: List[int], page: int = 0) -> List[Dict]:
        """Fetch a single page of resumes from HH.ru."""
        try:
            query_params = {
                'text': text,
                'area': area,
                'professional_role': professional_roles,
                'page': page
            }
            encoded_params = urlencode(query_params, doseq=True) # doseq=True for multiple professional_roles
            search_url = f"{self.__BASE_URL}/search/resume?{encoded_params}"
            logger.info(f"Navigating to: {search_url}")
            self.browser.get(search_url)

            # Wait for resume search results to load
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.resume-search-item__content-wrapper'))
            )

            resumes_data = []
            resume_elements = self.browser.find_elements(By.CSS_SELECTOR, '.resume-search-item__content-wrapper')
            for resume_elem in resume_elements:
                try:
                    name = resume_elem.find_element(By.CSS_SELECTOR, '.resume-search-item__name').text
                    age = resume_elem.find_element(By.CSS_SELECTOR, '.resume-search-item__fullname').text
                    try:
                        salary = resume_elem.find_element(By.CSS_SELECTOR, '.resume-search-item__compensation').text
                    except: # Salary might not always be present
                        salary = "N/A"
                    resume_link = resume_elem.find_element(By.CSS_SELECTOR, '.resume-search-item__name').get_attribute('href')
                    
                    resumes_data.append({
                        'name': name,
                        'age': age,
                        'salary': salary,
                        'resume_link': resume_link
                    })
                except Exception as e:
                    logger.warning(f"Could not parse resume element: {str(e)}")
                    continue
            return resumes_data
        except Exception as e:
            logger.error(f"Error fetching resumes for page {page}: {str(e)}")
            raise

    def collect_resumes(self, text: str, area: int, professional_roles: List[int], refresh: bool = False, max_pages: int = 5) -> List[Dict]:
        """Collect resumes based on search criteria."""
        self.refresh = refresh
        all_resumes = []
        logger.info(f"Collecting resumes for area {area}...")

        for page in range(max_pages):
            try:
                logger.info(f"Collecting resumes from page {page + 1}...")
                page_resumes = self._get_resumes(text, area, professional_roles, page)
                if not page_resumes: # Stop if no more resumes on this page
                    logger.info(f"No more resumes found on page {page + 1}. Stopping collection.")
                    break
                all_resumes.extend(page_resumes)
                time.sleep(2) # Be kind to the server and avoid getting blocked
            except Exception as e:
                logger.error(f"Failed to collect resumes from page {page + 1}: {str(e)}")
                break # Stop on error

        # Close the browser when done
        self.browser.quit()
        return all_resumes

    def get_exchange_rates(self) -> Dict[str, Optional[float]]:
        """Get exchange rates from HH.ru API. This still uses requests, as it's separate from resume scraping."""
        try:
            response = self.session.get("https://api.hh.ru/dictionaries")
            response.raise_for_status()
            data = response.json()
            exchange_rates = {
                rate['abbr']: rate['rate'] for rate in data.get('currency', [])
            }
            # Add RUR as 1 for consistency
            exchange_rates['RUR'] = 1.0
            logger.info(f"Get exchange rates: {exchange_rates}")
            return exchange_rates
        except RequestException as e:
            logger.error(f"Error fetching exchange rates: {e}")
            return {'RUR': 1, 'USD': None, 'EUR': None}
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching exchange rates: {e}")
            return {'RUR': 1, 'USD': None, 'EUR': None}

# Helper function for salary conversion - can be removed or adapted if not needed for scraped data
def convert_salary_to_rubles(salary: Union[int, str], currency: str, exchange_rates: Dict[str, Optional[float]]) -> Optional[float]:
    """Converts salary to rubles based on exchange rates."""
    if isinstance(salary, str):
        salary = int(re.sub(r'[^\d]', '', salary)) # Clean string if it contains non-digits
    
    rate = exchange_rates.get(currency)
    if rate is None:
        logger.warning(f"Exchange rate for {currency} not found.")
        return None
    return salary * rate 