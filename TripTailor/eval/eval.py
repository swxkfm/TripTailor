from geopy.distance import geodesic
import re
from datetime import datetime
import json
import pandas as pd
from fuzzywuzzy import fuzz
from tqdm import tqdm
from utils.ChatClient import ChatClient
from prompt import EXTRACT_PROMPT, EVALUATION_PROMPT
import argparse
import os

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
OPENAI_BASE_URL = os.environ['OPENAI_BASE_URL']

def fuzzy_match(target, candidate, substring_threshold=90, edit_distance_threshold=80):
    target = target.lower()
    candidate = candidate.lower()
    matched = False
    partial_score = fuzz.partial_ratio(target, candidate)
    if partial_score >= substring_threshold:
        matched = True

    edit_distance_score = fuzz.ratio(target, candidate)
    if edit_distance_score >= edit_distance_threshold:
        matched = True

    if not matched:
        return False, 0
    else:
        return True, edit_distance_score

def find_best_match(df, target_name, name_col="name", substring_threshold=90, edit_distance_threshold=80):
    df = df.copy()
    df["match_result"] = df[name_col].apply(
        lambda x: fuzzy_match(target_name, x, substring_threshold, edit_distance_threshold)[0]
    )
    df["match_score"] = df[name_col].apply(
        lambda x: fuzzy_match(target_name, x, substring_threshold, edit_distance_threshold)[1]
    )

    matched_df = df[df["match_result"]]

    if not matched_df.empty:
        best_match = matched_df.loc[matched_df["match_score"].idxmax()]
        return True, best_match
    else:
        return False, pd.DataFrame()

def is_complete_information(plan):
    if 'hotel' not in plan:
        return False
    if not plan['hotel']:
        return False
    
    if 'transportation' not in plan:
        return False
    if len(plan['transportation']) != 2:
        return False
    for transportation in plan['transportation']:
        for item_key in ['number', 'time', 'price']:
            if item_key not in transportation:
                return False
            if transportation[item_key] == '':
                return False 

    return True

def match_flight(number, transportations):
    flight = [transportation for transportation in transportations if transportation['Flight Number'] == number]
    if not flight:
        return False
    return True

def match_train(number, transportations):
    train = [transportation for transportation in transportations if number == transportation['Train_Number']]
    train1 = [transportation for transportation in transportations if number in transportation['Train_Number'].split('/')]
    if not train and not train1:
        return False
    return True

def match_restaurant(name, restaurants):
    if 'name_en' in restaurants.columns.tolist():
        name_col = 'name_en'
    else:
        name_col = 'name'
    return find_best_match(restaurants, name, name_col=name_col, substring_threshold=90, edit_distance_threshold=80)

def match_attraction(name, attractions):
    if 'name_en' in attractions.columns.tolist():
        name_col = 'name_en'
    else:
        name_col = 'poiName'
    return find_best_match(attractions, name, name_col=name_col, substring_threshold=90, edit_distance_threshold=50)

def match_accommodation(name, accommodations):
    if 'Hotel Name' in accommodations.columns.tolist():
        name_col = 'Hotel Name'
    else:
        name_col = 'name'
    return find_best_match(accommodations, name, name_col=name_col, substring_threshold=90, edit_distance_threshold=80)


def is_within_sandbox(plan, given_info):
    hotel = plan['hotel'][0]
    transportation = plan['transportation']
    daily_itinerary = plan['itinerary']

    hotel_res = True

    given_hotels = pd.DataFrame(given_info['hotel'])
    matched, _ = match_accommodation(hotel['name'], given_hotels)
    if not matched:
        hotel_res = False

    transportation_res = True
    
    transportation_otd_flights = given_info['transport_otd']['flight_options']
    transportation_otd_trains = given_info['transport_otd']['train_options']

    transportation_dto_flights = given_info['transport_dto']['flight_options']
    transportation_dto_trains = given_info['transport_dto']['train_options']

    if len(transportation) != 2:
        transportation_res = False
    else:
        if transportation[0]['mode'].lower() == 'Flight'.lower():
            if not match_flight(transportation[0]['number'], transportation_otd_flights):
                transportation_res = False
        elif 'Train'.lower() in transportation[0]['mode'].lower():
            if not match_train(transportation[0]['number'], transportation_otd_trains):
                transportation_res = False
        else:
            transportation_res = False
        
        if transportation[1]['mode'].lower() == 'Flight'.lower():
            if not match_flight(transportation[1]['number'], transportation_dto_flights):
                transportation_res = False
        elif 'Train'.lower() in transportation[1]['mode'].lower():
            if not match_train(transportation[1]['number'], transportation_dto_trains):
                transportation_res = False
        else:
            transportation_res = False
    
    given_restaurants = pd.DataFrame(given_info['restaurants'])
    given_attractions = pd.DataFrame(given_info['attractions'])

    attraction_res = True
    restaurant_res = True

    for day in daily_itinerary:
        itinerary = daily_itinerary[day]
        for activity in itinerary:
            if activity['action'] == 'sightseeing':
                matched, _ = match_attraction(activity['location'], given_attractions)
                if not matched:
                    attraction_res = False
            elif activity['action'] == 'dining':
                matched, _ = match_restaurant(activity['location'], given_restaurants)
                if not matched:
                    restaurant_res = False
    res = {'hotel': hotel_res, 'transportation':transportation_res, 'attraction': attraction_res, 'restaurant':restaurant_res}
    if hotel_res and transportation_res and attraction_res and restaurant_res:
        return True, res
    else:
        return False, res

def if_diverse_restaurants(plan):
    daily_itinerary = plan['itinerary']
    restaurant_names = set()

    for day in daily_itinerary:
        itinerary = daily_itinerary[day]
        for activity in itinerary:
            if activity['action'] == 'dining':
                restaurant_name = activity['location'].lower()
                if restaurant_name in restaurant_names:
                    return False
                restaurant_names.add(restaurant_name)

    return True

def if_diverse_attractions(plan):
    daily_itinerary = plan['itinerary']
    attraction_names = set()

    for day in daily_itinerary:
        itinerary = daily_itinerary[day]
        for activity in itinerary:
            if activity['action'] == 'sightseeing':
                attraction_name = activity['location'].lower()
                if attraction_name in attraction_names:
                    return False
                attraction_names.add(attraction_name)

    return True

def is_within_budget(plan, days, budget):
    cost = plan['hotel'][0]['price_per_night'] * (days - 1)
    for transportation in plan['transportation']:
        cost += transportation['price']
    for day in plan['itinerary']:
        for activity in plan['itinerary'][day]:
            cost += activity['price']
    
    return cost <= budget

def is_reasonable_meal_prices(plan, meal_price_range):
    pass_num = 0
    failed_num = 0
    for day in plan['itinerary']:
        for activity in plan['itinerary'][day]:
            if activity['action'] == 'dining':
                cost = activity['price']
                if cost > meal_price_range[1] or cost < meal_price_range[0]:
                    failed_num += 1
                else:
                    pass_num += 1
    if failed_num > 0:
        return False
    return True

def sort_daily_itinerary(json_str):
    data = json.loads(json_str)
    
    for day in data["itinerary"]:
        activities = data["itinerary"][day]
        
        sorted_activities = sorted(activities, 
                                 key=lambda x: parse_time(clean_time_str(x["time"])))
        data["itinerary"][day] = sorted_activities
    
    return json.dumps(data, indent=2, ensure_ascii=False)

def clean_time_str(time_str):
    cleaned = time_str.replace('-', '–')
    return cleaned.split('–')[0].strip()

def parse_time(time_str):
    try:
        return datetime.strptime(time_str, "%H:%M")
    except ValueError as e:
        print(f"{time_str}")
        return datetime.min
            
def route_lenght(plan, given_info, mode=0):
    hotel = plan['hotel'][0]
    daily_itinerary = plan['itinerary']

    given_hotels = pd.DataFrame(given_info['hotel'])
    _, hotel_selected = match_accommodation(hotel['name'], given_hotels)
    hotel_point = (float(hotel_selected['latitude']), float(hotel_selected['longitude']))

    given_restaurants = pd.DataFrame(given_info['restaurants'])
    given_attractions = pd.DataFrame(given_info['attractions'])

    distance_list = []

    for day in daily_itinerary:
        itinerary = daily_itinerary[day]
        if mode == 0:
            last_point = hotel_point
        else:
            last_point = None
        for activity in itinerary:
            if activity['action'] == 'dining':
                if mode != 2:
                    _, selected_restaurant = match_restaurant(activity['location'], given_restaurants)
                    point = (float(selected_restaurant['latitude']), float(selected_restaurant['longitude'])) 
                else:
                    continue   
            elif activity['action'] == 'sightseeing':
                _, selected_attraction = match_attraction(activity['location'], given_attractions)
                point = (float(selected_attraction['latitude']), float(selected_attraction['longitude']))
            else:
                continue
            if last_point is not None:
                distance_list.append(geodesic(point, last_point).kilometers)
            last_point = point

        if mode == 0:
            distance_list.append(geodesic(last_point, hotel_point).kilometers)

    return sum(distance_list) / len(distance_list) if len(distance_list) > 0 else 0

def parse_time_range(time_str):
    time_pattern = re.compile(
        r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(hour|minute|day)s?|'  # 匹配范围（如 2-4 hours）
        r'(Over|Under)\s*(\d+\.?\d*)\s*(hour|minute|day)s?|'     # 匹配 Over/Under（如 Over 3 hours）
        r'(\d+\.?\d*)\s*(hour|minute|day)s?'                     # 匹配单个值（如 1 hour）
    )

    match = time_pattern.search(time_str)
    if not match:
        return None  # 如果没有匹配到，返回 None

    if match.group(1) and match.group(2):  # 匹配范围（如 2-4 hours）
        min_time = float(match.group(1))
        max_time = float(match.group(2))
        unit = match.group(3)
        return {"min": min_time, "max": max_time, "unit": unit}
    elif match.group(4):  # 匹配 Over/Under（如 Over 3 hours）
        modifier = match.group(4)
        time_value = float(match.group(5))
        unit = match.group(6)
        if modifier.lower() == "over":
            return {"min": time_value, "max": float("inf"), "unit": unit}
        elif modifier.lower() == "under":
            return {"min": 0, "max": time_value, "unit": unit}
    elif match.group(7):  # 匹配单个值（如 1 hour）
        time_value = float(match.group(7))
        unit = match.group(8)
        return {"min": time_value, "max": time_value, "unit": unit}

    return None

def calculate_time_duration(time_range):
    time_range = time_range.replace('–', '-')
    
    try:
        start_time_str, end_time_str = time_range.split('-')
        start_time = datetime.strptime(start_time_str.strip(), '%H:%M')
        end_time = datetime.strptime(end_time_str.strip(), '%H:%M')
        
        time_difference = end_time - start_time
        duration_minutes = int(time_difference.total_seconds() / 60)
        return duration_minutes
    except Exception as e:
        return None

def check_duration(time, reference_time):
    if pd.isna(reference_time):
        return True
    
    if reference_time == '':
        return True
    
    reference_time_range = parse_time_range(reference_time)
    time_duration = calculate_time_duration(time)

    if reference_time_range is None:
        return True
    
    if time_duration is None:
        return False

    if reference_time_range['unit'] == 'day':
        max_time = reference_time_range['max'] * 1440
        min_time = reference_time_range['min'] * 1440 / 4 - 60
    elif reference_time_range['unit'] == 'hour':
        max_time = reference_time_range['max'] * 60 + 60
        min_time = reference_time_range['min'] * 60 - 60
    elif reference_time_range['unit'] == 'minute':
        max_time = reference_time_range['max'] + 60
        min_time = reference_time_range['min']
    
    if max_time == min_time:
        min_time = min_time * 0.5
        max_time = max_time * 1.5
    
    return (time_duration >= min_time) & (time_duration <= max_time)

def is_appropriate_visit_duration(plan, given_info):
    given_attractions = pd.DataFrame(given_info['attractions'])
    daily_itinerary = plan['itinerary']

    pass_num = 0
    failed_num = 0

    for day in daily_itinerary:
        itinerary = daily_itinerary[day]
        for activity in itinerary:
            if activity['action'] == 'sightseeing':
                _, selected_attraction = match_attraction(activity['location'], given_attractions)
                if 'recommended_duration' in selected_attraction:
                    item_key = 'recommended_duration'
                else:
                    item_key = 'reference_time'
                try:
                    if not check_duration(activity['time'], selected_attraction[item_key]):
                        failed_num += 1
                    else:
                        pass_num += 1
                except:
                    failed_num += 1
    if failed_num > 0:
        return False
    return True

def eval(input_file, plan_key, given_info_data, given_info_data_final):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)

    for item in tqdm(data):
        plan_json = json.loads(item[f'{plan_key}_plan_json'])
        plan_json_f = json.loads(item['final_plan_json'])
        given_info = given_info_data[str(item['pid'])]
        given_info_f = given_info_data_final[str(item['pid'])]

        within_sandbox, within_sandbox_res = is_within_sandbox(plan_json, given_info)
        complete_information = is_complete_information(plan_json)
        feasibility = within_sandbox and complete_information

        diverse_restaurants = if_diverse_restaurants(plan_json)
        diverse_attractions = if_diverse_attractions(plan_json)
        within_budget = is_within_budget(plan_json, item['day'], item['budget'])
        reasonable_meal_prices = is_reasonable_meal_prices(plan_json, item['meal_price_range'])
        
        if within_sandbox_res['attraction']:
            appropriate_visit_duration = is_appropriate_visit_duration(plan_json, given_info)
            average_route_distance = [route_lenght(plan_json, given_info, mode=i) for i in range(3)]

        else:
            appropriate_visit_duration = False
            average_route_distance = [None] * 3
        
        rationality = diverse_attractions and diverse_restaurants and reasonable_meal_prices and within_budget and appropriate_visit_duration
        
        result = {
            'Within Sandbox': within_sandbox,
            'Complete Information': complete_information,
            'Feasibility': feasibility,
            'Defined Budget Limit': within_budget,
            'Diverse Restaurants': diverse_restaurants,
            'Diverse Attractions': diverse_attractions,
            'Reasonable Meal Prices': reasonable_meal_prices,
            'Appropriate Visit Duration': appropriate_visit_duration,
            'Rationality': rationality,
            'Average Route Distance':average_route_distance
        }

        item[f'{plan_key}_plan_constraint'] = result
        average_route_distance_f = [route_lenght(plan_json_f, given_info_f, mode=i) for i in range(3)]
        item['final_plan_constraint'] = {'Average Route Distance': average_route_distance_f}
    
    return data

def extract_plan(input_file, plan_key, model_name, api_key, base_url):
    chat_client = ChatClient(model_name=model_name, api_key=api_key, base_url=base_url)
    with open(input_file, encoding='utf-8') as f:
        input_data = json.load(f)

    for input_item in tqdm(input_data):
        if f'{plan_key}_plan_json' not in input_item:
            try:
                itinerary = input_item[f'{plan_key}_plan']
                if isinstance(itinerary, list):
                    itinerary_text = '\n\n'.join(itinerary)
                else:
                    itinerary_text = itinerary
                prompt = EXTRACT_PROMPT.format(itinerary=itinerary_text)
                result = chat_client.chat_completion(user_message=prompt, temperature=0)
                res_dic = json.loads(result.split('```json')[-1].split('```')[0])

            except Exception as e:
                print(f"Error during processing with pid {input_item['pid']}: {e}")
                import traceback
                traceback.print_exc()
                continue
                        
            input_item[f'{plan_key}_plan_json'] = json.dumps(res_dic, ensure_ascii=False)

            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(input_data, f, ensure_ascii=False, indent=4)

def format_restaurant_information(restaurant_data):
    row = restaurant_data

    name = row['name'] if pd.notnull(row['name']) else "Unknown Name"
    avg_price = f"¥{row['avg_price']}" if pd.notnull(row['avg_price']) else "Not Available"
    small_cate = row['small_cate'] if pd.notnull(row['small_cate']) else "General"
    stars = row['stars'] if pd.notnull(row['stars']) else "No Rating"
    product_rating = row['product_rating'] if pd.notnull(row['product_rating']) else "No Rating"
    environment_rating = row['environment_rating'] if pd.notnull(row['environment_rating']) else "No Rating"
    service_rating = row['service_rating'] if pd.notnull(row['service_rating']) else "No Rating"

    restaurant_info = (
        f"Name: {name}, "
        f"Avg Price: {avg_price}, "
        f"Category: {small_cate}, "
        f"Rating: {stars}, "
        f"Product Rating: {product_rating}, "
        f"Environment Rating: {environment_rating}, "
        f"Service Rating: {service_rating}, "
    )

    return [restaurant_info]

def format_hotel_information(hotel_data):
    row = hotel_data
    name = row['name'] if pd.notnull(row['name']) else "Unknown Name"
    avg_price = f"¥{row['avg_price']}" if pd.notnull(row['avg_price']) else "Not Available"
    small_cate = row['small_cate'] if pd.notnull(row['small_cate']) else "General"
    stars = row['stars'] if pd.notnull(row['stars']) else "No Rating"
    product_rating = row['product_rating'] if pd.notnull(row['product_rating']) else "No Rating"
    environment_rating = row['environment_rating'] if pd.notnull(row['environment_rating']) else "No Rating"
    service_rating = row['service_rating'] if pd.notnull(row['service_rating']) else "No Rating"

    hotel_info = (
        f"Name: {name}, "
        f"Avg Price: {avg_price}, "
        f"Category: {small_cate}, "
        f"Rating: {stars}, "
        f"Product Rating: {product_rating}, "
        f"Environment Rating: {environment_rating}, "
        f"Service Rating: {service_rating} "
    )

    return [hotel_info]

def format_flight_information(data):
    res_info = []
    for item in data:
        info = (
            f"Flight Number: {item['Flight Number']}, "
            f"Departure Time: {item['Departure Time']}, "
            f"Estimated Arrival Time: {item['Estimated Arrival Time']}, "
            f"On-Time Performance: {item['On-Time Performance']}, "
            f"Average Delay (minutes): {item['Average Delay (minutes)']}"
        )
        res_info.append(info)

    return res_info

def format_train_information(data):
    res_info = []
    for item in data:
        info = (
            f"Train Number: {item['Train_Number']}, "
            f"Departure Time: {item['Departure_Time']}, "
            f"Arrival Time: {item['Arrival_Time']}"
        )
        res_info.append(info)

    return res_info

def get_match_flight(number, transportations):
    flight = [transportation for transportation in transportations if transportation['Flight Number'] == number]
    if not flight:
        return False, None
    return True, flight[0]

def get_match_train(number, transportations):
    train = [transportation for transportation in transportations if number == transportation['Train_Number']]
    train1 = [transportation for transportation in transportations if number in transportation['Train_Number'].split('/')]
    if not train and not train1:
        return False, None
    if not train:
        return True, train[0]
    else:
        return True, train1[0]

def get_reference_information(plan, given_info):
    hotel = plan['hotel'][0]
    transportation = plan['transportation']
    daily_itinerary = plan['itinerary']

    given_hotels = pd.DataFrame(given_info['hotel'])
    matched, accommodation = match_accommodation(hotel['name'], given_hotels)
    if matched:
        accommodation = format_hotel_information(accommodation)
    else:
        accommodation = []
    
    transportation_otd_flights = given_info['transport_otd']['flight_options']
    transportation_otd_trains = given_info['transport_otd']['train_options']

    transportation_dto_flights = given_info['transport_dto']['flight_options']
    transportation_dto_trains = given_info['transport_dto']['train_options']

    if transportation[0]['mode'].lower() == 'Flight'.lower():
        matched, transport_otd = get_match_flight(transportation[0]['number'], transportation_otd_flights)
        if matched:
            transport_otd = format_flight_information([transport_otd])
        else:
             transport_otd = []
    elif 'Train'.lower() in transportation[0]['mode'].lower():
        matched, transport_otd = get_match_train(transportation[0]['number'], transportation_otd_trains)
        if matched:
            transport_otd = format_train_information([transport_otd])
        else:
             transport_otd = []
    else:
        transport_otd = []
    
    if len(transportation) < 2:
        transport_dto = []
    else:
        if transportation[1]['mode'].lower() == 'Flight'.lower():
            matched, transport_dto = get_match_flight(transportation[1]['number'], transportation_dto_flights)
            if matched:
                transport_dto = format_flight_information([transport_dto])
            else:
                transport_dto = []
        elif 'Train'.lower() in transportation[1]['mode'].lower():
            matched, transport_dto = get_match_train(transportation[1]['number'], transportation_dto_trains)
            if matched:
                transport_dto = format_train_information([transport_dto])
            else:
                transport_dto = []
        else:
            transport_dto = []
    
    given_restaurants = pd.DataFrame(given_info['restaurants'])

    restaurants_info = []

    for day in daily_itinerary:
        itinerary = daily_itinerary[day]
        for activity in itinerary:
            if activity['action'] == 'dining':
                matched, restaurant = match_restaurant(activity['location'], given_restaurants)
                if matched:
                    restaurant = format_restaurant_information(restaurant)
                    restaurants_info += restaurant
    
    restaurants_text = 'n'.join(restaurants_info)
    accommodation_text = 'n'.join(accommodation)
    transport_text = '\n'.join(transport_otd + transport_dto)
    reference_information = f"Restaurants:\n\n{restaurants_text}\n\nHotel:\n\n{accommodation_text}\n\nTransportations:\n\n{transport_text}"
    return reference_information

def get_total_cost(plan, days):
    cost = plan['hotel'][0]['price_per_night'] * (days - 1)
    for transportation in plan['transportation']:
        cost += transportation['price']
    for day in plan['itinerary']:
        for activity in plan['itinerary'][day]:
            cost += activity['price']
    
    return cost

def llm_eval_plan(input_file, plan_key, given_info_data, model_name, api_key, base_url):
    chat_client = ChatClient(model_name=model_name, api_key=api_key, base_url=base_url)
    with open(input_file, encoding='utf-8') as f:
        input_data = json.load(f)
        
    for item in tqdm(input_data):
        if f'{plan_key}_eval_result' not in item or f'{model_name}_eval' not in item[f'{plan_key}_eval_result']:
            final_plan = '\n\n'.join(item['final_plan'])
            total_cost = get_total_cost(json.loads(item[f'final_plan_json']), item['day'])
            final_plan = final_plan + f'\nTotal Cost: \n¥{total_cost}'
            try:
                if given_info_data is not None:
                    reference_information = get_reference_information(json.loads(item[f'{plan_key}_plan_json']), given_info_data[str(item['pid'])])
            except Exception as e:
                print(f"Error during get_reference_information with pid {item['pid']}: {e}")
                continue
            plan = item[f'{plan_key}_plan']
            try:
                total_cost_p = get_total_cost(json.loads(item[f'{plan_key}_plan_json']), item['day'])
            except Exception as e:
                print(f"Error during get_total_cost with pid {item['pid']}: {e}")
                continue
            if given_info_data is not None:
                plan = plan + f'\nTotal Cost: \n¥{total_cost_p}\n' + '\nReference Information:\n' + reference_information
            else:
                plan = plan + f'\nTotal Cost: \n¥{total_cost_p}'
            query = item['query']

            try:
                prompt = EVALUATION_PROMPT.format(query=query, plan_a=final_plan, plan_b=plan)
                result = chat_client.chat_completion(user_message=prompt, temperature=0)
                res_dic = json.loads(result.split('```json')[-1].split('```')[0])

                prompt_r = EVALUATION_PROMPT.format(query=query, plan_a=plan, plan_b=final_plan)
                result_r = chat_client.chat_completion(user_message=prompt_r, temperature=0)
                res_dic_r = json.loads(result_r.split('```json')[-1].split('```')[0])
            except Exception as e:
                print(f"Error during processing with pid {item['pid']}: {e}")
                import traceback
                traceback.print_exc()
                continue

            if f'{plan_key}_eval_result' not in item:
                item[f'{plan_key}_eval'] = {f'{model_name}_eval': [result, result_r]}
                res_dic['plan'] = {'Plan A': 'final', 'Plan B': plan_key}
                res_dic_r['plan'] = {'Plan A': plan_key, 'Plan B': 'final'}
                item[f'{plan_key}_eval_result'] = {f'{model_name}_eval': [res_dic, res_dic_r]}
            else:
                item[f'{plan_key}_eval'][f'{model_name}_eval'] = [result, result_r]
                res_dic['plan'] = {'Plan A': 'final', 'Plan B': plan_key}
                res_dic_r['plan'] = {'Plan A': plan_key, 'Plan B': 'final'}
                item[f'{plan_key}_eval_result'][f'{model_name}_eval'] = [res_dic, res_dic_r]

            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(input_data, f, ensure_ascii=False, indent=4)

def llm_eval(input_file, plan_key):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)

    for item in data:

        evaluation_results = item[f'{plan_key}_eval_result']
        average_score = 0
        average_score_f = 0

        for evaluation_name, evaluation_data in evaluation_results.items():
            for evaluation_item in evaluation_data:
                if plan_key == evaluation_item['plan']['Plan A']:
                    average_score += evaluation_item['Personalization Evaluation']["Scores"]["Plan A"] / (len(evaluation_data) * len(evaluation_results))
                    average_score_f += evaluation_item['Personalization Evaluation']["Scores"]["Plan B"] / (len(evaluation_data) * len(evaluation_results))
                elif plan_key == evaluation_item['plan']['Plan B']:
                    average_score += evaluation_item['Personalization Evaluation']["Scores"]["Plan B"] / (len(evaluation_data) * len(evaluation_results))
                    average_score_f += evaluation_item['Personalization Evaluation']["Scores"]["Plan A"] / (len(evaluation_data) * len(evaluation_results))
        
        result = {f'{plan_key}_plan': average_score, 'final_plan': average_score_f}
        item[f'{plan_key}_llm_score'] = result
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def rm_eval(input_file, result_file, plan_key):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)
    
    with open(result_file, encoding='utf-8') as f:
         results = json.load(f)

    for item in data:
        result = [r for r in results if r['pid']==item['pid']][0]
        item[f'{plan_key}_rm_score'] = result[f'{plan_key}_plan_rm_score']
        item['final_plan_rm_score'] = result['final_plan_rm_score']
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
def eval_result(input_file, plan_key, data_mode='all'):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)
    
    average_route_distance_list_1 = []
    average_route_distance_list_2 = []
    average_route_distance_list_3 = []
    average_route_distance_ref_list_1 = []
    average_route_distance_ref_list_2 = []
    average_route_distance_ref_list_3 = []
    average_route_distance_ratio_list_1 = []
    average_route_distance_ratio_list_2 = []
    average_route_distance_ratio_list_3 = []
    result = {
        'method': plan_key,
        'average_route_distance_ratio':0,
        'average_route_distance_ratio_without_hotel':0,
        'average_route_distance_ratio_without_hotel_restaurant':0,
        'average_route_distance':0,
        'average_route_distance_without_hotel':0,
        'average_route_distance_without_hotel_restaurant':0,
        'average_route_distance_ref':0,
        'average_route_distance_ref_without_hotel':0,
        'average_route_distance_ref_without_hotel_restaurant':0,
        'feasibility_micro':0,
        'feasibility_macro':0,
        'rationality_micro':0,
        'rationality_macro':0,
        'llm':0,
        'rm':0,
        'final_surpassing_rate':0
        }
    if data_mode == 'easy':
        data = [item for item in data if item['day'] in [2,3]]
    elif data_mode == 'hard':
        data = [item for item in data if item['day'] in [4,5,6,7]]
    for item in data:
        constraint = item[f'{plan_key}_plan_constraint']
        result['feasibility_micro'] += (int(constraint['Within Sandbox']) + int(constraint['Complete Information'])) / 2
        result['feasibility_macro'] += int(constraint['Feasibility'])
        result['rationality_micro'] += (int(constraint['Defined Budget Limit']) + int(constraint['Diverse Restaurants']) + 
                                        int(constraint['Diverse Attractions']) + int(constraint['Reasonable Meal Prices']) + int(constraint['Appropriate Visit Duration'])) / 5
        result['rationality_macro'] += int(constraint['Rationality'])

        average_route_distance_ref_list_1.append(item['final_plan_constraint']['Average Route Distance'][0])
        average_route_distance_ref_list_2.append(item['final_plan_constraint']['Average Route Distance'][1])
        average_route_distance_ref_list_3.append(item['final_plan_constraint']['Average Route Distance'][2])
        if constraint['Average Route Distance'][0] is not None:
            average_route_distance_list_1.append(constraint['Average Route Distance'][0])
            if item['final_plan_constraint']['Average Route Distance'][0] != 0:
                average_route_distance_ratio_list_1.append(constraint['Average Route Distance'][0] / item['final_plan_constraint']['Average Route Distance'][0])
        if constraint['Average Route Distance'][1] is not None:
            average_route_distance_list_2.append(constraint['Average Route Distance'][1])
            if item['final_plan_constraint']['Average Route Distance'][1] != 0:
                average_route_distance_ratio_list_2.append(constraint['Average Route Distance'][1] / item['final_plan_constraint']['Average Route Distance'][1])
        if constraint['Average Route Distance'][2] is not None:
            average_route_distance_list_3.append(constraint['Average Route Distance'][2])
            if item['final_plan_constraint']['Average Route Distance'][2] != 0:
                average_route_distance_ratio_list_3.append(constraint['Average Route Distance'][2] / item['final_plan_constraint']['Average Route Distance'][2])
        
        if item[f'{plan_key}_llm_score'][f'{plan_key}_plan'] > item[f'{plan_key}_llm_score']['final_plan']:
            result['llm'] += 1
        
        if item[f'{plan_key}_rm_score'] > item['final_plan_rm_score']:
            result['rm'] += 1
        
        if constraint['Feasibility'] and constraint['Rationality']:
            if item[f'{plan_key}_llm_score'][f'{plan_key}_plan'] > item[f'{plan_key}_llm_score']['final_plan'] or item[f'{plan_key}_rm_score'] > item['final_plan_rm_score']:
                result['final_surpassing_rate'] += 1
    
    for key in result.keys():
        if key not in ['method','average_route_distance_ratio','average_route_distance_ratio_without_hotel',
                       'average_route_distance_ratio_without_hotel_restaurant','average_route_distance','average_route_distance_without_hotel',
                       'average_route_distance_without_hotel_restaurant', 'average_route_distance_ref','average_route_distance_ref_without_hotel',
                       'average_route_distance_ref_without_hotel_restaurant']:
            result[key] /= len(data)
            result[key] *= 100
        
    result['average_route_distance_ratio'] = sum(average_route_distance_ratio_list_1) / len(average_route_distance_ratio_list_1)
    result['average_route_distance_ratio_without_hotel'] = sum(average_route_distance_ratio_list_2) / len(average_route_distance_ratio_list_2)
    result['average_route_distance_ratio_without_hotel_restaurant'] = sum(average_route_distance_ratio_list_3) / len(average_route_distance_ratio_list_3)
    result['average_route_distance'] = sum(average_route_distance_list_1) / len(average_route_distance_list_1)
    result['average_route_distance_without_hotel'] = sum(average_route_distance_list_2) / len(average_route_distance_list_2)
    result['average_route_distance_without_hotel_restaurant'] = sum(average_route_distance_list_3) / len(average_route_distance_list_3)
    result['average_route_distance_ref'] = sum(average_route_distance_ref_list_1) / len(average_route_distance_ref_list_1)
    result['average_route_distance_ref_without_hotel'] = sum(average_route_distance_ref_list_2) / len(average_route_distance_ref_list_2)
    result['average_route_distance_ref_without_hotel_restaurant'] = sum(average_route_distance_ref_list_3) / len(average_route_distance_ref_list_3)

    print(f'{data_mode} ({len(data)}): ')
    for key, value in result.items():
        if key != 'method':
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
        
def eval_result_detail(input_file, plan_key, data_mode='all'):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)
    result = {
        'planning': data_mode,
        'method': plan_key,
        'Within Sandbox':0,
        'Complete Information':0,
        'Defined Budget Limit':0,
        'Diverse Restaurants':0,
        'Diverse Attractions':0,
        'Reasonable Meal Prices':0,
        'Appropriate Visit Duration':0,
        'llm':0,
        'rm':0,
        'Final Pass Rate':0,
        'Final Surpassing Rate':0
        }
    if data_mode == 'easy':
        data = [item for item in data if item['day'] in [2,3]]
    elif data_mode == 'hard':
        data = [item for item in data if item['day'] in [4,5,6,7]]
    for item in data:
        constraint = item[f'{plan_key}_plan_constraint']
        result['Within Sandbox'] += int(constraint['Within Sandbox'])
        result['Complete Information'] += int(constraint['Complete Information'])
        result['Defined Budget Limit'] += int(constraint['Defined Budget Limit'])
        result['Diverse Restaurants'] += int(constraint['Diverse Restaurants'])
        result['Diverse Attractions'] +=  int(constraint['Diverse Attractions'])
        result['Reasonable Meal Prices'] += int(constraint['Reasonable Meal Prices']) 
        result['Appropriate Visit Duration'] += int(constraint['Appropriate Visit Duration'])
        if item[f'{plan_key}_llm_score'][f'{plan_key}_plan'] > item[f'{plan_key}_llm_score']['final_plan']:
            result['llm'] += 1
        if item[f'{plan_key}_rm_score'] > item['final_plan_rm_score']:
            result['rm'] += 1
        
        if constraint['Feasibility'] and constraint['Rationality']:
            result['Final Pass Rate'] += 1
            if item[f'{plan_key}_llm_score'][f'{plan_key}_plan'] > item[f'{plan_key}_llm_score']['final_plan'] or item[f'{plan_key}_rm_score'] > item['final_plan_rm_score']:
                result['Final Surpassing Rate'] += 1
    
    for key in result.keys():
        if key != 'planning':
            result[key] /= len(data)
            result[key] *= 100

    for key, value in result.items():
        if key != 'planning' and key != 'method':
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="")
    parser.add_argument("--strategy", type=str, default="direct")
    parser.add_argument("--input_file", type=str, default="./")
    parser.add_argument("--info_file", type=str, default="./")
    parser.add_argument("--eval_model_name", type=str, default="")
    parser.add_argument("--rm_file", type=str, default="./")


    args = parser.parse_args()
    input_file = args.input_file
    model_name = args.eval_model_name
    api_key = OPENAI_API_KEY
    base_url = OPENAI_BASE_URL

    plan_key = f'{args.model_name}_{args.strategy}'
    with open(args.info_file, encoding='utf-8') as f:
        given_info_data = json.load(f)
    eval(input_file, plan_key, given_info_data)
    extract_plan(input_file, plan_key, model_name, api_key, base_url)
    llm_eval_plan(input_file, plan_key, given_info_data, model_name, api_key, base_url)
    llm_eval(input_file, plan_key)
    rm_eval(input_file, args.rm_file, plan_key)
    eval_result(input_file, plan_key, data_mode='all')
    eval_result_detail(input_file, plan_key, data_mode='all')
