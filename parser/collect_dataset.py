#!/usr/bin/env python3
"""
Dataset Collection Script for ML Engineering

This script collects multiple datasets of IT vacancies and combines them
into a single, clean dataset suitable for ML training.
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import subprocess
import time

class DatasetCollector:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "datasets"
        self.data_dir.mkdir(exist_ok=True)
        
        # Load settings
        with open(self.base_dir / "settings.json", "r") as f:
            self.settings = json.load(f)
    
    def collect_batch(self, batch_name):
        """Collect one batch of data"""
        print(f"\nCollecting batch: {batch_name}")
        
        # Run the parser
        cmd = [
            "python3", 
            str(self.base_dir / "researcher.py"),
            "--refresh",
            f"--num_workers={self.settings['num_workers']}"
        ]
        
        subprocess.run(cmd, check=True)
        
        # Move and rename the output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if (self.base_dir / "hh_results.csv").exists():
            new_name = f"batch_{batch_name}_{timestamp}.csv"
            os.rename(
                self.base_dir / "hh_results.csv",
                self.data_dir / new_name
            )
            print(f"Saved batch to: {new_name}")
            return new_name
        return None

    def clean_dataset(self, input_files):
        """Clean and combine datasets"""
        print("\nCleaning and combining datasets...")
        
        # Read all CSV files
        dfs = []
        for file in input_files:
            df = pd.read_csv(self.data_dir / file)
            dfs.append(df)
        
        # Combine all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates
        combined_df = combined_df.drop_duplicates(subset=['Ids'])
        
        # Clean the data
        # 1. Remove rows with empty critical fields
        critical_fields = ['Name', 'Description', 'Keys', 'Experience']
        combined_df = combined_df.dropna(subset=critical_fields)
        
        # 2. Clean salary data
        # Remove rows where both From and To are empty
        combined_df = combined_df[
            ~(combined_df['From'].isna() & combined_df['To'].isna())
        ]
        
        # 3. Clean text fields
        for field in ['Name', 'Description', 'Keys']:
            if field in combined_df.columns:
                combined_df[field] = combined_df[field].astype(str).str.strip()
                # Remove rows with empty strings
                combined_df = combined_df[combined_df[field] != '']
        
        # Save the cleaned dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_dir / f"ml_dataset_{timestamp}.csv"
        combined_df.to_csv(output_file, index=False)
        
        # Print dataset statistics
        print("\nDataset Statistics:")
        print(f"Total vacancies: {len(combined_df)}")
        print(f"Unique companies: {combined_df['Employer'].nunique()}")
        print(f"Roles distribution:\n{combined_df['Name'].value_counts().head()}")
        print(f"\nSaved cleaned dataset to: {output_file}")
        
        return output_file

def main():
    collector = DatasetCollector()
    
    # Collect multiple batches
    print("Starting dataset collection...")
    batch_files = []
    
    # Collect 3 batches with delays to avoid API rate limits
    for i in range(3):
        batch_name = f"batch_{i+1}"
        if file := collector.collect_batch(batch_name):
            batch_files.append(file)
        if i < 2:  # Don't sleep after the last batch
            print("Waiting 5 minutes before next batch...")
            time.sleep(300)  # 5 minutes delay
    
    if batch_files:
        # Clean and combine the datasets
        collector.clean_dataset(batch_files)
    else:
        print("No data was collected!")

if __name__ == "__main__":
    main() 