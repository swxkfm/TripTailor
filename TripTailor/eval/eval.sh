#!/bin/bash

MODEL_NAME="qwen-plus"
STRATEGY="direct"
INPUT_FILE="../agents/outputs/qwen-plus_direct_result.json"  
INFO_FILE="../database_EN/given_info_data.json"   
FINAL_INFO_FILE="../database_EN/infomation.json"     
EVAL_MODEL_NAME=""                        
RM_FILE=""               

API_KEY=""
BASE_URL=""

export OPENAI_API_KEY="$API_KEY"
export OPENAI_BASE_URL="$BASE_URL"

LOG_FILE="eval_${MODEL_NAME}_${STRATEGY}_log.txt"

python eval.py --model_name "$MODEL_NAME" \
               --strategy "$STRATEGY" \
               --input_file "$INPUT_FILE" \
               --info_file "$INFO_FILE" \
               --final_info_file "$FINAL_INFO_FILE" \
               --eval_model_name "$EVAL_MODEL_NAME" \
               --rm_file "$RM_FILE" \
               &> "./$LOG_FILE"