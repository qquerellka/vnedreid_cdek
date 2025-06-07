"""Head Hunter Researcher

Description   :
    HeadHunter (hh.ru) main research script.

    1. Get data from hh.ru by user request (i.e. 'Machine learning')
    2. Collect all vacancies.
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

from src.analyzer import Analyzer
from src.currency_exchange import Exchanger
from src.data_collector import DataCollector
from src.parser import Settings
from src.predictor import Predictor

# Ensure cache directory exists
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

SETTINGS_PATH = "settings.json"


class ResearcherHH:
    """Main class for searching vacancies and analyze them."""

    def __init__(self, config_path: str = SETTINGS_PATH, no_parse: bool = False):
        self.settings = Settings(config_path, no_parse=no_parse)
        self.exchanger = Exchanger(config_path)
        self.collector: Optional[DataCollector] = None
        self.analyzer: Optional[Analyzer] = None
        self.predictor = Predictor()

    def update(self, **kwargs):
        self.settings.update_params(**kwargs)
        if not any(self.settings.rates.values()) or self.settings.update:
            print("[INFO]: Trying to get exchange rates from remote server...")
            self.exchanger.update_exchange_rates(self.settings.rates)
            self.exchanger.save_rates(self.settings.rates)

        print(f"[INFO]: Get exchange rates: {self.settings.rates}")
        self.collector = DataCollector(self.settings.rates)
        self.analyzer = Analyzer(self.settings.save_result)

    def __call__(self):
        print("[INFO]: Collect data from JSON. Create list of vacancies...")
        vacancies = self.collector.collect_vacancies(
            query=self.settings.options, refresh=self.settings.refresh, num_workers=self.settings.num_workers
        )
        print("[INFO]: Prepare dataframe...")
        df = self.analyzer.prepare_df(vacancies)
        print("\n[INFO]: Analyze dataframe...")
        self.analyzer.analyze_df(df)
        print("\n[INFO]: Predict None salaries...")
        # total_df = self.predictor.predict(df)
        # self.predictor.plot_results(total_df)
        print("[INFO]: Done! Exit()")


def hh_analyzer():
    """Main function for HH.ru vacancies researcher"""
    settings = Settings("settings.json")
    collector = DataCollector(settings.rates)
    
    # If list_roles flag is set, show roles and exit
    if settings.options.get('list_roles'):
        print("\nFetching professional roles from HH.ru API...")
        roles = collector.get_professional_roles()
        if roles:
            print("\nAvailable Professional Roles:")
            print("=" * 50)
            for category in roles['categories']:
                print(f"\n{category['name'].upper()}:")
                print("-" * 50)
                for role in category['roles']:
                    print(f"ID: {role['id']:<4} | {role['name']}")
        return

    analyzer = Analyzer(settings.save_result)
    print("[INFO]: Get exchange rates:", settings.rates)
    print("[INFO]: Collect data from JSON. Create list of vacancies...")
    vacancies = collector.collect_vacancies(
        query=settings.options, refresh=settings.refresh, num_workers=settings.num_workers
    )
    df = analyzer.prepare_df(vacancies)
    analyzer.analyze_df(df)
    print("[INFO]: Done! Exit()")


if __name__ == "__main__":
    hh_analyzer()
