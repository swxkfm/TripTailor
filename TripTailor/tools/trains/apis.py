import pandas as pd
import os
from math import ceil

import pandas as pd
import os

class Trains:
    def __init__(self, relative_path="../../database_EN/Train_Schedule.csv"):
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

    def run(self, origin: str, destination: str, departure_date: str):
        if self.data is None:
            print("Error: Data is not loaded.")
            return None
        
        # Filter rows where Station_Name contains origin or destination
        filtered_data = self.data[
            self.data['Station_Name'].str.contains(origin, case=False, na=False) | 
            self.data['Station_Name'].str.contains(destination, case=False, na=False)
        ]
        filtered_data = filtered_data.groupby('Train_Number').filter(lambda x: len(x) >= 2)

        # Ensure that only rows with the same Train_Number are considered
        results = []
        train_numbers = filtered_data['Train_Number'].unique()
        
        for train in train_numbers:
            train_data = filtered_data[filtered_data['Train_Number'] == train]
            
             # 查找出发站和到达站
            origin_data = train_data[train_data['Station_Name'].str.contains(origin, case=False, na=False)]
            destination_data = train_data[train_data['Station_Name'].str.contains(destination, case=False, na=False)]
            
            # 如果任一为空，跳过该列车
            if origin_data.empty or destination_data.empty:
                continue
            
            # 获取第一行的出发站和到达站
            origin_row = origin_data.iloc[0]
            destination_row = destination_data.iloc[0]
            
            # Ensure Station_Number condition
            if origin_row['Station_Number'] < destination_row['Station_Number']:
                second_class_price = destination_row['Second_Class_Price'] - origin_row['Second_Class_Price']
                first_class_price = destination_row['First_Class_Price'] - origin_row['First_Class_Price']
                
                results.append({
                    'Train_Number': train,
                    'Origin_Station': origin_row['Station_Name'],
                    'Destination_Station': destination_row['Station_Name'],
                    'Departure_Time': origin_row['Departure_Time'],
                    'Arrival_Time': destination_row['Arrival_Time'],
                    'Origin_Latitude':origin_row['Latitude'],
                    'Origin_Longitude':origin_row['Longitude'],
                    'Destination_Latitude':destination_row['Latitude'],
                    'Destination_Longitude':destination_row['Longitude'],
                    'Second_Class_Price': second_class_price,
                    'First_Class_Price': first_class_price
                })
        
        # Convert results to DataFrame
        result_df = pd.DataFrame(results)
        return result_df

# Usage example
if __name__ == "__main__":
    trains = Trains()
    result = trains.run(origin="beijing", destination="zhuhai", departure_date="2024-11-24")
    print(result)
