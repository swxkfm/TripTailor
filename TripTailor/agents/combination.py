from tqdm import tqdm
import json
import argparse
import os

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--set_type", type=str, default="test")
    parser.add_argument("--model_name", type=str, default="")
    parser.add_argument("--strategy", type=str, default="direct")
    parser.add_argument("--output_dir", type=str, default="./")
    parser.add_argument("--submission_file", type=str, default="./")

    args = parser.parse_args()

    if args.set_type == 'test':
        with open(f'{args.output_dir}/{args.model_name}_{args.strategy}.json', encoding='utf-8') as f:
            results = json.load(f)
        with open(args.input_file, encoding='utf-8') as f:
            data = json.load(f)
    
    if os.path.exists(args.submission_file):
        with open(args.submission_file, encoding='utf-8') as f:
            result_data = json.load(f)
    else:
        result_data = []
    
    fields_to_extract = ["destination_city", "departure_city", "day", "pid", "meal_price_range", "budget", "query", "final_plan", "final_plan_json"]
    
    for result in tqdm(results):
        pid = result['pid']
        plan = result[f'{args.model_name}_{args.strategy}_plan']

        test_data = [item for item in data if item['pid'] == pid]
        if not test_data:
            continue
        test_item = test_data[0]

        result_items = [item for item in result_data if item['pid'] == pid]
        if not result_items:
            result_item = {field: test_item[field] for field in fields_to_extract}
            result_item[f'{args.model_name}_{args.strategy}_plan'] = plan
            result_data.append(result_item)
        else:
            result_item = result_items[0]
            result_item[f'{args.model_name}_{args.strategy}_plan'] = plan
    
    with open(args.submission_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=4, ensure_ascii=False)
