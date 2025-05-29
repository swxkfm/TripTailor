import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re
from agents.UserDemands import DemandsInfo
from datetime import datetime

def is_time_greater(time_str1, time_str2):
    time_format = "%H:%M"
    time1 = datetime.strptime(time_str1, time_format)
    time2 = datetime.strptime(time_str2, time_format)
    return time1 >= time2

def extract_demands_info(response):
    # Regex patterns for extraction
    regex_patterns = {
        "departure_day": r"Departure Day:\s*\[(\w+)\]",
        "return_day": r"Return Day:\s*\[(\w+)\]",
        "departure_time": r"Departure Time:\s*\[(early morning|late morning|morning|afternoon|evening)\]",
        "return_time": r"Return Time:\s*\[(early morning|late morning|morning|afternoon|evening)\]",
        "duration": r"Duration:\s*\[(\d+)\]",
        "departure_city": r"Departure City:\s*\[([^\]]+)\]",
        "destination_city": r"Destination City:\s*\[([^\]]+)\]",
        "other_requirements": r"Other Requirements:\s*\[(.*)\]",
        "hotel_cost": r"Hotel Cost:\s*\[(\w+)\]",
        "meal_cost_range": r"Meal Cost Range:\s*\[(\d+)\s*,\s*(\d+)\]",
        "budget": r"Budget:\s*\[(\d+)\]"
    }
    
    # Extract data
    extracted_data = {}
    for key, pattern in regex_patterns.items():
        match = re.search(pattern, response)
        if match:
            extracted_data[key] = match.groups() if len(match.groups()) > 1 else match.group(1)
        else:
            extracted_data[key] = None  # Set None if not found
    
    # Convert tuple for meal_cost_range back to string format
    if isinstance(extracted_data["meal_cost_range"], tuple):
        extracted_data["meal_cost_range"] = [int(extracted_data['meal_cost_range'][0]),int(extracted_data['meal_cost_range'][1])]
    
    return DemandsInfo(
        departure_day=extracted_data["departure_day"],
        return_day=extracted_data["return_day"],
        departure_time = extracted_data["departure_time"],
        return_time = extracted_data["return_time"],
        duration=int(extracted_data["duration"]) if extracted_data["duration"] else None,
        departure_city=extracted_data["departure_city"],
        destination_city=extracted_data["destination_city"],
        other_requirements=extracted_data["other_requirements"],
        hotel_cost=extracted_data["hotel_cost"],
        meal_cost_range=extracted_data["meal_cost_range"],
        budget=extracted_data["budget"]
    )

def extract_transportation_info(response):
    """
    Extracts the most suitable Flight Number or Train Number and specifies its type (Flight or Train).

    Args:
        text (str): The input text containing transportation recommendations.

    Returns:
        tuple: A tuple containing the type ("Flight" or "Train") and the selected number.
    """
    # Define the regex pattern
    pattern = r'(Flight Number|Train Number)\[\s*(.*?)\s*\]'
    
    # Search for a single match
    match = re.search(pattern, response)
    
    if match:
        transport_type = match.group(1)  # "Flight Number" or "Train Number"
        transport_number = match.group(2).strip()  # Extract the number and clean up whitespace
        return (transport_type.replace(" Number", ""), transport_number)  # Simplify type
    else:
        return None, None

def format_transport_options(transport_options, reverse=False, max_records=8):
    results = []

    flights = transport_options["flights"]
    if reverse:
        flights = flights.iloc[::-1] 
    # flights = flights.head(max_records)

    for _, row in flights.iterrows():
        flight_info = (
            f"Flight Number: {row['Flight Number']}, "
            f"Departure Time: {row['Departure Time']}, Arrival Time: {row['Arrival Time']}, "
            f"Price: ¥{int(row['Price'])}, "
            f"On-Time Performance: {row['On-Time Performance']}, "
            f"Average Delay: {row['Average Delay (minutes)']} minutes"
        )
        results.append(flight_info)

    trains = transport_options["trains"]
    if reverse:
        trains = trains.iloc[::-1] 
    # trains = trains.head(max_records)

    for _, row in trains.iterrows():
        train_info = (
            f"Train Number: {row['Train_Number']}, "
            f"Departure Time: {row['Departure_Time']}, "
            f"Arrival Time: {row['Arrival_Time']}"
        )
        if row['Second_Class_Price'] > 0:
            train_info += f", Second Class Price: ¥{int(row['Second_Class_Price'])}"
        if row['First_Class_Price'] > 0:
            train_info += f", First Class Price: ¥{int(row['First_Class_Price'])}"
        results.append(train_info)

    return results

def format_poi_information(poi_data, start_index, end_index):
    results = []


    selected_pois = poi_data.iloc[start_index:end_index]

    for _, row in selected_pois.iterrows():
        level = row['sightLevelStr'] if pd.notnull(row['sightLevelStr']) else "3A"
        price = f"¥{row['price']}" if pd.notnull(row['price']) else "free"
        tags = row['tagNameList'] if row['tagNameList'] else "No Tags"
        features = row['shortFeatures'] if pd.notnull(row['shortFeatures']) else "No Features"

        poi_info = (
            f"POI ID: {row['poiId']}, "
            f"Name: {row['poiName']}, "
            f"Rating: {row['commentScore']}, "
            f"Heat Score: {row['heatScore']}, "
            f"Sight Level: {level}, "
            f"Price: {price}, "
            f"Tags: {tags}, "
            f"Features: {features},"
            f"Recommended Duration: {row['reference_time']},"
            f"Opening Hours: {row['opening_hours']}"
        )
        results.append(poi_info)

    return results

def extract_poi_id(response):
    match = re.search(r'Attractions\s*\[([^\]]*)\]', response)
    if match:
        numbers = re.findall(r'\d+', match.group(1))
        number_list = list(map(int, numbers))
        return number_list
    else:
        return None

def format_restaurant_information(restaurant_data):
    results = []

    selected_restaurants = restaurant_data

    for _, row in selected_restaurants.iterrows():
        name = row['name'] if pd.notnull(row['name']) else "Unknown Name"
        avg_price = f"¥{row['avg_price']}" if pd.notnull(row['avg_price']) else "Not Available"
        small_cate = row['small_cate'] if pd.notnull(row['small_cate']) else "General"
        stars = row['stars'] if pd.notnull(row['stars']) else "No Rating"
        good_remarks = row['good_remarks'] if pd.notnull(row['good_remarks']) else "No Positive Feedback"
        bad_remarks = row['bad_remarks'] if pd.notnull(row['bad_remarks']) else "No Negative Feedback"
        product_rating = row['product_rating'] if pd.notnull(row['product_rating']) else "No Rating"
        environment_rating = row['environment_rating'] if pd.notnull(row['environment_rating']) else "No Rating"
        service_rating = row['service_rating'] if pd.notnull(row['service_rating']) else "No Rating"

        restaurant_info = (
            f"Restaurant ID: {row['id']}, "
            f"Name: {name}, "
            f"Avg Price: {avg_price}, "
            f"Category: {small_cate}, "
            f"Rating: {stars}, "
            f"Good Remarks: {good_remarks}, "
            f"Bad Remarks: {bad_remarks}, "
            f"Product Rating: {product_rating}, "
            f"Environment Rating: {environment_rating}, "
            f"Service Rating: {service_rating} "
        )
        results.append(restaurant_info)

    return results

def format_hotel_information(hotel_data):
    results = []
    selected_hotels = hotel_data

    for _, row in selected_hotels.iterrows():
        name = row['name'] if pd.notnull(row['name']) else "Unknown Name"
        avg_price = f"¥{row['avg_price']}" if pd.notnull(row['avg_price']) else "Not Available"
        small_cate = row['small_cate'] if pd.notnull(row['small_cate']) else "General"
        stars = row['stars'] if pd.notnull(row['stars']) else "No Rating"
        good_remarks = row['good_remarks'] if pd.notnull(row['good_remarks']) else "No Positive Feedback"
        bad_remarks = row['bad_remarks'] if pd.notnull(row['bad_remarks']) else "No Negative Feedback"
        product_rating = row['product_rating'] if pd.notnull(row['product_rating']) else "No Rating"
        environment_rating = row['environment_rating'] if pd.notnull(row['environment_rating']) else "No Rating"
        service_rating = row['service_rating'] if pd.notnull(row['service_rating']) else "No Rating"

        hotel_info = (
            f"Hotel ID: {row['id']}, "
            f"Name: {name}, "
            f"Avg Price: {avg_price}, "
            f"Category: {small_cate}, "
            f"Rating: {stars}, "
            f"Good Remarks: {good_remarks}, "
            f"Bad Remarks: {bad_remarks}, "
            f"Product Rating: {product_rating}, "
            f"Environment Rating: {environment_rating}, "
            f"Service Rating: {service_rating} "
        )
        results.append(hotel_info)

    return results


def format_poi_plan(attractions, poiId):
    selected_pois = attractions[attractions['poiId']==poiId]

    for _, row in selected_pois.iterrows():
        level = row['sightLevelStr'] if pd.notnull(row['sightLevelStr']) else "No Level"
        price = f"¥{row['price']}" if pd.notnull(row['price']) else "¥0"
        tags = row['tagNameList'] if pd.notnull(row['tagNameList']) else 'No Tags'
        features = row['shortFeatures'] if pd.notnull(row['shortFeatures']) else "No Features"
        reference_time = row['reference_time'] if pd.notnull(row['reference_time']) else "2-3 hours"
        summary = row['summary'] if pd.notnull(row['summary']) else "No Summary"

        latitude = float(row['latitude'])
        longitude = float(row['longitude'])

        poi_info = (
            f"Name: {row['poiName']}, "
            f"Level: {level}, "
            f"Price: {price}, "
            f"tags: {tags}, "
            f"Features: {features}, "
            f"Recommended Duration: {reference_time}, "
            f"Summary: {summary}"
        )

    return poi_info, latitude, longitude


def extract_poi_lists(input_text):
    # Regex to match anything inside square brackets
    matches = re.findall(r"\[\s*([^\]]+?)\s*\]", input_text)
    result = []
    
    # Helper function to safely convert a string to an integer
    def safe_convert_to_int(s):
        try:
            return int(s)
        except ValueError:
            return None  # Or return a default value like 0, depending on your needs
    
    for match in matches:
        result.append([x for x in map(lambda x: safe_convert_to_int(x.strip()), match.split(",")) if x is not None])
  
    return result

def df_to_dict(df):
    df_data = df.where(pd.notnull(df), None).to_dict(orient='records')
    return df_data

def format_given_information(given_info, departure_city, destination_city):
    transportations_info = []
    for direction in ['transport_otd', 'transport_dto']:
        if direction == 'transport_otd':
            transportations_info.append(f'Transportation options for the first day from {departure_city} to {destination_city}\n')
        elif direction == 'transport_dto':
            transportations_info.append(f'Transportation options for the last day from {destination_city} to {departure_city}\n') 
        for transportation in given_info[direction]:
            if transportation == 'flight_options':
                for transport in given_info[direction][transportation]:
                    flight_info = (
                        f"Flight Number: {transport['Flight Number']}, "
                        f"Price: ¥{int(transport['Price'])}, "
                        f"Departure Time: {transport['Departure Time']}, "
                        f"Estimated Arrival Time: {transport['Estimated Arrival Time']}, "
                        f"On-Time Performance: {transport['On-Time Performance']}, "
                        f"Average Delay (minutes): {transport['Average Delay (minutes)']}"
                    )
                    transportations_info.append(flight_info)
            elif transportation == 'train_options':
                for transport in given_info[direction][transportation]:
                    train_info = (
                        f"Train Number: {transport['Train_Number']}, "
                        f"Price: ¥{int(transport['Second_Class_Price'])}, "
                        f"Departure Time: {transport['Departure_Time']}, "
                        f"Arrival Time: {transport['Arrival_Time']}"
                    )
                    transportations_info.append(train_info)

    attractions_info = []
    for attraction in given_info['attractions']:
        poi_name = attraction.get('poiName') if attraction.get('poiName') is not None else "Unknown Name"
        sight_level = attraction.get('sightLevelStr') if attraction.get('sightLevelStr') is not None else "No Level"
        comment_score = attraction.get('commentScore') if attraction.get('commentScore') is not None else "No Rating"
        heat_score = attraction.get('heatScore') if attraction.get('heatScore') is not None else "No Heat Score"
        price = f"¥{attraction.get('price')}" if attraction.get('price') is not None else "Free"
        tag_name_list = attraction.get('tagNameList') if attraction.get('tagNameList') is not None else "No Tags"
        short_features = attraction.get('shortFeatures') if attraction.get('shortFeatures') is not None else "No Features"
        reference_time = attraction.get('reference_time') if attraction.get('reference_time') is not None else "No Duration"
        opening_hours = attraction.get('opening_hours') if attraction.get('opening_hours') is not None else "No Opening Hours"
        summary = attraction.get('summary') if attraction.get('summary') is not None else "No Summary"

        poi_info = (
            f"Name: {poi_name}, "
            f"Level: {sight_level}, "
            f"Rating: {comment_score}, "
            f"Heat Score: {heat_score}, "
            f"Price: {price}, "
            f"Tags: {tag_name_list}, "
            f"Features: {short_features}, "
            f"Recommended Duration: {reference_time}, "
            f"Opening Hours: {opening_hours}, "
            f"Summary: {summary}"
        )
        attractions_info.append(poi_info)
    
    restaurants_info = []
    for restaurant in given_info['restaurants']:
        name = restaurant.get('name') if restaurant.get('name') is not None else "Unknown Name"
        avg_price = f"¥{restaurant.get('avg_price')}" if restaurant.get('avg_price') is not None else "Not Available"
        small_cate = restaurant.get('small_cate') if restaurant.get('small_cate') is not None else "General"
        stars = restaurant.get('stars') if restaurant.get('stars') is not None else "No Rating"
        good_remarks = restaurant.get('good_remarks') if restaurant.get('good_remarks') is not None else "No Positive Feedback"
        bad_remarks = restaurant.get('bad_remarks') if restaurant.get('bad_remarks') is not None else "No Negative Feedback"
        product_rating = restaurant.get('product_rating') if restaurant.get('product_rating') is not None else "No Rating"
        environment_rating = restaurant.get('environment_rating') if restaurant.get('environment_rating') is not None else "No Rating"
        service_rating = restaurant.get('service_rating') if restaurant.get('service_rating') is not None else "No Rating"
        nearby_attractions = restaurant.get('nearby_attractions') if restaurant.get('nearby_attractions') is not None else "No Nearby Attractions"

        restaurant_info = (
            f"Name: {name}, "
            f"Avg Price: {avg_price}, "
            f"Category: {small_cate}, "
            f"Rating: {stars}, "
            f"Good Remarks: {good_remarks}, "
            f"Bad Remarks: {bad_remarks}, "
            f"Product Rating: {product_rating}, "
            f"Environment Rating: {environment_rating}, "
            f"Service Rating: {service_rating}, "
            f"Nearby Attractions: {nearby_attractions}"
        )
        restaurants_info.append(restaurant_info)
    
    hotels_info = []
    for hotel in given_info['hotels']:
        name = hotel.get('name') if hotel.get('name') is not None else "Unknown Name"
        avg_price = f"¥{hotel.get('avg_price')}" if hotel.get('avg_price') is not None else "Not Available"
        small_cate = hotel.get('small_cate') if hotel.get('small_cate') is not None else "General"
        stars = hotel.get('stars') if hotel.get('stars') is not None else "No Rating"
        good_remarks = hotel.get('good_remarks') if hotel.get('good_remarks') is not None else "No Positive Feedback"
        bad_remarks = hotel.get('bad_remarks') if hotel.get('bad_remarks') is not None else "No Negative Feedback"
        product_rating = hotel.get('product_rating') if hotel.get('product_rating') is not None else "No Rating"
        environment_rating = hotel.get('environment_rating') if hotel.get('environment_rating') is not None else "No Rating"
        service_rating = hotel.get('service_rating') if hotel.get('service_rating') is not None else "No Rating"
        hotel_info = (
            f"Hotel Name: {name}, "
            f"Avg Price: {avg_price}, "
            f"Category: {small_cate}, "
            f"Rating: {stars}, "
            f"Good Remarks: {good_remarks}, "
            f"Bad Remarks: {bad_remarks}, "
            f"Product Rating: {product_rating}, "
            f"Environment Rating: {environment_rating}, "
            f"Service Rating: {service_rating}"
        )
        hotels_info.append(hotel_info)

    attractions_text = '\n'.join(attractions_info)
    restaurants_text = '\n'.join(restaurants_info)
    hotel_text = '\n'.join(hotels_info)
    transportations_text = '\n'.join(transportations_info)
    given_information = f'Attractions:\n\n{attractions_text}\n\nRestaurants:\n\n{restaurants_text}\n\nHotel:\n\n{hotel_text}\n\nTransportations:\n\n{transportations_text}'
    return given_information

if __name__ == '__main__':
    response = ""
    extract_poi_id(response)
