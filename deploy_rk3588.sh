#!/bin/bash
# RK3588火灾烟雾检测系统部署脚本
# 作者：基于原项目优化
# 适配：RK3588平台

echo "🚀 RK3588火灾烟雾检测系统部署脚本"
echo "================================="

# 检查系统架构
ARCH=$(uname -m)
echo "系统架构: $ARCH"

if [[ $ARCH != "aarch64" ]]; then
    echo "⚠️  警告：此脚本专为ARM64 (aarch64) 架构设计，当前为 $ARCH"
    read -p "是否继续? (y/N): " -n 1 -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 更新系统
echo "📦 更新系统包..."
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
echo "🔧 安装基础依赖..."
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y cmake build-essential pkg-config
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y ffmpeg v4l-utils
sudo apt install -y htop iotop screen tmux

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
cd ~/
python3 -m venv fire-detect-env
source fire-detect-env/bin/activate

# 安装Python依赖
echo "📚 安装Python依赖包..."
pip3 install --upgrade pip

# 针对ARM64优化的包安装
pip3 install numpy==1.24.3
pip3 install opencv-python==4.8.1.78
pip3 install pillow pyyaml tqdm
pip3 install matplotlib seaborn pandas
pip3 install psutil

# PyTorch ARM64版本
echo "🔥 安装PyTorch (ARM64版本)..."
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 克隆项目（如果还没有）
if [ ! -d "fire-smoke-detect" ]; then
    echo "📥 克隆项目代码..."
    git clone https://github.com/gengyanlei/fire-detect-yolov4.git fire-smoke-detect
fi

cd fire-smoke-detect/yolov5

# 下载模型权重（如果没有）
if [ ! -f "best.pt" ]; then
    echo "📥 下载预训练模型..."
    # 这里需要替换为实际的模型下载地址
    echo "请手动下载best.pt模型文件到当前目录"
fi

echo "✅ 基础环境安装完成！"
echo ""
echo "🎯 测试命令："
echo "source ~/fire-detect-env/bin/activate"
echo "cd ~/fire-smoke-detect/yolov5"
echo "python3 detect.py --source 0 --weights ./best.pt --device cpu --img-size 416 --conf 0.4"
echo ""
echo "📱 RTSP摄像头测试："
echo "python3 detect.py --source 'rtsp://admin:password@IP:554/stream' --weights ./best.pt --device cpu --img-size 416"