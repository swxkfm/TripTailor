import os
import json
import random
from datasets import Dataset, DatasetDict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

random.seed(32)

def calculate_tfidf_similarity(query1, query2, vectorizer):
    tfidf_matrix = vectorizer.fit_transform([query1, query2])
    
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return similarity[0][0]

def shuffle_middle_days(plan):
    """
    Shuffle the middle days of a plan.
    :param plan: The original plan list, where each element represents a day's itinerary.
    :return: The plan with middle days shuffled.
    """
    if len(plan) > 3:
        # Extract the middle part (excluding the first and last day)
        middle = plan[1:-1]
        middle_cleaned = [item.split('\n\n', 1)[-1].strip() for item in middle]

        # Ensure the shuffled order is different from the original order
        while True:
            random.shuffle(middle_cleaned)
            if middle_cleaned != [item.split('\n\n', 1)[-1].strip() for item in middle]:
                break

        # Add back the day labels
        middle_shuffled = []
        for i, day_item in enumerate(middle_cleaned, start=2):
            day_label = f"**Day {i} Itinerary**\n\n"
            middle_shuffled.append(f"{day_label}{day_item}")

        # Combine into a complete plan
        shuffled_plan = [plan[0]] + middle_shuffled + [plan[-1]]
        return '\n'.join(shuffled_plan)
    else:
        # If the plan length is not greater than 3, return the original plan
        return '\n'.join(plan)

def find_rejected_plans(data, item, vectorizer, num):
    """
    Find rejected plans that are most different from the current item's query.
    Prioritize plans from the same city and with the same number of days. If not enough, supplement with plans from different cities but with the same number of days.
    """
    # Get plans from the same city and with the same number of days
    same_cities = [
        rdata for rdata in data
        if rdata != item and 
           rdata['departure_city'] == item['departure_city'] and 
           rdata['destination_city'] == item['destination_city'] and
           rdata['day'] == item['day']
    ]

    # Calculate similarity scores
    similarity_scores = [
        (rdata, calculate_tfidf_similarity(rdata['query'], item['query'], vectorizer))
        for rdata in same_cities
    ]

    # Sort by similarity (ascending order)
    similarity_scores.sort(key=lambda x: x[1])

    # Select the most different plans
    rejected_plans = [rdata for rdata, _ in similarity_scores[:num]]

    if len(rejected_plans) < num:
        diff_departure_same_destination = [
            rdata for rdata in data
            if rdata != item and 
               rdata['destination_city'] == item['destination_city'] and 
               rdata['departure_city'] != item['departure_city'] and
               rdata['day'] == item['day']
        ]

        # Calculate similarity scores for these plans
        diff_departure_scores = [
            (rdata, calculate_tfidf_similarity(rdata['query'], item['query'], vectorizer))
            for rdata in diff_departure_same_destination
        ]

        # Sort by similarity and select additional plans
        diff_departure_scores.sort(key=lambda x: x[1])
        additional_plans = [rdata for rdata, _ in diff_departure_scores[:num - len(rejected_plans)]]

        if item['day'] > 2:
            for plan in additional_plans:
                middle_days = plan['final_plan'][1:-1]
                plan['final_plan'] = [item['final_plan'][0]] + middle_days + [item['final_plan'][-1]]
        
        rejected_plans.extend(additional_plans)
    
    if len(rejected_plans) < num:
        same_city_different_days = [
            rdata for rdata in data
            if rdata != item and 
               rdata['destination_city'] == item['destination_city'] and 
               rdata['day'] != item['day']
        ]

        # Calculate similarity scores for these plans
        different_days_scores = [
            (rdata, calculate_tfidf_similarity(rdata['query'], item['query'], vectorizer))
            for rdata in same_city_different_days
        ]

        # Sort by similarity and select additional plans
        different_days_scores.sort(key=lambda x: x[1])
        additional_plans = [rdata for rdata, _ in different_days_scores[:num - len(rejected_plans)]]

        for plan in additional_plans:
            plan_days = len(plan['final_plan'])
            item_days = len(item['final_plan'])

            if plan_days > item_days:
                # Truncate the middle days to match item_days
                plan['final_plan'] = [plan['final_plan'][0]] + plan['final_plan'][1:item_days-1] + [plan['final_plan'][-1]]
            elif plan_days < item_days:
                for rdata, _ in diff_departure_scores[num - len(rejected_plans):]:
                    middle_days = rdata['final_plan'][1:-1]
                    random.shuffle(middle_days)
                    for day_plan in middle_days:
                        plan['final_plan'].insert(-1, day_plan)
                        plan_days += 1
                        if plan_days == item_days:
                            break
                    if plan_days == item_days:
                        break
            rejected_plans.append(plan)

    return rejected_plans


def transform_data(data):
    transformed = []
    vectorizer = TfidfVectorizer()  # Initialize the TF-IDF vectorizer

    for item in data:
        prompt = item['query']
        final_plan = item['final_plan']

        # If the length of final_plan is greater than 3, create two examples: original order and shuffled order
        if len(final_plan) > 3:
            # Original plan
            chosen_original = '\n'.join(final_plan)

            # Shuffle the middle part
            chosen_shuffled = shuffle_middle_days(final_plan)

            # Find rejected plans
            rejected_plans = find_rejected_plans(data, item, vectorizer, 1)
            if not rejected_plans:
                continue

            # Shuffle the middle days for each rejected plan
            for rejected_plan in rejected_plans:
                rejected_final_plan = rejected_plan['final_plan']

                # Original rejected plan
                rejected_original = '\n'.join(rejected_final_plan)

                # Shuffle the middle part of the rejected plan
                rejected_shuffled = shuffle_middle_days(rejected_final_plan)

                # Add the original order example
                transformed.append({
                    'prompt': prompt,
                    'chosen': chosen_original,
                    'rejected': rejected_original,
                    'id': item['pid'],
                    'destination_city': item['destination_city'],
                    'departure_city': item['departure_city']
                })

                if len(rejected_final_plan) > 3:

                    # Add the shuffled order example
                    transformed.append({
                        'prompt': prompt,
                        'chosen': chosen_original,
                        'rejected': rejected_shuffled,
                        'id': item['pid'],
                        'destination_city': item['destination_city'],
                        'departure_city': item['departure_city']
                    })

            # Add the shuffled chosen plan example
            for rejected_plan in rejected_plans:
                rejected_final_plan = rejected_plan['final_plan']

                # Original rejected plan
                rejected_original = '\n'.join(rejected_final_plan)

                # Shuffle the middle part of the rejected plan
                rejected_shuffled = shuffle_middle_days(rejected_final_plan)

                # Add the shuffled chosen plan example
                transformed.append({
                    'prompt': prompt,
                    'chosen': chosen_shuffled,
                    'rejected': rejected_original,
                    'id': item['pid'],
                    'destination_city': item['destination_city'],
                    'departure_city': item['departure_city']
                })

                if len(rejected_final_plan) > 3:

                    # Add the shuffled chosen plan and shuffled rejected plan example
                    transformed.append({
                        'prompt': prompt,
                        'chosen': chosen_shuffled,
                        'rejected': rejected_shuffled,
                        'id': item['pid'],
                        'destination_city': item['destination_city'],
                        'departure_city': item['departure_city']
                    })

        else:
            # If the length is not greater than 3, process directly
            chosen = '\n'.join(final_plan)
            rejected_plans = find_rejected_plans(data, item, vectorizer, 1)
            if not rejected_plans:
                continue

            for rejected_plan in rejected_plans:
                rejected = '\n'.join(rejected_plan['final_plan'])
                transformed.append({
                    'prompt': prompt,
                    'chosen': chosen,
                    'rejected': rejected,
                    'id': item['pid'],
                    'destination_city': item['destination_city'],
                    'departure_city': item['departure_city']
                })

    return transformed

def transform_test_data(data):
    transformed = []
    vectorizer = TfidfVectorizer()  # Initialize the TF-IDF vectorizer

    for item in data:
        prompt = item['query']
        final_plan = item['final_plan']
        chosen_original = '\n\n'.join(final_plan)


        # Find rejected plans
        rejected_plans = find_rejected_plans(data, item, vectorizer, 1)
        if not rejected_plans:
            continue
        transformed.append({
            'prompt': prompt,
            'chosen': chosen_original,
            'rejected': '\n\n'.join(rejected_plans[0]['final_plan']),
            'id': item['pid'],
            'destination_city': item['destination_city'],
            'departure_city': item['departure_city']
        })

    return transformed

# # Load the JSON data

with open('', 'r', encoding='utf-8') as file:
    data = json.load(file)

with open('', 'r', encoding='utf-8') as file:
    test_data = json.load(file)


# Shuffle the original data to ensure randomness
random.shuffle(data)

# # Split the transformed data into train and test sets: 80% train, 20% test
# split_idx = int(len(data) * 0.8)
# train_data = data[:split_idx]
# val_data = data[split_idx:]

train_data = data
val_data = test_data
random.shuffle(val_data)

# Transform the entire dataset
transformed_train_data = transform_data(train_data)
transformed_val_data = transform_test_data(val_data)
 
# Convert to Dataset format
train_dataset = Dataset.from_dict({key: [d[key] for d in transformed_train_data] for key in transformed_train_data[0]})
val_dataset = Dataset.from_dict({key: [d[key] for d in transformed_val_data] for key in transformed_val_data[0]})

# Create a DatasetDict
dataset_dict = DatasetDict({
    'train': train_dataset,
    'test': val_dataset
})

# Save datasets to disk so they can be loaded with `load_from_disk`
dataset_path = 'dataset_path'

dataset_dict.save_to_disk(dataset_path)

