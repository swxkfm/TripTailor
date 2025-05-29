import os
import pandas as pd
from pandas import DataFrame
from geopy.distance import geodesic

class Attractions:
    def __init__(self, relative_path="../../database_EN/attractions.csv"):
        # Get the absolute path of the current file
        current_file_path = os.path.abspath(__file__)
        # Get the directory of the current file
        current_directory = os.path.dirname(current_file_path)
        # Construct the full path of the file
        self.path = os.path.join(current_directory, relative_path)
        
        # Attempt to read the CSV file
        try:
            self.data = pd.read_csv(self.path, low_memory=False)
        except FileNotFoundError:
            print(f"Error: The file {self.path} was not found.")
            self.data = None
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            self.data = None

    def load_db(self):
        self.data = pd.read_csv(self.path, low_memory=False)

    def run(self, city: str):
        """Search for Accommodations by city (case-insensitive) and shuffle results."""
        # Ensure case-insensitive comparison by converting both to lowercase
        results = self.data[self.data["city"].str.lower() == city.lower()]
        # Shuffle the results
        shuffled_results = results.sample(frac=1).reset_index(drop=True)
        return shuffled_results

 