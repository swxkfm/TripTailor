export INPUT_FILE="../database_EN/test.json"
export OUTPUT_DIR="../agents/outputs"
export MODEL_NAME="qwen-plus"
export SET_TYPE=test
export STRATEGY=direct
export SUBMISSION_FILE="./outputs/qwen-plus_direct_result.json"

python combination.py  --set_type $SET_TYPE --input_file $INPUT_FILE --output_dir $OUTPUT_DIR --model_name $MODEL_NAME --strategy $STRATEGY --submission_file $SUBMISSION_FILE
