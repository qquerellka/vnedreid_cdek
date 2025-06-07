"""Get currency exchange for RUB, EUR, USD from remore server

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
import json
from typing import Dict, Optional

import requests


class Exchanger:
    """Get currency exchange rates from remote server."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._rates = None
        self._update_rates()

    def _update_rates(self):
        """Update exchange rates from remote server."""
        try:
            response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
            if response.status_code == 200:
                data = response.json()
                self._rates = {
                    "RUR": 1.0,
                    "USD": 1.0 / float(data["Valute"]["USD"]["Value"]),
                    "EUR": 1.0 / float(data["Valute"]["EUR"]["Value"])
                }
            else:
                print(f"[WARNING]: Failed to get exchange rates. Status code: {response.status_code}")
                self._rates = {"RUR": 1.0, "USD": None, "EUR": None}
        except Exception as e:
            print(f"[WARNING]: Failed to get exchange rates: {str(e)}")
            self._rates = {"RUR": 1.0, "USD": None, "EUR": None}

    def update_exchange_rates(self, rates: Dict[str, Optional[float]]) -> Dict[str, float]:
        """Update exchange rates in the given dictionary.

        Parameters
        ----------
        rates : Dict[str, Optional[float]]
            Dictionary of currency rates to update

        Returns
        -------
        Dict[str, float]
            Updated dictionary with exchange rates
        """
        if self._rates is None:
            self._update_rates()
        
        # Update only None values
        for currency, rate in self._rates.items():
            if currency in rates and rates[currency] is None:
                rates[currency] = rate
        
        return rates

    def save_rates(self, rates: Dict[str, Optional[float]]):
        """Save exchange rates to config file.

        Parameters
        ----------
        rates : Dict[str, Optional[float]]
            Dictionary of currency rates to save
        """
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            
            config["rates"] = rates
            
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"[WARNING]: Failed to save exchange rates: {str(e)}")


if __name__ == "__main__":
    _exchanger = Exchanger("../settings.json")
    _default = {"RUB": None, "USD": None, "EUR": None, "UAH": None}
    _exchanger.update_exchange_rates(_default)
    _exchanger.save_rates(_default)
    for _k, _v in _default.items():
        print(f"{_k}: {_v :.05f}")
