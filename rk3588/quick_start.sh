#!/bin/bash

# RK3588 火烟检测系统快速启动脚本
# 一键完成安装、转换、测试的完整流程

set -e

echo "🔥 RK3588 火烟检测系统 - 快速部署脚本 🔥"
echo "============================================"

# 检查系统
echo "📋 检查系统环境..."
if [[ $(uname -m) != "aarch64" ]]; then
    echo "⚠️  警告: 不是ARM64架构，请确认在RK3588上运行"
fi

# 步骤1: 安装环境
echo ""
echo "🚀 步骤1: 安装系统环境..."
if [[ ! -f ".env_installed" ]]; then
    ./install.sh
    touch .env_installed
    echo "✅ 环境安装完成"
else
    echo "✅ 环境已安装，跳过"
fi

# 步骤2: 转换模型
echo ""
echo "🔄 步骤2: 转换PyTorch模型为RKNN..."
if [[ ! -f "rknn_models/best.rknn" ]]; then
    echo "开始模型转换..."
    python3 convert_to_rknn.py --input models/best.pt --output rknn_models
    echo "✅ 模型转换完成"
else
    echo "✅ RKNN模型已存在，跳过转换"
fi

# 步骤3: 验证安装
echo ""
echo "🔍 步骤3: 验证安装..."
echo "检查RKNN工具包..."
python3 -c "import rknn_toolkit2; print(f'✅ RKNN Toolkit2 版本: {rknn_toolkit2.__version__}')" || echo "❌ RKNN Toolkit2未安装"

echo "检查关键依赖..."
python3 -c "import cv2; print(f'✅ OpenCV 版本: {cv2.__version__}')"
python3 -c "import torch; print(f'✅ PyTorch 版本: {torch.__version__}')"

echo "检查模型文件..."
ls -la models/best.pt && echo "✅ PyTorch模型存在"
ls -la rknn_models/best.rknn && echo "✅ RKNN模型存在" || echo "❌ RKNN模型不存在"

# 步骤4: 测试选项
echo ""
echo "🧪 步骤4: 选择测试方式..."
echo "请选择要测试的输入源:"
echo "1) 本地摄像头 (USB/CSI)"
echo "2) RTSP网络摄像头"
echo "3) 跳过测试，直接启动服务"
echo "4) 仅显示状态信息"

read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo "🎥 测试本地摄像头..."
        python3 detect_rknn.py --source 0 --weights rknn_models/best.rknn --conf 0.4 --img-size 416
        ;;
    2)
        echo "📡 测试RTSP摄像头..."
        echo "请输入RTSP地址 (回车使用默认):"
        read -p "[默认: rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/102]: " rtsp_url
        rtsp_url=${rtsp_url:-"rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/102"}
        python3 detect_rknn.py --source "$rtsp_url" --weights rknn_models/best.rknn --conf 0.5 --img-size 416
        ;;
    3)
        echo "⏭️  跳过测试"
        ;;
    4)
        echo "📊 显示系统状态"
        echo "系统信息:"
        uname -a
        echo "Python版本:"
        python3 --version
        echo "内存使用:"
        free -h
        echo "存储使用:"
        df -h .
        exit 0
        ;;
    *)
        echo "❌ 无效选项，跳过测试"
        ;;
esac

# 步骤5: 服务部署选项
echo ""
echo "⚙️  步骤5: 系统服务部署..."
echo "是否要安装为系统服务? (y/N)"
read -p "安装服务将在后台自动运行检测: " install_service

if [[ "$install_service" =~ ^[Yy]$ ]]; then
    echo "🔧 安装系统服务..."
    ./scripts/rk3588_manager.sh install
    echo "✅ 服务安装完成"
    
    echo "🚀 启动服务..."
    ./scripts/rk3588_manager.sh start
    
    echo "📊 服务状态:"
    ./scripts/rk3588_manager.sh status
fi

# 完成信息
echo ""
echo "🎉 部署完成!"
echo "============================================"
echo "📋 可用命令:"
echo "  测试摄像头:     python3 detect_rknn.py --source 0 --weights rknn_models/best.rknn"
echo "  测试RTSP:      python3 detect_rknn.py --source 'RTSP_URL' --weights rknn_models/best.rknn"
echo "  管理服务:       ./scripts/rk3588_manager.sh [start|stop|status|logs]"
echo "  系统监控:       ./scripts/rk3588_manager.sh monitor"
echo "  查看日志:       tail -f logs/detect.log"
echo ""
echo "🚀 系统已就绪，开始检测火烟吧！"