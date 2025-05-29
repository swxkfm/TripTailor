import os
import pandas as pd
from math import ceil

class Flights:
    def __init__(self, relative_path="../../database_EN/Flight_Schedule.csv"):
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

    def calculate_estimated_arrival(self, arrival_time, delay_minutes):
        """
        Calculate the estimated arrival time based on the given arrival time and delay minutes.

        Args:
        - arrival_time (str): The actual arrival time in the format "HH:MM".
        - delay_minutes (int): The number of minutes the flight is delayed.

        Return:
        - str: The estimated arrival time in the format "HH:MM".

        Example:
        >>> flights = Flights()
        >>> flights.calculate_estimated_arrival("12:30", 30)
        '13:00'
        """
        # Convert arrival time to minutes
        hours, minutes = map(int, arrival_time.split(":"))
        total_minutes = hours * 60 + minutes + delay_minutes

        # Round to the nearest 10 minutes
        rounded_minutes = ceil(total_minutes / 10) * 10

        # Convert back to HH:MM format
        estimated_hours = (rounded_minutes // 60) % 24
        estimated_minutes = rounded_minutes % 60

        return f"{estimated_hours:02}:{estimated_minutes:02}"

   
    def run(self, origin: str, destination: str, departure_date: str):
        """
        According to the departure place, destination and departure date, filter the flights and return a DataFrame containing the flight information that meets the criteria.

        Args:
        - origin (str): Departure city.
        - destination (str): Destination city.
        - departure_date (str): Departure date.

        Return:
        - DataFrame: A DataFrame containing flight information that meets the criteria.

        Exceptions:
        - ValueError: If the database is not loaded, throw this exception.
        """
        # If the data is not loaded, throw an exception
        if self.data is None:
            raise ValueError("Database not loaded. Call load_db() first.")

        # Filter flights based on criteria
        filtered_flights = self.data[
            (self.data['Departure City'].str.lower() == origin.lower()) &
            (self.data['Arrival City'].str.lower() == destination.lower()) &
            (self.data[departure_date] == 1)
        ]

        # If there are no flights that meet the criteria, return an empty DataFrame
        if filtered_flights.empty:
            return filtered_flights

        filtered_flights = filtered_flights.copy()
        # Calculate the estimated arrival time and add it to the DataFrame
        filtered_flights['Estimated Arrival Time'] = filtered_flights.apply(
            lambda row: self.calculate_estimated_arrival(
                row['Arrival Time'], row['Average Delay (minutes)']
            ), axis=1
        )

        # Select the required columns
        result_columns = [
            'Flight Number', 'Airline', 'Departure Time', 'Arrival Time',
            'Price', 'On-Time Performance', 'Average Delay (minutes)',
            'Estimated Arrival Time', 'Departure Airport', 'Arrival Airport',
            'Arrival Airport Latitude', 'Arrival Airport Longitude', 'Departure City', 'Arrival City'
        ]
        result = filtered_flights[result_columns]

        # Return the final DataFrame
        return result


# Usage example
if __name__ == "__main__":
    flights = Flights()
    flights.load_db()
    result = flights.run(origin="shanghai", destination="harbin", departure_date="Monday")
    print(result)

