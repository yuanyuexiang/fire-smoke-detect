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

#!/bin/bash

# RK3588 火烟检测系统快速启动脚本
# 使用预转换的RKNN模型，无需转换步骤

set -e

echo "🔥 RK3588 火烟检测系统 - 快速部署脚本 🔥"
echo "============================================"

# 检查系统
echo "� 检查系统环境..."
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

# 步骤2: 检查预转换模型
echo ""
echo "🔍 步骤2: 检查预转换的RKNN模型..."
if [[ -f "models/best_final_clean.rknn" ]]; then
    echo "✅ 找到RKNN模型: models/best_final_clean.rknn"
    ls -la models/best_final_clean.*
else
    echo "❌ 未找到RKNN模型文件，请检查部署"
    exit 1
fi

# 步骤3: 验证安装
echo ""
echo "🔍 步骤3: 验证安装..."
echo "检查关键依赖..."
python3 -c "import cv2; print(f'✅ OpenCV 版本: {cv2.__version__}')"

echo "检查RKNN运行时..."
python3 -c "from rknn.api import RKNN; print('✅ RKNN API 可用')" || echo "❌ RKNN API不可用"

echo "检查模型文件..."
if [[ -f "models/best_final_clean.rknn" ]]; then
    echo "✅ RKNN模型文件存在"
    du -h models/best_final_clean.*
else
    echo "❌ RKNN模型文件不存在"
    exit 1
fi

# 步骤4: 测试选项
echo ""
echo "🧪 步骤4: 选择测试方式..."
echo "请选择要测试的输入源:"
echo "1) 本地摄像头 (USB/CSI)"
echo "2) RTSP网络摄像头"
echo "3) RKNN环境诊断 (推荐先执行)"
echo "4) 跳过测试，直接启动服务"
echo "5) 仅显示状态信息"

read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo "🎥 测试本地摄像头..."
        python3 detect_rknn.py --source 0 --weights models/best_final_clean.rknn --conf 0.4 --img-size 640
        ;;
    2)
        echo "📡 测试RTSP摄像头..."
        echo "请输入RTSP地址 (回车使用默认):"
        read -p "[默认: rtsp://admin:sual116y@192.168.86.19:554/Streaming/Channels/102]: " rtsp_url
        rtsp_url=${rtsp_url:-"rtsp://admin:sual116y@192.168.86.19:554/Streaming/Channels/102"}
        python3 detect_rknn.py --source "$rtsp_url" --weights models/best_final_clean.rknn --conf 0.5 --img-size 640
        ;;
    3)
        echo "🔍 运行RKNN环境诊断..."
        python3 diagnose_rknn.py
        echo ""
        echo "如果诊断通过，可以继续测试检测功能"
        ;;
    4)
        echo "⏭️  跳过测试"
        ;;
    5)
        echo "📊 显示系统状态"
        echo "系统信息:"
        uname -a
        echo "Python版本:"
        python3 --version
        echo "内存使用:"
        free -h
        echo "存储使用:"
        df -h .
        echo "NPU设备检查:"
        ls -la /dev/rknpu* 2>/dev/null || echo "未找到NPU设备文件"
        ls -la /dev/dri/renderD* 2>/dev/null || echo "未找到DRI设备文件"
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