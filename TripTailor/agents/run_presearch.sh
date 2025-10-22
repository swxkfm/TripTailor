#!/bin/bash

INPUT_FILE="../database_EN/test.json"
INPUT_INFO_FILE="../database_EN/infomation.json"
OUTPUT_PATH="./outputs"
OUTPUT_INFO_FILE="../database_EN/given_info_data_direct.json"
MODEL_NAME=""
MODE="presearch"

API_KEY=""
BASE_URL=""

mkdir -p "$OUTPUT_PATH"

LOG_FILE="${MODEL_NAME}_${MODE}_log.txt"

python TravelAgent.py --input_file "$INPUT_FILE" \
                    --info_file "$INPUT_INFO_FILE" \
                    --output_path "$OUTPUT_PATH" \
                    --output_info_file "$OUTPUT_INFO_FILE" \
                    --model_name "$MODEL_NAME" \
                    --mode "$MODE" \
                    --api_key "$API_KEY" \
                    --base_url "$BASE_URL"\
                    &> "$OUTPUT_PATH"/"$LOG_FILE" 
