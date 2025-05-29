from tqdm import tqdm
import json
import argparse
import os

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--set_type", type=str, default="test")
    parser.add_argument("--model_name", type=str, default="gpt-3.5-turbo-1106")
    parser.add_argument("--strategy", type=str, default="direct")
    parser.add_argument("--output_dir", type=str, default="./")
    parser.add_argument("--submission_file", type=str, default="./")
    parser.add_argument("--query_data_path", type=str, default="../agents/output/test.json")
    parser.add_argument("--selected_data_path", type=str, default="../Rm/data/test_selected.json")

    args = parser.parse_args()

    if args.set_type == 'test':
        with open(args.query_data_path, encoding='utf-8') as f:
            query_data_list = json.load(f)
        with open(args.selected_data_path, encoding='utf-8') as f:
            data = json.load(f)

    if os.path.exists(args.submission_file):
        with open(args.submission_file, encoding='utf-8') as f:
            result_data = json.load(f)
    else:
        result_data = []
    
    fields_to_extract = ["destination_city", "departure_city", "day", "pid", "meal_price_range", "budget", "query", "final_plan", "final_plan_json"]
    
    numbers = [i for i in range(1,len(query_data_list)+1)]

    if args.strategy in ['react', 'reflexion']:
        result_key = f'{args.model_name}_{args.strategy}_sole-planning_results_expand'
    else:
        result_key = f'{args.model_name}_{args.strategy}_sole-planning_results'
    
    for number in tqdm(numbers):
        query_data = query_data_list[number-1]
        with open(f'{args.output_dir}/{args.set_type}/generated_plan_{number}.json', encoding='utf-8') as f:
            result = json.load(f)
        query = query_data['query']
        pid = query_data['pid']
        plan = result[-1][result_key]

        test_data = [item for item in data if item['pid'] == pid]
        if not test_data:
            continue
        test_item = test_data[0]

        results = [item for item in result_data if item['pid'] == pid]
        if not results:
            result_item = {field: test_item[field] for field in fields_to_extract}
            result_item[f'{args.model_name}_{args.strategy}_plan'] = plan
            result_data.append(result_item)
        else:
            result_item = results[0]
            result_item[f'{args.model_name}_{args.strategy}_plan'] = plan
    
    with open(args.submission_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=4, ensure_ascii=False)
