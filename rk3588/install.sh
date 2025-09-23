#!/bin/bash

# RK3588环境安装脚本
# 自动安装所有必要的依赖和工具

set -e  # 如果任何命令失败则退出

echo "====== RK3588 火烟检测系统安装脚本 ======"
echo "开始安装环境依赖..."

# 检查系统架构
ARCH=$(uname -m)
echo "系统架构: $ARCH"

if [[ "$ARCH" != "aarch64" ]]; then
    echo "警告: 当前系统不是ARM64架构，请确认在RK3588上运行此脚本"
fi

# 更新系统包管理器
echo "更新系统包..."
sudo apt update

# 安装系统依赖
echo "安装系统依赖包..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    cmake \
    build-essential \
    libopencv-dev \
    python3-opencv \
    ffmpeg \
    v4l-utils \
    git \
    wget \
    curl

# 升级pip
echo "升级pip..."
python3 -m pip install --upgrade pip

# 安装Python依赖
echo "安装Python依赖包..."
pip3 install -r requirements.txt

# 检测Python版本并安装对应的RKNN Toolkit2
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python版本: $PYTHON_VERSION"

# 设置RKNN Toolkit2下载URL
case $PYTHON_VERSION in
    "3.8")
        RKNN_WHL="https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.2/rknn_toolkit2-2.3.2+81f21f4d-cp38-cp38-linux_aarch64.whl"
        ;;
    "3.9")
        RKNN_WHL="https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.2/rknn_toolkit2-2.3.2+81f21f4d-cp39-cp39-linux_aarch64.whl"
        ;;
    "3.10")
        RKNN_WHL="https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.2/rknn_toolkit2-2.3.2+81f21f4d-cp310-cp310-linux_aarch64.whl"
        ;;
    "3.11")
        RKNN_WHL="https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.2/rknn_toolkit2-2.3.2+81f21f4d-cp311-cp311-linux_aarch64.whl"
        ;;
    "3.12")
        RKNN_WHL="https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.2/rknn_toolkit2-2.3.2+81f21f4d-cp312-cp312-linux_aarch64.whl"
        ;;
    *)
        echo "警告: Python版本 $PYTHON_VERSION 可能不受支持"
        echo "尝试通过pip安装..."
        pip3 install rknn-toolkit2
        ;;
esac

# 下载并安装RKNN Toolkit2
if [[ -n "$RKNN_WHL" ]]; then
    echo "下载RKNN Toolkit2 for Python $PYTHON_VERSION..."
    WHL_FILE="rknn_toolkit2-2.3.2-cp${PYTHON_VERSION//./}-linux_aarch64.whl"
    
    if [[ ! -f "$WHL_FILE" ]]; then
        wget -O "$WHL_FILE" "$RKNN_WHL"
    fi
    
    echo "安装RKNN Toolkit2..."
    pip3 install "$WHL_FILE"
fi

# 创建必要目录
echo "创建工作目录..."
mkdir -p rknn_models
mkdir -p logs
mkdir -p output

# 设置权限
echo "设置脚本权限..."
chmod +x scripts/*.sh
chmod +x *.py

# 验证安装
echo "验证安装..."
python3 -c "import rknn_toolkit2; print(f'RKNN Toolkit2 版本: {rknn_toolkit2.__version__}')" || echo "RKNN Toolkit2未安装"
python3 -c "import cv2; print(f'OpenCV 版本: {cv2.__version__}')"
python3 -c "import torch; print(f'PyTorch 版本: {torch.__version__}')"
python3 -c "import numpy; print(f'NumPy 版本: {numpy.__version__}')"

echo ""
echo "====== 安装完成 ======"
echo "下一步操作:"
echo "1. 转换模型: python3 convert_to_rknn.py --input models/best.pt --output rknn_models"
echo "2. 测试检测: python3 detect_rknn.py --source 0 --weights rknn_models/best.rknn"
echo "3. 启动服务: ./scripts/rk3588_manager.sh start"
echo ""