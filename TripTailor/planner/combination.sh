export OUTPUT_DIR=""
export MODEL_NAME=""
# SET_TYPE in ['validation', 'test']
export SET_TYPE=test
# STRATEGY in ['direct','cot','react','reflexion']
export STRATEGY=reflexion
export SUBMISSION_FILE=""

python combination.py  --set_type $SET_TYPE --output_dir $OUTPUT_DIR --model_name $MODEL_NAME --strategy $STRATEGY --submission_file $SUBMISSION_FILE