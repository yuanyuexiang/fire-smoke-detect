# RKNN模型转换环境

## 📋 概述

这是一个独立的模型转换环境，用于在普通Ubuntu系统上将### 步骤3: 转换模型
```bash
# 🎉 推荐使用: 已验证成功的转换器
python3 convert_working.py --input models/best.pt --output output

# 备选: 标准转换器
python3 convert_model.py --input models/best.pt --output output
```

**✅ 推荐使用 `convert_working.py`，已在Ubuntu上验证成功！**

转换成功后会生成：
- `output/best_final_clean.onnx` - ONNX中间格式
- `output/best_final_clean.rknn` - RK3588 NPU模型（最终目标）RKNN格式。转换完成后可以将RKNN模型复制到RK3588设备使用。

## 🎯 转换流程

```
PyTorch(.pt) → ONNX(.onnx) → RKNN(.rknn)
```

## 📁 目录结构

```
model_converter/
├── README.md                    # 本文档
├── requirements.txt             # Python依赖包
├── convert_working.py           # 🎉 推荐转换器 (已验证)
├── convert_model.py             # 标准转换器
├── models/                      # 输入模型目录
│   └── best.pt                  # 原始PyTorch模型
├── output/                      # 输出模型目录
│   ├── best_final_clean.onnx   # 转换的ONNX模型
│   └── best_final_clean.rknn   # 转换的RKNN模型
├── logs/                       # 转换日志
└── docs/                       # 说明文档
    └── DEPLOYMENT_GUIDE.md     # 部署指南
```

## 🚀 快速开始

### 步骤1: 安装环境
```bash
# 安装Python依赖 (Ubuntu系统)
pip3 install -r requirements.txt
```

### 步骤2: 准备模型
```bash
# 复制PyTorch模型到models目录
cp ../yolov5/best.pt models/

# 或者创建符号链接
ln -s ../yolov5/best.pt models/best.pt
```

### 步骤3: 转换模型
```bash
# �� 推荐使用: 已验证成功的转换器
python3 convert_working.py --input models/best.pt --output output

# 🎯 带量化选项的转换器
python3 convert_quantized.py --input models/best.pt --output output              # 使用量化
python3 convert_quantized.py --input models/best.pt --output output --no-quantization  # 不使用量化

# 其他备选转换器
python3 convert_final.py --input models/best.pt --output output
python3 convert_fixed_shape.py --input models/best.pt --output output
python3 convert_weights_only.py --input models/best.pt --output output
python3 convert_model.py --input models/best.pt --output output
```

**✅ 推荐使用 `convert_working.py`，已在Ubuntu上验证成功！**

转换成功后会生成：
- `output/best_final_clean.onnx` - ONNX中间格式
- `output/best_final_clean.rknn` - RK3588 NPU模型（最终目标）

### 步骤4: 部署到RK3588
```bash
# RKNN模型已经生成，直接复制到RK3588项目
cp output/best_final_clean.rknn ../rk3588/models/
cp output/best_final_clean.onnx ../rk3588/models/

# 现在可以直接在RK3588上使用预转换的模型！
```

## 🛠️ 环境要求 (仅支持Linux)

- **⚠️ 重要**: RKNN Toolkit2仅支持Linux系统，不支持Windows/macOS
- **系统**: Ubuntu 18.04+ / Debian 10+ / CentOS 7+ (推荐Ubuntu 20.04)
- **架构**: x86_64 或 ARM64
- **Python**: 3.8-3.12 (推荐3.10)
- **内存**: 至少2GB可用内存 
- **存储**: 至少1GB可用空间
- **网络**: 稳定的互联网连接（用于下载依赖）

## 💡 使用建议

1. **在Mac/Windows开发**: 可以在本地编写代码，但转换必须在Linux上进行
2. **使用云服务器**: 推荐使用阿里云/腾讯云的Ubuntu服务器进行转换
3. **Docker方案**: 可以使用Docker在本地运行Ubuntu容器进行转换
4. **虚拟机方案**: 使用VMware/VirtualBox运行Ubuntu虚拟机

## 📋 依赖包清单 (精简版)

**核心依赖**：
- torch (CPU版本) - PyTorch模型加载
- onnx==1.16.1 - 中间格式转换
- rknn-toolkit2==2.3.2 - RKNN转换核心
- numpy, pillow - 基础工具

**不需要的包** (节省空间)：
- ❌ CUDA/cuDNN (使用CPU转换)
- ❌ OpenCV (转换阶段不需要)
- ❌ matplotlib (不需要可视化)
- ❌ jupyter (不需要交互环境)

## 🎯 使用说明

转换成功后，你会得到：
- `output/best.onnx` - ONNX中间格式 (用于调试)
- `output/best.rknn` - RK3588 NPU模型 (最终目标)
- `logs/conversion.log` - 详细转换日志

将 `best.rknn` 复制到RK3588的 `rknn_models/` 目录即可使用NPU加速！

## 🔧 故障排除

### 转换成功案例 (Ubuntu)
✅ **已验证成功**：使用 `convert_working.py` 在Ubuntu系统上完成转换！

转换过程：
1. ✅ **ONNX转换成功**: 生成固定形状的ONNX模型 (1,3,640,640)
2. ✅ **RKNN构建成功**: OpFusing优化完成，无量化配置问题
3. ✅ **模型导出成功**: 生成 `best_final_clean.rknn` NPU模型

日志示例：
```
2025-09-23 23:04:30,367 - INFO - 🔥 最终确认版本转换
2025-09-23 23:04:30,636 - INFO - ✓ ONNX: output/best_final_clean.onnx
I rknn building ...
I rknn building done.
2025-09-23 23:04:31,458 - INFO - ✅ 成功! RKNN: output/best_final_clean.rknn
```

### 常见问题
1. **RKNN工具包安装失败**: 检查Python版本兼容性，确保使用Linux系统
2. **模型加载失败**: 确认PyTorch模型文件完整，使用固定形状转换器
3. **转换超时**: 增加系统内存或使用量化选项
4. **依赖冲突**: 使用虚拟环境隔离依赖
5. **量化类型错误**: 确保使用新版本兼容的量化类型如 `w8a8`

### 调试命令 (仅在Ubuntu上执行)
```bash
# 检查环境
python3 -c "import torch, onnx; from rknn.api import RKNN; print('环境OK')"

# 查看模型信息
python3 -c "import torch; m=torch.load('models/best.pt'); print(type(m))"

# 检查ONNX模型
python3 -c "import onnx; m=onnx.load('output/best_fixed.onnx'); print([i.name for i in m.graph.input])"
```