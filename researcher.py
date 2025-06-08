"""Head Hunter Researcher

Description   :
    HeadHunter (hh.ru) main research script.

    1. Get data from hh.ru by user request (i.e. 'Machine learning')
    2. Collect all vacancies or resumes based on mode.
    3. Parse JSON and get useful values: salary, experience, name,
    skills, employer name etc.
    4. Calculate some statistics: average salary, median, std, variance.

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

import os
from pathlib import Path
from typing import Optional
import argparse
import requests

from src.analyzer import Analyzer
from src.currency_exchange import Exchanger
from src.data_collector import DataCollector
from src.resume_collector import ResumeCollector
from src.parser import Settings
from src.predictor import Predictor

# Ensure cache directory exists
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

SETTINGS_PATH = "settings.json"

def get_professional_roles():
    """Get professional roles from HH.ru API"""
    try:
        response = requests.get('https://api.hh.ru/professional_roles')
        response.raise_for_status()
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
        print(f"Error fetching professional roles: {str(e)}")
        return None

def hh_analyzer():
    """Main function for HH.ru vacancies and resumes researcher"""
    settings = Settings("settings.json")
    
    # If list_roles flag is set, show roles and exit
    if settings.list_roles:
        print("\nFetching professional roles from HH.ru API...")
        get_professional_roles()
        return

    print("[INFO]: Get exchange rates:", settings.rates)
    
    if settings.parse_resumes:
        print("[INFO]: Starting resume collection...")
        collector = ResumeCollector()
        collector.refresh = settings.refresh
        
        # Convert area to int if it's a list
        area = settings.options.get('area', 1)
        if isinstance(area, list):
            area = area[0]  # Take first area if multiple provided
            
        print(f"[INFO]: Collecting resumes for area {area}...")
        resumes = collector.collect_resumes(
            text=settings.options.get('text', ''),
            area=area,
            professional_roles=settings.options.get('professional_roles'),
            refresh=settings.refresh
        )
        
        print(f"\n[INFO]: Found {len(resumes)} resumes")
        if resumes:
            print("\nSample resume data:")
            print("=" * 50)
            for i, resume in enumerate(resumes[:3], 1):  # Show first 3 resumes
                print(f"\nResume {i}:")
                print(f"Title: {resume.get('title', 'N/A')}")
                print(f"Name: {resume.get('first_name', 'N/A')} {resume.get('last_name', 'N/A')}")
                print(f"Age: {resume.get('age', 'N/A')}")
                print(f"Experience: {resume.get('total_experience', {}).get('months', 'N/A')} months")
                print(f"Skills: {', '.join(resume.get('skills', ['N/A']))}")
                print("-" * 50)
            
            if settings.save_result:
                import pandas as pd
                df = pd.DataFrame(resumes)
                output_file = "resume_results.csv"
                df.to_csv(output_file, index=False)
                print(f"\n[INFO]: Saved {len(resumes)} resumes to {output_file}")
    else:
        print("[INFO]: Starting vacancy collection...")
        collector = DataCollector(settings.rates)
        analyzer = Analyzer(settings.save_result)
        print("[INFO]: Collect data from JSON. Create list of vacancies...")
        vacancies = collector.collect_vacancies(
            query=settings.options, refresh=settings.refresh, num_workers=settings.num_workers
        )
        df = analyzer.prepare_df(vacancies)
        analyzer.analyze_df(df)
    
    print("[INFO]: Done! Exit()")

if __name__ == "__main__":
    hh_analyzer() 