OUTPUT_DIR="./outputs"
MODEL_NAME=""
SET_TYPE="test"
STRATEGY="react"
SUBMISSION_FILE="./outputs/${MODEL_NAME}_${STRATEGY}_result.json"

QUERY_DATA_PATH="../agents/outputs/direct_input.json"
SELECTED_DATA_PATH="../database_EN/test.json"

python combination.py \
    --set_type "$SET_TYPE" \
    --output_dir "$OUTPUT_DIR" \
    --model_name "$MODEL_NAME" \
    --strategy "$STRATEGY" \
    --submission_file "$SUBMISSION_FILE" \
    --query_data_path "$QUERY_DATA_PATH" \
    --selected_data_path "$SELECTED_DATA_PATH"
