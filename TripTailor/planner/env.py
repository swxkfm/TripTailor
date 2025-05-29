import re
import json
from fuzzywuzzy import fuzz
import pandas as pd

def calculate_total_cost(text):
    # Use regex to find all occurrences of 'Cost: ¥<amount>'
    cost_matches = re.findall(r'Cost: ¥(\d+)', text)
    
    # Convert matches to integers and calculate the sum
    total_cost = sum(map(int, cost_matches))
    
    return total_cost

class ReactEnv:
    def __init__(self):
        pass
    
    def run(self, tested_data):

        total_cost = 0
        unit = tested_data
        people_number = 1
        returned_info = []

        if 'transportation' in unit and unit['transportation'] and unit['transportation'] != '-':
            pass

        if 'lunch' in unit and unit['lunch'] and unit['lunch'] != '-':
            total_cost += calculate_total_cost(unit['lunch']) * people_number

        if 'dinner' in unit and unit['dinner'] and unit['dinner'] != '-':
            total_cost += calculate_total_cost(unit['dinner']) * people_number

        if 'accommodation' in unit and unit['accommodation'] and unit['accommodation'] != '-':
            total_cost += calculate_total_cost(unit['accommodation']) * people_number
        
        if 'attraction' in unit and unit['attraction'] and unit['attraction'] != '-':
            total_cost += calculate_total_cost(unit['attraction']) * people_number
         
        if len(returned_info) == 0:
            return f"The cost of your plan is ¥{total_cost} (except transportation cost)."
        else:
            message = "Sorry, the cost of your plan is not available because of the following reasons:"
            for idx, info in enumerate(returned_info):
                message += str(idx + 1) + ". " + info + " " + '\t'
            return message

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

def match_flight(number, transportations):
    flight = [transportation for transportation in transportations if transportation['Flight Number'] == number]
    if not flight:
        return False
    return True

def match_train(number, transportations):
    train = [transportation for transportation in transportations if transportation['Train_Number'] == number]
    if not train:
        return False
    return True

def match_restaurant(name, restaurants):
    return find_best_match(restaurants, name, name_col='name', substring_threshold=80, edit_distance_threshold=50)

def match_attraction(name, attractions):
    return find_best_match(attractions, name, name_col='poiName', substring_threshold=80, edit_distance_threshold=50)

def match_accommodation(name, accommodations):
    return find_best_match(accommodations, name, name_col='name', substring_threshold=80, edit_distance_threshold=50)
        
class ReactReflectEnv():
    def __init__(self):
        self.is_terminated = False
        self.max_retry_step = 3
        self.retry_step = 0

        with open('given_info_data.json') as f:
            self.given_data = json.load(f)

    def reset(self):
        self.is_terminated = False
        self.retry_step = 0

    def run(self, tested_data, id):
        total_cost = 0
        unit = tested_data
        people_number = 1
        returned_info = []

        given_info = self.given_data[str(id)]

        if 'transportation' in unit and unit['transportation'] and unit['transportation'] != '-':
            value = unit['transportation']
            flights = given_info['transport_otd']['flight_options'] + given_info['transport_dto']['flight_options']
            trains = given_info['transport_otd']['train_options'] + given_info['transport_dto']['train_options']
            if 'flight number' in value.lower():
                try:
                    if match_flight(value.split('Flight Number: ')[1].split(',')[0], flights):
                        total_cost += calculate_total_cost(unit['transportation']) * people_number
                    else:
                        returned_info.append('The filght information is not valid')
                except:
                    returned_info.append('The filght information is not valid')

            if 'train number' in value.lower():
                try:
                    if match_flight(value.split('Train Number: ')[1].split(',')[0], trains):
                        total_cost += calculate_total_cost(unit['transportation']) * people_number
                    else:
                        returned_info.append('The train information is not valid')
                except:
                    returned_info.append('The train information is not valid')

        if 'lunch' in unit and unit['lunch'] and unit['lunch'] != '-':
            matched, _ = match_restaurant(unit['lunch'].split(',')[0], pd.DataFrame(given_info['restaurants']))
            if matched:
                total_cost += calculate_total_cost(unit['lunch']) * people_number
            else:
                returned_info.append('The lunch information is not valid, please check.')

        if 'dinner' in unit and unit['dinner'] and unit['dinner'] != '-':
            matched, _ = match_restaurant(unit['dinner'].split(',')[0], pd.DataFrame(given_info['restaurants']))
            if matched:
                total_cost += calculate_total_cost(unit['dinner']) * people_number
            else:
                returned_info.append('The dinner information is not valid, please check.')

        if 'accommodation' in unit and unit['accommodation'] and unit['accommodation'] != '-':
            matched, _ = match_accommodation(unit['accommodation'].split(',')[0], pd.DataFrame(given_info['hotel']))
            if matched:
                total_cost += calculate_total_cost(unit['accommodation']) * people_number
            else:
                returned_info.append('The accommodation information is not valid, please check.')
        
        if 'attraction' in unit and unit['attraction'] and unit['attraction'] != '-':
            matched, _ = match_attraction(unit['attraction'].split(',')[0], pd.DataFrame(given_info['attractions']))
            if matched:
                total_cost += calculate_total_cost(unit['attraction']) * people_number
            else:
                returned_info.append('The attraction information is not valid, please check.')
        
        if len(returned_info) == 0:
            self.retry_step = 0
            self.is_terminated = False
            return f"The cost of your plan is ¥{total_cost}."
        else:
            message = "Sorry, the cost of your plan is not available because of the following reasons:"
            for idx, info in enumerate(returned_info):
                message += str(idx + 1) + ". " + info + " " + '\t'
            self.retry_step += 1
            if self.retry_step >= self.max_retry_step:
                self.is_terminated = True
            return message
        
