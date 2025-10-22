# TripTailor Shell Scripts Usage Guide

本项目包含多个shell脚本，用于不同的旅行规划任务。以下是每个脚本的详细使用说明。

## 📁 项目结构

```
TripTailor/
├── agents/                    # 旅行代理相关脚本
│   ├── run_TravelAgent.sh     # 完整工作流程
│   ├── run_presearch.sh       # 预搜索模式
│   ├── run_TravelAgent_direct.sh  # 直接规划模式
│   └── combination.sh         # 结果组合
├── planner/                   # 规划器相关脚本
│   ├── run_sole_planning.sh   # 独立规划
│   └── combination.sh         # 规划结果组合
├── eval/                      # 评估相关脚本
│   └── eval.sh               # 评估脚本
└── Rm/DeepSpeed-Chat/         # 模型训练
    └── run_rm_train.sh       # 奖励模型训练
```

## 🚀 脚本详细说明

### 1. agents/run_TravelAgent.sh
**功能**: 运行完整的旅行代理工作流

**详细配置参数**:
- `INPUT_FILE`: 输入测试文件路径
- `INPUT_INFO_FILE`: 输入信息文件路径
- `OUTPUT_PATH`: 输出目录路径
- `MODEL_NAME`: 使用的模型名称
- `MODE`: 运行模式 (默认: `workflow`)
- `OUTPUT_INFO_FILE`: 输出信息文件路径

**使用方法**:
```bash
cd agents
bash run_TravelAgent.sh
```

**输出**: 在 `./outputs/` 目录生成规划结果和日志文件

---

### 2. agents/run_presearch.sh
**功能**: 运行预搜索模式，为后续规划准备数据

**详细配置参数**:
- `INPUT_FILE`: 输入测试文件路径
- `INPUT_INFO_FILE`: 输入信息文件路径
- `OUTPUT_PATH`: 输出目录路径
- `OUTPUT_INFO_FILE`: 输出预搜索信息文件路径
- `MODEL_NAME`: 使用的模型名称
- `MODE`: 运行模式 (固定: `presearch`)

**使用方法**:
```bash
cd agents
bash run_presearch.sh
```

**输出**: 生成预搜索信息文件，为后续直接规划提供数据

---

### 3. agents/run_TravelAgent_direct.sh
**功能**: 运行直接规划模式，基于预搜索的信息生成规划

**详细配置参数**:
- `INPUT_FILE`: 输入文件路径
- `OUTPUT_PATH`: 输出目录路径
- `MODEL_NAME`: 使用的模型名称
- `MODE`: 运行模式 (固定: `direct`)
- `API_KEY`: API密钥
- `BASE_URL`: API基础URL

**使用方法**:
```bash
cd agents
bash run_TravelAgent_direct.sh
```

**前置条件**: 需要先运行 `run_presearch.sh` 生成输入数据

---

### 4. agents/combination.sh
**功能**: 组合旅行代理的输出结果

**详细配置参数**:
- `INPUT_FILE`: 输入文件路径
- `OUTPUT_DIR`: 输出目录路径
- `MODEL_NAME`: 模型名称
- `SET_TYPE`: 数据集类型 (默认: `test`)
- `STRATEGY`: 策略类型 (默认: `direct`)
- `SUBMISSION_FILE`: 最终结果文件路径

**使用方法**:
```bash
cd agents
bash combination.sh
```

**输出**: 生成最终的结果文件

---

### 5. planner/run_sole_planning.sh
**功能**: 运行独立规划器，支持多种策略

**详细配置参数**:
- `INPUT_FILE`: 输入文件路径
- `SET_TYPE`: 数据集类型 (默认: `test`)
- `MODEL_NAME`: 使用的模型名称
- `OUTPUT_DIR`: 输出目录路径
- `STRATEGY`: 规划策略

**环境变量设置**:
- `OPENAI_API_KEY`: 设置为API密钥
- `OPENAI_BASE_URL`: 设置为API基础URL

**支持的策略**:
- `direct`: 直接规划
- `cot`: 思维链规划 (Chain of Thought)
- `react`: 推理-行动规划 (Reasoning and Acting)
- `reflexion`: 反思式规划

**使用方法**:
```bash
cd planner
bash run_sole_planning.sh
```

**输出**: 在 `./outputs/test/` 目录生成规划结果文件

---

### 6. planner/combination.sh
**功能**: 组合规划器的输出结果

**详细配置参数**:
- `OUTPUT_DIR`: 输出目录路径
- `MODEL_NAME`: 模型名称
- `SET_TYPE`: 数据集类型
- `STRATEGY`: 策略类型
- `SUBMISSION_FILE`: 最终结果文件名

**Python脚本参数**:
- `--query_data_path`: 查询数据路径
- `--selected_data_path`: 测试原始数据路径

**使用方法**:
```bash
cd planner
bash combination.sh
```

**前置条件**: 需要先运行 `run_sole_planning.sh`

---

### 7. eval/eval.sh
**功能**: 评估生成的旅行规划

**详细配置参数**:
- `MODEL_NAME`: 被评估的模型名称
- `STRATEGY`: 被评估的策略
- `INPUT_FILE`: 待评估的结果文件路径
- `INFO_FILE`: 信息文件路径
- `FINAL_INFO_FILE`: 参考计划信息文件路径
- `EVAL_MODEL_NAME`: 用于评估的模型名称
- `RM_FILE`: 奖励模型打分结果文件路径

**使用方法**:
```bash
cd eval
bash eval.sh
```

**输出**: 生成评估报告和日志文件

---

### 8. Rm/DeepSpeed-Chat/run_rm_train.sh
**功能**: 训练奖励模型

**使用方法**:
```bash
cd Rm/DeepSpeed-Chat
bash run_rm_train.sh
```

**输出**: 在指定目录生成训练好的模型和训练日志

## ⚙️ 通用配置

### 环境变量
某些脚本需要设置环境变量：
```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="your_base_url"
```

## 🔄 典型工作流程

### 完整直接规划流程：
```bash
# 1. 预搜索准备数据
cd agents
bash run_presearch.sh

# 2. 运行直接规划
bash run_TravelAgent_direct.sh

# 3. 组合结果
bash combination.sh

# 4. 评估结果
cd ../eval
bash eval.sh
```

### 独立Planner流程：
```bash
# 1. 运行规划器
cd planner
bash run_sole_planning.sh

# 2. 组合结果
bash combination.sh

# 3. 评估
cd ../eval 
bash eval.sh
```

### 模型训练流程：
```bash
# 训练奖励模型
cd Rm/data
python data_transform.py
cd ../DeepSpeed-Chat
bash run_rm_train.sh
```

## 🛠️ 自定义配置

每个脚本的配置参数都在文件顶部，可以根据需要修改：

### 常见修改项：
1. **模型配置**: 修改 `MODEL_NAME` 选择不同模型
2. **API配置**: 修改 `API_KEY` 和 `BASE_URL` 使用不同API
3. **文件路径**: 修改输入输出文件路径
4. **策略选择**: 修改 `STRATEGY` 选择不同规划策略
