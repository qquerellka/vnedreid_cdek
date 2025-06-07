r"""Vacancy finder

------------------------------------------------------------------------

GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) 2020 Kapitanov Alexander

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT
WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT
NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND
PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE
DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR
OR CORRECTION.

------------------------------------------------------------------------
"""

# Authors       : Alexander Kapitanov
# ...
# Contacts      : <empty>
# License       : GNU GENERAL PUBLIC LICENSE

import hashlib
import os
import pickle
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Any, List
from urllib.parse import urlencode
from pathlib import Path

import requests
from tqdm import tqdm
import json
from concurrent.futures import as_completed
import time

CACHE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cache")


class DataCollector:
    """Collect vacancies from HH.ru API."""

    def __init__(self, exchange_rates: Dict[str, float]):
        self.exchange_rates = exchange_rates
        self._cache_dir = Path(__file__).parent.parent / "cache"
        self._cache_dir.mkdir(exist_ok=True)
        self._refresh = False  # Initialize refresh flag
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; HH.ru/1.0; +https://hh.ru)',
            'Accept': '*/*'
        })
        self.__API_BASE_URL = "https://api.hh.ru/vacancies/"
        self.__PROF_ROLES_URL = "https://api.hh.ru/professional_roles"
        self.__DICT_KEYS = (
            "Ids",
            "Employer",
            "Name",
            "Salary",
            "From",
            "To",
            "Experience",
            "Schedule",
            "Keys",
            "Description",
        )

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text by removing HTML tags and extra whitespace.

        Parameters
        ----------
        text : str
            Text to clean

        Returns
        -------
        str
            Cleaned text
        """
        # First remove HTML tags
        text = DataCollector.clean_tags(text)
        # Then clean whitespace
        text = ' '.join(text.split())
        return text.strip()

    @staticmethod
    def clean_tags(html_text: str) -> str:
        """Remove HTML tags from text.

        Parameters
        ----------
        html_text : str
            Text with HTML tags

        Returns
        -------
        str
            Text without HTML tags
        """
        return re.sub(r'<[^>]+>', '', html_text)

    @staticmethod
    def __convert_gross(is_gross: bool) -> float:
        return 0.87 if is_gross else 1

    def _get_vacancy(self, vacancy_id: int) -> Optional[Dict]:
        """Get vacancy data from API or cache."""
        cache_file = self._cache_dir / f"{vacancy_id}.json"
        
        # Try to get from cache first
        if not self._refresh and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Get from API
        try:
            url = f"{self.__API_BASE_URL}{vacancy_id}"
            response = requests.get(url)
            response.raise_for_status()
            vacancy = response.json()
            
            # Cache the result
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(vacancy, f, ensure_ascii=False, indent=2)
            except IOError:
                pass  # Ignore cache write errors
                
            return vacancy
        except (requests.RequestException, json.JSONDecodeError):
            return None

    def get_vacancy(self, vacancy_id: str) -> Dict:
        """Get vacancy data by ID.

        Parameters
        ----------
        vacancy_id : str
            Vacancy ID

        Returns
        -------
        Dict
            Dictionary with vacancy data
        """
        try:
            vacancy = self._get_vacancy(vacancy_id)
            if not vacancy or not isinstance(vacancy, dict):
                return {}

            # Clean and process vacancy data with safe gets
            name = self.clean_text(str(vacancy.get("name", "")))
            description = self.clean_text(str(vacancy.get("description", "")))
            
            # Safe dictionary access for nested fields
            employer = str(vacancy.get("employer", {}).get("name", ""))
            experience = str(vacancy.get("experience", {}).get("name", ""))
            schedule = str(vacancy.get("schedule", {}).get("name", ""))
            
            # Safe list processing for key skills
            key_skills = vacancy.get("key_skills", [])
            if not isinstance(key_skills, list):
                key_skills = []
            keys = [self.clean_text(str(key.get("name", ""))) for key in key_skills]

            # Process salary with proper None handling
            salary_from = None
            salary_to = None
            has_salary = False
            
            salary = vacancy.get("salary")
            if salary and isinstance(salary, dict):
                has_salary = True
                salary_from = salary.get("from")
                salary_to = salary.get("to")
                salary_currency = str(salary.get("currency", "RUR"))

                # Convert salary to RUR if needed
                if salary_currency in self.exchange_rates and self.exchange_rates[salary_currency]:
                    if salary_from is not None:
                        try:
                            salary_from = float(salary_from) * self.exchange_rates[salary_currency]
                        except (TypeError, ValueError):
                            salary_from = None
                    if salary_to is not None:
                        try:
                            salary_to = float(salary_to) * self.exchange_rates[salary_currency]
                        except (TypeError, ValueError):
                            salary_to = None

            return {
                "Ids": str(vacancy_id),
                "Employer": employer,
                "Name": name,
                "Salary": has_salary,
                "From": salary_from,
                "To": salary_to,
                "Experience": experience,
                "Schedule": schedule,
                "Keys": keys,
                "Description": description,
            }
        except Exception as e:
            print(f"Error processing vacancy {vacancy_id}: {str(e)}")
            return {}

    @staticmethod
    def __encode_query_for_url(query: Optional[Dict]) -> str:
        if 'professional_roles' in query:
            query_copy = query.copy()

            roles = '&'.join([f'professional_role={r}' for r in query_copy.pop('professional_roles')])

            return roles + (f'&{urlencode(query_copy)}' if len(query_copy) > 0 else '')

        return urlencode(query)

    def _get_vacancies(self, query: Dict, area: int) -> Optional[Dict]:
        """Get list of vacancies for a specific area.

        Parameters
        ----------
        query : Dict
            Query parameters
        area : int
            Area ID to search in

        Returns
        -------
        Optional[Dict]
            Dictionary with vacancy list data or None if request fails
        """
        try:
            # Prepare query for this area
            area_query = query.copy()
            area_query['area'] = area
            url_params = self.__encode_query_for_url(area_query)
            
            # Check cache first
            if not self._refresh:
                cache_name = f"{url_params}_area_{area}"
                cache_hash = hashlib.md5(cache_name.encode()).hexdigest()
                cache_file = self._cache_dir / cache_hash
                
                if cache_file.exists():
                    try:
                        with open(cache_file, 'rb') as f:
                            return pickle.load(f)
                    except (pickle.UnpicklingError, EOFError):
                        pass

            # Get first page to determine total number of pages
            target_url = f"{self.__API_BASE_URL}?{url_params}"
            response = self.session.get(target_url)
            response.raise_for_status()
            first_page = response.json()

            if not isinstance(first_page, dict) or "items" not in first_page:
                print(f"[WARNING]: Invalid API response for area {area}")
                return None

            # Get total number of pages
            total_pages = first_page.get("pages", 0)
            total_found = first_page.get("found", 0)
            print(f"[INFO]: Area {area} - Found {total_found} vacancies in {total_pages} pages")

            # Collect all pages
            all_items = first_page["items"]
            for page in range(1, total_pages):
                try:
                    page_url = f"{target_url}&page={page}"
                    response = self.session.get(page_url)
                    response.raise_for_status()
                    page_data = response.json()
                    
                    if "items" in page_data:
                        all_items.extend(page_data["items"])
                    else:
                        print(f"[WARNING]: Invalid page data for area {area}, page {page}")
                        break
                        
                    # Add a small delay to avoid rate limiting
                    time.sleep(0.25)
                    
                except Exception as e:
                    print(f"[WARNING]: Failed to fetch page {page} for area {area}: {str(e)}")
                    break

            # Create combined response
            combined_data = first_page.copy()
            combined_data["items"] = all_items
            print(f"[INFO]: Area {area} - Successfully collected {len(all_items)} vacancies")

            # Cache the results
            if not self._refresh:
                cache_file.parent.mkdir(exist_ok=True)
                with open(cache_file, 'wb') as f:
                    pickle.dump(combined_data, f)

            return combined_data

        except requests.RequestException as e:
            print(f"[ERROR]: Failed to fetch vacancies for area {area}: {str(e)}")
            return None
        except Exception as e:
            print(f"[ERROR]: Unexpected error fetching vacancies for area {area}: {str(e)}")
            return None

    def collect_vacancies(
        self, query: Dict, refresh: bool = False, num_workers: int = 10
    ) -> List[Dict]:
        """Collect vacancies from HH.ru API.

        Parameters
        ----------
        query : Dict
            Query parameters
        refresh : bool, optional
            Whether to refresh cached data, by default False
        num_workers : int, optional
            Number of workers for multithreading, by default 10

        Returns
        -------
        List[Dict]
            List of processed vacancies
        """
        self._refresh = refresh
        area_vacancies = {}
        ids = []

        # Collect vacancy IDs for each area
        for area in query.get("area", []):
            print(f"\n[INFO]: Area {area} - Found {query.get('per_page', 100)} vacancies")
            print(f"[INFO]: Area {area} - Processing {query.get('pages', 20)} pages")
            
            # Get vacancies for this area
            data = self._get_vacancies(query, area)
            if not data or "items" not in data:
                print(f"[WARNING]: No data found for area {area}")
                continue
                
            # Collect IDs and store area mapping
            area_ids = [x["id"] for x in data["items"] if "id" in x]
            if not area_ids:
                print(f"[WARNING]: No valid IDs found for area {area}")
                continue
                
            # Store area mapping for each ID
            for vid in area_ids:
                area_vacancies[vid] = area
            ids.extend(area_ids)

        if not ids:
            print("[WARNING]: No vacancy IDs collected")
            return []

        # Process vacancies in parallel
        processed_vacancies = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for vid in ids:
                futures.append(executor.submit(self.get_vacancy, vid))
            
            # Process results as they complete
            for future in tqdm(
                as_completed(futures),
                total=len(ids),
                desc="Get data via HH API (Area 1)",
                unit="it",
            ):
                try:
                    vacancy = future.result()
                    if vacancy:  # Only add non-empty vacancies
                        processed_vacancies.append(vacancy)
                except Exception as e:
                    print(f"[ERROR]: Failed to process vacancy: {str(e)}")
                    continue

        print(f"\n[INFO]: Successfully processed {len(processed_vacancies)} vacancies")
        return processed_vacancies

    @staticmethod
    def get_professional_roles():
        """Get list of available professional roles from HH.ru API
        
        Returns
        -------
        dict
            Dictionary of professional roles with their IDs and names
        """
        try:
            response = requests.get(DataCollector.__PROF_ROLES_URL)
            roles = response.json()
            print("\nAvailable Professional Roles:")
            print("=" * 50)
            for category in roles['categories']:
                print(f"\n{category['name'].upper()}:")
                print("-" * 50)
                for role in category['roles']:
                    print(f"ID: {role['id']:<4} | {role['name']}")
            return roles
        except Exception as e:
            print(f"Error fetching professional roles: {e}")
            return None


if __name__ == "__main__":
    dc = DataCollector(exchange_rates={"USD": 0.01264, "EUR": 0.01083, "RUR": 1.00000})

    vacancies = dc.collect_vacancies(
        query={"text": "FPGA", "area": 1, "per_page": 50},
        # refresh=True
    )
    print(vacancies["Employer"])

    # Print available roles when run directly
    DataCollector.get_professional_roles()
