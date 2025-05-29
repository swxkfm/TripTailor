#!/bin/bash

INPUT_FILE="input_file"
OUTPUT_PATH="output_path"
MODEL_NAME="model_name"
MODE="direct"

API_KEY=""
BASE_URL=""

mkdir -p "$OUTPUT_PATH"

LOG_FILE="${MODEL_NAME}_${MODE}_log.txt"

python TravelAgent.py --input_file "$INPUT_FILE" \
                    --output_path "$OUTPUT_PATH" \
                    --model_name "$MODEL_NAME" \
                    --mode "$MODE" \
                    --api_key "$API_KEY" \
                    --base_url "$BASE_URL"\
                    &> "$OUTPUT_PATH"/"$LOG_FILE" 
