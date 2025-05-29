import importlib
import json
import os
import random
import re
import sys
import pandas as pd
from tqdm import tqdm
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ChatClient import ChatClient
from utils.func import extract_demands_info,extract_transportation_info,format_transport_options,format_poi_information, is_time_greater, df_to_dict, format_given_information
from utils.func import extract_poi_id,extract_poi_lists,format_poi_plan,format_restaurant_information,format_hotel_information
from agents.Prompt import demand_extraction_prompt,major_otd_transport_prompt,major_dto_transport_prompt,attraction_rank_prompt
from agents.Prompt import daily_schedule_prompt,daily_schedule_extract_prompt,restaurant_select_prompt,hotel_select_prompt,planner_agent_prompt
from agents.UserDemands import DemandsInfo
from geopy.distance import geodesic
from agents.Prompt import frist_day_prompt, last_day_prompt, day_prompt

class TravelAgent:
    def __init__(self, user_query,tools=["flights","trains","attractions","accommodations","restaurants"],model_name="", api_key='', base_url=''):
        self.user_query = user_query
        self.chat_client = ChatClient(model_name=model_name, api_key=api_key, base_url=base_url)
        self.demands_info = DemandsInfo()
        self.tools = self.load_tools(tools=tools)
        
        self.transport_options_otd = {}
        self.transport_options_dto = {}
        self.major_transport = {}

        self.attractions = []
        self.attractions_options = []
        self.attractions_selected = []
        self.given_attractions = []
        self.daily_schedule = []
        self.plan = []
        self.final_plan = []

        self.restaurants = None
        self.hotels = []
        self.hotel = []
        self.hotel_ids = []
        self.local_transport = []

    def extract_demands(self):
        demand = demand_extraction_prompt.format(user_profile = self.user_profile,user_query = self.user_query)
        response = self.chat_client.chat_completion(user_message=demand, temperature=0.3)
        self.demands_info = extract_demands_info(response=response)

    def determine_major_transport(self):
        self.fetch_and_select_transport_options(
            origin=self.demands_info.departure_city,
            destination=self.demands_info.destination_city,
            departure_date=self.demands_info.departure_day,
            direction="origin_to_destination",
            departure_time=self.demands_info.departure_time,
        )

        self.fetch_and_select_transport_options(
            origin=self.demands_info.destination_city,
            destination=self.demands_info.departure_city,
            departure_date=self.demands_info.return_day,
            direction="destination_to_origin",
            departure_time=self.demands_info.return_time,
        )

    def fetch_and_select_transport_options(self, origin, destination, departure_date, direction, departure_time, given_info):
        flights = self.tools["flights"].run(origin=origin, destination=destination, departure_date=departure_date)
        trains = self.tools["trains"].run(origin=origin, destination=destination, departure_date=departure_date)
        if direction == "origin_to_destination":
            if departure_time == 'early morning':
                time = '4:00-9:00'
            elif departure_time == 'late morning':
                time = '9:00-12:00'
            elif departure_time == 'afternoon':
                time = '12:00-18:00'
            elif departure_time == 'evening':
                time = '18:00-23:59'
            elif departure_time == 'morning':
                time = '4:00-12:00'

            if not flights.empty:
                flight_options = flights[flights['Departure Time'].apply(lambda x: is_time_greater(time.split('-')[1], x))]
                if not flight_options.empty:
                    flight_options = flight_options[flight_options['Departure Time'].apply(lambda x: is_time_greater(x, time.split('-')[0]))]
            else:
                flight_options = pd.DataFrame()
            if not trains.empty:
                train_options = trains[trains['Departure_Time'].apply(lambda x: is_time_greater(time.split('-')[1], x))]
                if not train_options.empty:
                    train_options = train_options[train_options['Departure_Time'].apply(lambda x: is_time_greater(x, time.split('-')[0]))]
            else:
                train_options = pd.DataFrame()

            transport_options = {
                "flights": flight_options if not flight_options.empty else flights,
                "trains": train_options if not train_options.empty else trains
            }

            self.transport_options_otd = transport_options
            results = format_transport_options(transport_options,reverse=False)
            transportation = major_otd_transport_prompt.format(user_query=self.user_query, transport_options="\n".join(results))   
        else:
            if departure_time == 'early morning':
                time = '4:00-9:00'
            elif departure_time == 'late morning':
                time = '9:00-12:00'
            elif departure_time == 'afternoon':
                time = '12:00-18:00'
            elif departure_time == 'evening':
                time = '18:00-23:59'
            elif departure_time == 'morning':
                time = '4:00-12:00'

            if not flights.empty:
                flight_options = flights[flights['Departure Time'].apply(lambda x: is_time_greater(time.split('-')[1], x))]
                if not flight_options.empty:
                    flight_options = flight_options[flight_options['Departure Time'].apply(lambda x: is_time_greater(x, time.split('-')[0]))]
            else:
                flight_options = pd.DataFrame()
            if not trains.empty:
                train_options = trains[trains['Departure_Time'].apply(lambda x: is_time_greater(time.split('-')[1], x))]
                if not train_options.empty:
                    train_options = train_options[train_options['Departure_Time'].apply(lambda x: is_time_greater(x, time.split('-')[0]))]
            else:
                train_options = pd.DataFrame()

            transport_options = {
                "flights": flight_options if not flight_options.empty else flights,
                "trains": train_options if not train_options.empty else trains
            }

            self.transport_options_dto = transport_options
            results = format_transport_options(transport_options,reverse=False)
            transportation = major_dto_transport_prompt.format(user_query=self.user_query, transport_options="\n".join(results))

        # Chat client interaction
        response = self.chat_client.chat_completion(user_message=transportation, temperature=0.5)
        
        # Extract transport info
        transport_type, transport_number = extract_transportation_info(response=response)

        # If transport_type is "none", assign the first non-empty transport_number from the available options
        if not transport_type:
            if transport_options["flights"].shape[0] > 0:  # Check if flights are available
                transport_type = "Flight"
                transport_number = transport_options["flights"].iloc[0]["Flight Number"]
            elif transport_options["trains"].shape[0] > 0:  # Check if trains are available
                transport_type = "Train"
                transport_number = transport_options["trains"].iloc[0]["Train_Number"]

        # Assign selected transport based on response
        if transport_type == "Flight":
            self.major_transport[direction] = transport_options["flights"][transport_options["flights"]["Flight Number"] == transport_number]
        elif transport_type == "Train":
            self.major_transport[direction] = transport_options["trains"][transport_options["trains"]["Train_Number"] == transport_number]
            
 
    def select_attractions(self, given_info):
        # self.attractions = self.tools["attractions"].run(city=self.demands_info.destination_city)
        self.attractions = pd.DataFrame(given_info['attractions'])
        
        self.attractions = self.attractions.drop(columns=['poiId'], errors='ignore')  
        self.attractions['poiId'] = range(1, len(self.attractions) + 1)  
                 
        batch_size = 10 
        for start_index in range(0, len(self.attractions), batch_size):
            end_index = start_index + batch_size
            batch_attractions = format_poi_information(self.attractions, start_index=start_index, end_index=end_index)
            attraction_rank = attraction_rank_prompt.format(user_query=self.user_query, attractions="\n".join(batch_attractions))
            response = self.chat_client.chat_completion(user_message=attraction_rank, temperature=0.6)
            # print(response)
            poi_id = extract_poi_id(response)
            if poi_id: 
                self.attractions_selected.append(poi_id)

        num_rows = len(self.attractions_selected)
        select_count_per_row = int(self.demands_info.duration * 3 / num_rows) + 1

        selected_ids = [id_ for row in self.attractions_selected for id_ in row[:select_count_per_row]]

        self.selected_ids = selected_ids

        if len(selected_ids) == 0:
            print(selected_ids[0])

        selected_pois = self.attractions[self.attractions["poiId"].isin(selected_ids)]
        self.attractions_options = given_info['attractions']
        results = []

        for _, row in selected_pois.iterrows():
            features = row['shortFeatures'] if row['shortFeatures'] else "No Features"
            tags = row['tagNameList'] if row['tagNameList'] else "No Tags"
            reference_time = row['reference_time'] if pd.notnull(row['reference_time']) else "1-3 hours"

            poi_info = (
                f"POI ID: {row['poiId']}, "
                f"Name: {row['poiName']}, "
                f"Recommended Duration: {reference_time}, "
                f"Tags: {tags}, "
                f"Features: {features}"
            )
            results.append(poi_info)

        if 'Flight Number' in self.major_transport["origin_to_destination"].columns:
            arrival_time = self.major_transport["origin_to_destination"]["Estimated Arrival Time"].iloc[0]
        else:
            arrival_time = self.major_transport["origin_to_destination"]["Arrival_Time"].iloc[0]
        if 'Flight Number' in self.major_transport["destination_to_origin"].columns:
            departure_time = self.major_transport["destination_to_origin"]["Departure Time"].iloc[0]
        else:
            departure_time = self.major_transport["destination_to_origin"]["Departure_Time"].iloc[0]

        for i in range(10):

            daily_schedule = daily_schedule_prompt.format(user_query=self.user_query,arrival_time=arrival_time,departure_time=departure_time,attractions="\n".join(results))
            response1 = self.chat_client.chat_completion(user_message=daily_schedule, temperature=0.5)
            daily_schedule_extract = daily_schedule_extract_prompt.format(attractions="\n".join(results),schedule=response1)

            response2 = self.chat_client.chat_completion(user_message=daily_schedule_extract, temperature=0)
            self.daily_schedule = extract_poi_lists(input_text=response2)

            if self.detect_errors():
                break
            else:
                self.fix_plan()
                if self.detect_errors():
                    break
        if not self.detect_errors():
            self.fix_plan_attraction()

    def generate_overall_plan(self):
        latitude_list = []
        longitude_list = []   
        for day_schedule in self.daily_schedule:
            day_plan = [] 
            for i in range(len(day_schedule)):
                poiId = day_schedule[i]
                if poiId != 1000:
                    formatted_poi, latitude, longitude = format_poi_plan(self.attractions, poiId)
                    latitude_list.append(latitude)
                    longitude_list.append(longitude)
                    day_plan.append(formatted_poi)
                elif poiId == 1000:  
                    try:
                        longitude = self.attractions.loc[self.attractions["poiId"] == day_schedule[i-1], 'longitude'].iloc[0]
                        latitude = self.attractions.loc[self.attractions["poiId"] == day_schedule[i-1], 'latitude'].iloc[0]
                    except:
                        try:
                            longitude = self.attractions.loc[self.attractions["poiId"] == day_schedule[i+1], 'longitude'].iloc[0]
                            latitude = self.attractions.loc[self.attractions["poiId"] == day_schedule[i+1], 'latitude'].iloc[0]
                        except:
                            poiIds = [item for item in day_schedule if item != 1000]
                            longitude = self.attractions.loc[self.attractions["poiId"] == poiIds[-1], 'longitude'].iloc[0]
                            latitude = self.attractions.loc[self.attractions["poiId"] == poiIds[-1], 'latitude'].iloc[0]
                    restaurant, restaurant_data = self.select_restaurant(longitude=longitude, latitude=latitude)
                    if self.restaurants is None:
                        self.restaurants = restaurant_data
                    else:
                        self.restaurants = pd.concat([self.restaurants, restaurant_data], axis=0)
                    day_plan.append(restaurant)
            self.plan.append(day_plan)
        
        latitude = sum(latitude_list) / len(latitude_list)
        longitude = sum(longitude_list) / len(longitude_list)

        self.hotel = self.select_hotels(latitude, longitude)
        self.plan[0].insert(0, self.hotel)
        otd_transport = self.major_transport["origin_to_destination"]
        dto_transport = self.major_transport["destination_to_origin"]
        if 'Flight Number' in otd_transport.columns:
            flight_info = (
                f"Departure city: {self.demands_info.departure_city}, Arrival city: {self.demands_info.destination_city},"
                f"Flight Number: {otd_transport['Flight Number'].iloc[0]}, "
                f"Airline: {otd_transport['Airline'].iloc[0]}, "
                f"Price: ¥{int(otd_transport['Price'].iloc[0])}, "
                f"Departure Time: {otd_transport['Departure Time'].iloc[0]}, "
                f"Estimated Arrival Time: {otd_transport['Estimated Arrival Time'].iloc[0]}"
            )
        else:
            flight_info = (
                f"Departure city: {self.demands_info.departure_city}, Arrival city: {self.demands_info.destination_city},"
                f"Train Number: {otd_transport['Train_Number'].iloc[0]}, "
                f"Price: ¥{int(otd_transport['Second_Class_Price'].iloc[0])}, "
                f"Departure Time: {otd_transport['Departure_Time'].iloc[0]}, "
                f"Arrival Time: {otd_transport['Arrival_Time'].iloc[0]}"
            )
        self.plan[0].insert(0, flight_info)

        if 'Flight Number' in dto_transport.columns:
            flight_info = (
                f"Departure city: {self.demands_info.destination_city}, Arrival city: {self.demands_info.departure_city},"
                f"Flight Number: {dto_transport['Flight Number'].iloc[0]}, "
                f"Airline: {dto_transport['Airline'].iloc[0]}, "
                f"Price: ¥{int(dto_transport['Price'].iloc[0])}, "
                f"Departure Time: {dto_transport['Departure Time'].iloc[0]}, "
                f"Estimated Arrival Time: {dto_transport['Estimated Arrival Time'].iloc[0]}"
            )
        else:
            flight_info = (
                f"Departure city: {self.demands_info.destination_city}, Arrival city: {self.demands_info.departure_city},"
                f"Train Number: {dto_transport['Train_Number'].iloc[0]}, "
                f"Price: ¥{int(dto_transport['Second_Class_Price'].iloc[0])}, "
                f"Departure Time: {dto_transport['Departure_Time'].iloc[0]}, "
                f"Arrival Time: {dto_transport['Arrival_Time'].iloc[0]}"
            )

        self.plan[-1].append(flight_info)

    def generate_final_plan(self):
        for i, day_plan in enumerate(self.plan, 1):  # Using enumerate to track the day number
            day_plan_str = "\n\n".join(day_plan)
            if i == len(self.plan):  # Check if it's the last day
                day_plan_with_day = f"This is the last day of the trip\n\n{day_plan_str}"
            else:
                day_plan_with_day = f"This is day {i} of the trip\n\n{day_plan_str}"
            if i == 1:
                day_plan = frist_day_prompt.format(activities=day_plan_with_day)
            elif i == len(self.plan):
                day_plan = last_day_prompt.format(city1=self.demands_info.departure_city, city2=self.demands_info.departure_city, activities=day_plan_with_day)
            else:
                day_plan = day_prompt.format(activities=day_plan_with_day)

            response = self.chat_client.chat_completion(user_message=day_plan, temperature=0.7)
            self.final_plan.append(f'**Day {i} Itinerary**\n\n{response}')
        
        given_data = {
            'hotel': df_to_dict(self.hotels),
            'transport_otd': {
                'flight_options': df_to_dict(self.transport_options_otd['flights']),
                'train_options': df_to_dict(self.transport_options_otd['trains'])
            },
            'transport_dto': {
                'flight_options': df_to_dict(self.transport_options_dto['flights']),
                'train_options': df_to_dict(self.transport_options_dto['trains'])
            },
            'attractions': self.attractions_options,
            'restaurants': df_to_dict(self.restaurants)
        }
        return given_data

    def detect_errors(self):
        plan = self.daily_schedule
        expected_days = self.demands_info.duration
        actual_days = len(plan)
        
        # Check if the number of days matches
        if actual_days != expected_days:
            return False
        
        all_attractions = []
        for day in plan:
            attractions = [item for item in day if item != 1000]
            all_attractions.extend(attractions)
        if 0 in all_attractions:
            return False
        
        duplicate_attractions = set([x for x in all_attractions if all_attractions.count(x) > 1])
        if duplicate_attractions:
            return False
        
        # Check each day's meal count and duplicate attractions
        for idx, day in enumerate(plan, 1):
            meal_count = day.count(1000)
            attractions = [attraction for attraction in day if attraction != 1000]
        
            # Check meal count
            if meal_count > 2:
                return False
        
            # Check if there is at least one attraction
            if len(attractions) == 0:
                return False
    
        return True

    def fix_plan(self):
        plan = self.daily_schedule
        fixed_plan = []
        used_attractions = set()  # Keep track of attractions already used
        
        for i, day in enumerate(plan, 1):
            meal_count = 0
            fixed_day = []
            seen_attractions = set()
            
            for item in day:
                if item == 1000:
                    meal_count += 1
                    if meal_count <= 2:  # Keep only the first two meals
                        fixed_day.append(1000)
                else:
                    # Only add attractions that have not been used globally
                    if item not in used_attractions and item not in seen_attractions:
                        fixed_day.append(item)
                        seen_attractions.add(item)
                        used_attractions.add(item)
            
            if i == 1 or i == self.demands_info.duration:
                pass
            else:
                # Ensure exactly two meals
                while meal_count < 2:
                    fixed_day.append(1000)
                    meal_count += 1
            
            fixed_plan.append(fixed_day)
        self.daily_schedule = fixed_plan
    
    def fix_plan_attraction(self):
        plan = self.daily_schedule
        fixed_plan = []
        used_attractions = set()  # Keep track of attractions already used
        
        for i, day in enumerate(plan, 1):
            meal_count = 0
            fixed_day = []
            seen_attractions = set()
            
            for item in day:
                if item == 1000:
                    meal_count += 1
                    if meal_count <= 2:  # Keep only the first two meals
                        fixed_day.append(1000)
                elif item == 0:
                    pass
                else:
                    # Only add attractions that have not been used globally
                    if item not in used_attractions and item not in seen_attractions:
                        fixed_day.append(item)
                        seen_attractions.add(item)
                        used_attractions.add(item)
            
            if i == 1 or i == self.demands_info.duration:
                pass
            else:
                # Ensure exactly two meals
                while meal_count < 2:
                    fixed_day.append(1000)
                    meal_count += 1
            
            fixed_plan.append(fixed_day)
        self.daily_schedule = fixed_plan

        for i, day in enumerate(self.daily_schedule, 1):
            attraction_num = len([item for item in day if item != 1000])
            if attraction_num == 0 and day != []:
                selected_attraction_id = random.sample(set(self.selected_ids).difference(used_attractions), 1)
                day.insert(0, selected_attraction_id[0])
                used_attractions.add(selected_attraction_id[0])


    def select_restaurant(self, longitude, latitude):

        restaurants = self.tools["restaurants"].run(city=self.demands_info.destination_city,meal_cost_range=self.demands_info.meal_cost_range, longitude=longitude,latitude=latitude)
        name_selected = list(self.restaurants['name']) if self.restaurants is not None else []
        restaurants = restaurants[~restaurants['name'].isin(name_selected)]
        restaurants["id"] = range(1, len(restaurants) + 1)
        results = format_restaurant_information(restaurants)
        message = restaurant_select_prompt.format(user_query=self.user_query,restaurants="\n".join(results))
        response = self.chat_client.chat_completion(user_message=message, temperature=0.5)
        match = re.search(r"Restaurant\[(\d+)\]", response)
        if match:
            restaurant_id = int(match.group(1)) 
            if 1 <= restaurant_id <= len(results):
                return results[restaurant_id - 1], restaurants[restaurants['id'] == restaurant_id] 
            else:
                return results[0], restaurants.head(1)
   
    def select_hotels(self, latitude, longitude):
        hotels = self.tools["accommodations"].run(city=self.demands_info.destination_city,hotel_cost=self.demands_info.hotel_cost, sample_num=0)
        hotels['distance'] = hotels.apply(
                lambda row: geodesic((latitude, longitude), (row['latitude'], row['longitude'])).kilometers,
                axis=1
            )
        within_dis = 5
        nearby_hotels = hotels[hotels['distance'] <= within_dis]
        while nearby_hotels.empty:
            within_dis += 5
            nearby_hotels = hotels[hotels['distance'] <= within_dis]
            
        sorted_hotels = nearby_hotels.sort_values(by='stars', ascending=False)
        sorted_hotels = sorted_hotels.head(8)
        self.hotels = sorted_hotels
        sorted_hotels["id"] = range(1, len(sorted_hotels) + 1)
        results = format_hotel_information(sorted_hotels)
        message = hotel_select_prompt.format(user_query=self.user_query,hotels="\n".join(results))
        response = self.chat_client.chat_completion(user_message=message, temperature=0.5)
        match = re.search(r"Hotel\[(\d+)\]", response)
        if match:
            hotel_id = int(match.group(1))  
            if 1 <= hotel_id <= len(results):
                return results[hotel_id - 1] 
            else:
                return results[0]

    def determine_local_transport(self):
        pass

    def load_tools(self,tools):
        tools_map = {}
        for tool_name in tools:
            module = importlib.import_module("tools.{}.apis".format(tool_name))
            tools_map[tool_name] = getattr(module, tool_name[0].upper()+tool_name[1:])()
        return tools_map
    
    def generate_plan_direct(self, given_information):
        message = planner_agent_prompt.format(text=given_information, query=self.user_query)
        response = self.chat_client.chat_completion(user_message=message)
        self.final_plan = response
    
    def presearch(self, given_info):
        given_attractions = given_info['attractions']
        given_poiids = [attraction['poiid'] for attraction in given_attractions]
        
        destination_city = self.demands_info.destination_city
        departure_city = self.demands_info.departure_city
        attractions = self.tools["attractions"].run(city=destination_city)

        attractions_in = attractions[attractions['poiId'].isin(given_poiids)]
        attractions_notin = attractions[~attractions['poiId'].isin(given_poiids)]
        max_attraction_num = self.demands_info.duration * 10
        if max_attraction_num < 50:
            max_attraction_num = 50
        if max_attraction_num - len(attractions_in) <= len(attractions_notin):
            if max_attraction_num - len(attractions_notin) <= 0:
                sample_num = 20
            else:
                sample_num = max_attraction_num - len(attractions_in)
            attractions_notin = attractions_notin.sample(sample_num)
        attractions = pd.concat([attractions_in, attractions_notin], ignore_index=True)
        attractions_data = df_to_dict(attractions)

        meal_cost_range = self.demands_info.meal_cost_range
        max_restaurant_num = self.demands_info.duration * 4
        restaurants = self.tools["restaurants"].data.dropna().copy()
        restaurants = restaurants[restaurants['real_city'].str.lower() == destination_city.lower()]
        restaurants = restaurants[
            (restaurants['avg_price'] >= meal_cost_range[0]) &
            (restaurants['avg_price'] <= meal_cost_range[1])
        ]
        if len(restaurants) > max_restaurant_num:
            restaurants = restaurants.sample(max_restaurant_num)

        restaurants_data = df_to_dict(restaurants)

        restaurants = self.tools["restaurants"].data.dropna().copy()
        restaurants = restaurants[restaurants['real_city'].str.lower() == destination_city.lower()]
        restaurants = restaurants[
            ~(
                (restaurants['avg_price'] >= meal_cost_range[0]) & 
                (restaurants['avg_price'] <= meal_cost_range[1])
            )
        ]
        if len(restaurants) > max_restaurant_num:
            restaurants = restaurants.sample(max_restaurant_num)

        restaurants_data_ = df_to_dict(restaurants)
        restaurants_data = restaurants_data + restaurants_data_

        hotels = self.tools["accommodations"].run(city=self.demands_info.destination_city,hotel_cost=self.demands_info.hotel_cost, sample_num=5)
        hotels_data = df_to_dict(hotels)
        
        hotels = self.tools["accommodations"].run_(city=self.demands_info.destination_city, sample_num=5)
        hotels_data_ = df_to_dict(hotels)
        hotels_data = hotels_data + hotels_data_
        
        transport_options = {}
        transport_options_otd = {}
        transport_options_otd["flights"] = self.tools["flights"].run(origin=departure_city, destination=destination_city, departure_date=self.demands_info.departure_day).sample(frac=1).reset_index(drop=True)
        transport_options_otd["trains"] = self.tools["trains"].run(origin=departure_city, destination=destination_city, departure_date=self.demands_info.departure_day).sample(frac=1).reset_index(drop=True)
        transport_options_dto = {}
        transport_options_dto["flights"] = self.tools["flights"].run(origin=destination_city, destination=departure_city, departure_date=self.demands_info.return_day).sample(frac=1).reset_index(drop=True)
        transport_options_dto["trains"] = self.tools["trains"].run(origin=destination_city, destination=departure_city, departure_date=self.demands_info.return_day).sample(frac=1).reset_index(drop=True)
        transport_options['otd'] = transport_options_otd
        transport_options['dto'] = transport_options_dto

        transport_data = {
            "transport_otd": {
                "flight_options": df_to_dict(transport_options_otd['flights']),
                "train_options": df_to_dict(transport_options_otd['trains'])
            },
            "transport_dto": {
                "flight_options": df_to_dict(transport_options_dto['flights']),
                "train_options": df_to_dict(transport_options_dto['trains'])
            }
        }

        given_data = {
            'hotels': hotels_data,
            'transport_otd': transport_data['transport_otd'],
            'transport_dto': transport_data['transport_dto'],
            'attractions': attractions_data,
            'restaurants': restaurants_data
        }

        return given_data

    def run(self, given_info=None):
        self.extract_demands()
        self.determine_major_transport()
        self.select_attractions(given_info)
        self.generate_overall_plan()
        given_data = self.generate_final_plan()
        return self.final_plan, given_data
    
    def run_direct(self, given_information):
        self.generate_plan_direct(given_information)
        return self.final_plan

    def run_presearch(self, given_info):
        self.extract_demands()
        presearch_info = self.presearch(given_info)
        return presearch_info, format_given_information(presearch_info)

    
 
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--input_file", type=str)
    parser.add_argument("--info_file", type=str)
    parser.add_argument("--output_path", type=str)
    parser.add_argument("--model_name", type=str)
    parser.add_argument("--mode", type=str, default='')
    parser.add_argument("--api_key", type=str)
    parser.add_argument('--base_url', type=str)


    args = parser.parse_args()

    model_name = args.model_name
    input_file = args.input_file
    info_file = args.info_file
    output_path = args.output_path
    mode = args.mode

    api_key = args.api_key
    base_url = args.base_url

    if not os.path.exists(output_path):
        os.os.makedirs(output_path)
    
    def process_and_save_incrementally(input_file, output_file):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            random.shuffle(data)

            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as out_f:
                    results = json.load(out_f)
            else:
                results = []
                
            with open(info_file, 'r', encoding='utf-8') as f:
                given_info_data = json.load(f)
            
            if os.path.exists(f'{output_path}/info_{model_name}_{mode}.json'):
                with open(f'{output_path}/info_{model_name}_{mode}.json', 'r', encoding='utf-8') as out_f:
                    results_data = json.load(out_f)
            else:
                results_data = {}

            processed_ids = {entry["pid"] for entry in results}
            if len(processed_ids) == len(data):
                exit()

            for entry in tqdm(data):
                try:
                    if entry["pid"] in processed_ids:
                        # print(f"Skipping already processed entry with id {entry['pid']}")
                        continue

                    user_query = entry.get("query", "")
                    if not user_query:
                        raise ValueError("Missing query")

                    travel_agent = TravelAgent(user_query=user_query, model_name=model_name, api_key=api_key, base_url=base_url)
                    try:
                        given_info = given_info_data[str(entry['pid'])]
                        final_plan, given_data = travel_agent.run(mode=mode, given_info=given_info)
                    except Exception as e:
                        print(f"Error during run() for entry with id {entry.get('pid')}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

                    entry[f"{model_name}_{mode}_plan"] = final_plan
                    results.append(entry)
                    results_data[entry['pid']] = given_data

                    with open(output_file, 'w', encoding='utf-8') as out_f:
                        json.dump(results, out_f, ensure_ascii=False, indent=4)
                    
                    with open(f'{output_path}/info_{model_name}_{mode}.json', 'w', encoding='utf-8') as out_f:
                        json.dump(results_data, out_f, ensure_ascii=False, indent=4)

                    print(f"Processed and saved entry with id {entry['pid']}")

                except Exception as e:
                    print(f"Error processing entry with id {entry.get('pid')}: {e}")
                    continue 

            print(f"Processing of {input_file} complete. Results saved to {output_file}")

        except Exception as e:
            print(f"Error reading input file {input_file}: {e}")
    
    def process_and_save_incrementally_direct(input_file, output_file):
        try:

            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            random.shuffle(data)

            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as out_f:
                    results = json.load(out_f)
            else:
                results = []

            processed_ids = {entry["pid"] for entry in results}

            for entry in tqdm(data):
                try:
                    if entry["pid"] in processed_ids:
                        # print(f"Skipping already processed entry with id {entry['pid']}")
                        continue

                    user_query = entry.get("query", "")
                    given_information = entry.get("given_information", "")
                    if not user_query:
                        raise ValueError("Missing query")
                    if not given_information:
                        raise ValueError("Missing given information")


                    travel_agent = TravelAgent(user_query=user_query, model_name=model_name, api_key=api_key, base_url=base_url)
                    try:
                        final_plan = travel_agent.run_direct(given_information)
                    except Exception as e:
                        print(f"Error during run() for entry with id {entry.get('pid')}: {e}")
                        import traceback
                        traceback.print_exc()  
                        continue

                    results.append({'pid': entry['pid'], 'query': entry['query'], f"{model_name}_{mode}_plan": final_plan})

                    with open(output_file, 'w', encoding='utf-8') as out_f:
                        json.dump(results, out_f, ensure_ascii=False, indent=4)

                    print(f"Processed and saved entry with id {entry['pid']}")

                except Exception as e:
                    print(f"Error processing entry with id {entry.get('pid')}: {e}")
                    continue 

            print(f"Processing of {input_file} complete. Results saved to {output_file}")

        except Exception as e:
            print(f"Error reading input file {input_file}: {e}")
    
    def genarate_given_info(input_file, input_info_file, output_text_file, output_info_file):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with open(input_info_file, 'r', encoding='utf-8') as f:
                input_info_data = json.load(f)
            
            random.shuffle(data)

            if os.path.exists(output_text_file):
                with open(output_text_file, 'r', encoding='utf-8') as out_f:
                    text_results = json.load(out_f)
            else:
                text_results = []
            
            if os.path.exists(output_info_file):
                with open(output_info_file, 'r', encoding='utf-8') as out_f:
                    info_results = json.load(out_f)
            else:
                info_results = {}

            processed_ids = {entry["pid"] for entry in text_results}

            for entry in tqdm(data):
                try:
                    if entry["pid"] in processed_ids:
                        # print(f"Skipping already processed entry with id {entry['pid']}")
                        continue

                    user_query = entry.get("query", "")
                    if not user_query:
                        raise ValueError("Missing query")

                    travel_agent = TravelAgent(user_query=user_query, model_name=model_name, api_key=api_key, base_url=base_url)
                    try:
                        given_data, given_information = travel_agent.run_presearch(input_info_data[str(entry['pid'])])
                    except Exception as e:
                        print(f"Error during run() for entry with id {entry.get('pid')}: {e}")
                        import traceback
                        traceback.print_exc()  
                        continue

                    text_results.append({'pid': entry['pid'], 'query': entry['query'], "given_information": given_information})
                    info_results[str(entry['pid'])] = given_data


                    with open(output_text_file, 'w', encoding='utf-8') as out_f:
                        json.dump(text_results, out_f, ensure_ascii=False, indent=4)
                    
                    with open(output_info_file, 'w', encoding='utf-8') as out_f:
                        json.dump(info_results, out_f, ensure_ascii=False, indent=4)

                    print(f"Processed and saved entry with id {entry['pid']}")

                except Exception as e:
                    print(f"Error processing entry with id {entry.get('pid')}: {e}")
                    continue 

            print(f"Processing of {input_file} complete. Results saved to {output_file}")

        except Exception as e:
            print(f"Error reading input file {input_file}: {e}")

    output_file = f'{output_path}/{model_name}_{mode}.json' 

    if mode == 'direct':
        process_and_save_incrementally_direct(input_file, output_file)
    elif mode == 'presearch':
        input_info_file = ''
        output_text_file = output_file
        output_info_file = ''
        genarate_given_info(input_file, input_info_file, output_text_file, output_info_file)
   
    else:
        while True:
            process_and_save_incrementally(input_file, output_file)
 