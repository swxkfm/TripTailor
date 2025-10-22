#!/bin/bash

INPUT_FILE="../agents/outputs/direct_input.json"
SET_TYPE="test"
MODEL_NAME=""
OUTPUT_DIR="./outputs"
STRATEGY="react" # direct/cot/react/reflexion

API_KEY=""
BASE_URL=""

export OPENAI_API_KEY="$API_KEY"
export OPENAI_BASE_URL="$BASE_URL"
export GOOGLE_API_KEY=""

mkdir -p "$OUTPUT_DIR"

LOG_FILE="${MODEL_NAME}_${STRATEGY}_sole_planning_log.txt"

python sole_planning.py --input_file "$INPUT_FILE" \
                        --set_type "$SET_TYPE" \
                       --model_name "$MODEL_NAME" \
                       --output_dir "$OUTPUT_DIR" \
                       --strategy "$STRATEGY" \
                       &> "$OUTPUT_DIR"/"$LOG_FILE"
