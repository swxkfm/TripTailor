export INPUT_FILE="input_file"
export OUTPUT_DIR="output_dir"
export MODEL_NAME="model_name"
# SET_TYPE in ['validation', 'test']
export SET_TYPE=test
# STRATEGY in ['direct','cot','react','reflexion']
export STRATEGY=direct
export SUBMISSION_FILE="submission_file"

python combination.py  --set_type $SET_TYPE --input_file $INPUT_FILE --output_dir $OUTPUT_DIR --model_name $MODEL_NAME --strategy $STRATEGY --submission_file $SUBMISSION_FILE