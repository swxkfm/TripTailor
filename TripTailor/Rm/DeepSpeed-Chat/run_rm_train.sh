#!/bin/bash
# Copyright (c) Microsoft Corporation.
# SPDX-License-Identifier: Apache-2.0

# DeepSpeed Team
OUTPUT=$1
ZERO_STAGE=$2
if [ "$OUTPUT" == "" ]; then
    OUTPUT="output_path"
fi
if [ "$ZERO_STAGE" == "" ]; then
    ZERO_STAGE=3
fi
mkdir -p $OUTPUT


CUDA_VISIBLE_DEVICES=0,1,2,3 deepspeed main.py \
   --data_path travel \
   --data_split 0,10,0 \
   --model_name_or_path "model_name_or_path" \
   --per_device_train_batch_size 4 \
   --per_device_eval_batch_size 1 \
   --max_seq_len 4096 \
   --learning_rate 1e-5 \
   --weight_decay 0.01 \
   --num_padding_at_beginning 0 \
   --num_train_epochs 2  \
   --gradient_accumulation_steps 2 \
   --lr_scheduler_type cosine \
   --num_warmup_steps 0 \
   --seed 42 \
   --gradient_checkpointing \
   --zero_stage $ZERO_STAGE \
   --deepspeed \
   --enable_tensorboard \
   --tensorboard_path "tensorboard_path" \
   --output_dir $OUTPUT \
   &> $OUTPUT/training.log
