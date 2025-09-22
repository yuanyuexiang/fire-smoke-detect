#!/bin/bash
# RK3588火灾检测系统管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="fire-detect"
VENV_PATH="~/fire-detect-env"
PROJECT_PATH="~/fire-smoke-detect"

show_usage() {
    echo "🔥 RK3588火灾检测系统管理脚本"
    echo "================================="
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  install     - 安装系统和依赖"
    echo "  convert     - 转换模型为RKNN格式"
    echo "  start       - 启动检测服务"
    echo "  stop        - 停止检测服务"
    echo "  restart     - 重启检测服务"
    echo "  status      - 查看服务状态"
    echo "  logs        - 查看日志"
    echo "  test        - 测试摄像头检测"
    echo "  test-rknn   - 测试NPU加速检测"
    echo "  test-rtsp   - 测试RTSP检测"
    echo "  monitor     - 监控系统资源"
    echo "  config      - 编辑配置"
    echo "  uninstall   - 卸载服务"
}

install_system() {
    echo "🚀 开始安装RK3588火灾检测系统..."
    
    # 运行部署脚本
    if [ -f "$SCRIPT_DIR/deploy_rk3588.sh" ]; then
        bash "$SCRIPT_DIR/deploy_rk3588.sh"
    else
        echo "❌ 部署脚本不存在"
        exit 1
    fi
    
    # 安装服务
    if [ -f "$SCRIPT_DIR/fire-detect.service" ]; then
        sudo cp "$SCRIPT_DIR/fire-detect.service" /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable $SERVICE_NAME
        echo "✅ 系统服务安装完成"
    fi
    
    echo ""
    echo "🚀 接下来的步骤："
    echo "1. 转换模型: $0 convert"
    echo "2. 启动服务: $0 start"
}

convert_model() {
    echo "🔄 转换PyTorch模型为RKNN格式..."
    source $VENV_PATH/bin/activate
    cd $PROJECT_PATH/yolov5
    
    if [ ! -f "./best.pt" ]; then
        echo "❌ PyTorch模型文件 best.pt 不存在"
        echo "请先将模型文件放到 $PROJECT_PATH/yolov5/ 目录下"
        return 1
    fi
    
    # 安装RKNN工具包（如果还没安装）
    if ! python3 -c "import rknn.api" 2>/dev/null; then
        echo "📦 安装RKNN工具包..."
        # 检查架构
        ARCH=$(uname -m)
        if [ "$ARCH" = "aarch64" ]; then
            echo "检测到ARM64架构，安装RKNN Toolkit2..."
            pip3 install https://github.com/rockchip-linux/rknn-toolkit2/releases/download/v1.5.2/rknn_toolkit2-1.5.2+b642f30c-cp38-cp38-linux_aarch64.whl
        else
            echo "❌ 不支持的架构: $ARCH"
            echo "RKNN只支持ARM64 (aarch64) 架构"
            return 1
        fi
    fi
    
    # 执行转换
    python3 convert_to_rknn.py --input ./best.pt --output ./rknn_models
    
    if [ $? -eq 0 ]; then
        echo "✅ 模型转换完成！"
        echo "RKNN模型保存在: $PROJECT_PATH/yolov5/rknn_models/"
        echo ""
        echo "🧪 测试RKNN模型:"
        echo "$0 test-rknn"
    else
        echo "❌ 模型转换失败"
        return 1
    fi
}

start_service() {
    echo "🟢 启动火灾检测服务..."
    sudo systemctl start $SERVICE_NAME
    sudo systemctl status $SERVICE_NAME --no-pager -l
}

stop_service() {
    echo "🔴 停止火灾检测服务..."
    sudo systemctl stop $SERVICE_NAME
}

restart_service() {
    echo "🔄 重启火灾检测服务..."
    sudo systemctl restart $SERVICE_NAME
    sudo systemctl status $SERVICE_NAME --no-pager -l
}

show_status() {
    echo "📊 服务状态:"
    sudo systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    echo "🔧 系统资源:"
    echo "CPU使用率:"
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
    echo "内存使用:"
    free -h
    echo "温度信息:"
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        echo "CPU温度: $((temp/1000))°C"
    fi
}

show_logs() {
    echo "📝 查看最近日志 (Ctrl+C退出):"
    sudo journalctl -u $SERVICE_NAME -f
}

test_camera() {
    echo "📷 测试本地摄像头检测（CPU推理）..."
    source $VENV_PATH/bin/activate
    cd $PROJECT_PATH/yolov5
    python3 detect_rk3588.py --source 0 --weights ./best.pt --img-size 416 --conf 0.4 --view-img
}

test_rknn() {
    echo "🚀 测试NPU加速检测..."
    source $VENV_PATH/bin/activate
    cd $PROJECT_PATH/yolov5
    
    if [ ! -f "./rknn_models/best.rknn" ]; then
        echo "❌ RKNN模型不存在，请先转换模型:"
        echo "$0 convert"
        return 1
    fi
    
    python3 detect_rknn.py --source 0 --weights ./rknn_models/best.rknn --conf 0.4
}

test_rtsp() {
    echo "📹 测试RTSP摄像头检测..."
    echo "请输入RTSP地址:"
    read -r rtsp_url
    if [ -n "$rtsp_url" ]; then
        source $VENV_PATH/bin/activate
        cd $PROJECT_PATH/yolov5
        python3 detect_rk3588.py --source "$rtsp_url" --weights ./best.pt --img-size 416 --conf 0.4 --view-img
    fi
}

monitor_system() {
    echo "📊 系统监控 (Ctrl+C退出)..."
    watch -n 2 '
    echo "=== RK3588火灾检测系统监控 ==="
    echo "时间: $(date)"
    echo ""
    echo "服务状态:"
    systemctl is-active fire-detect
    echo ""
    echo "CPU使用率:"
    top -bn1 | grep "Cpu(s)" | awk "{print \$2}" | cut -d"%" -f1
    echo ""
    echo "内存使用:"
    free -h | grep Mem
    echo ""
    echo "磁盘使用:"
    df -h / | tail -1
    echo ""
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        echo "CPU温度: $((temp/1000))°C"
    fi
    echo ""
    echo "最近检测日志:"
    journalctl -u fire-detect --since "1 minute ago" --no-pager -q | tail -5
    '
}

edit_config() {
    echo "⚙️  编辑配置文件..."
    if [ -f /etc/systemd/system/$SERVICE_NAME.service ]; then
        sudo nano /etc/systemd/system/$SERVICE_NAME.service
        echo "配置修改后需要重新加载:"
        echo "sudo systemctl daemon-reload"
        echo "sudo systemctl restart $SERVICE_NAME"
    else
        echo "❌ 服务配置文件不存在"
    fi
}

uninstall_service() {
    echo "🗑️  卸载火灾检测服务..."
    sudo systemctl stop $SERVICE_NAME 2>/dev/null
    sudo systemctl disable $SERVICE_NAME 2>/dev/null
    sudo rm -f /etc/systemd/system/$SERVICE_NAME.service
    sudo systemctl daemon-reload
    echo "✅ 服务卸载完成"
}

# 主程序
case "$1" in
    install)
        install_system
        ;;
    convert)
        convert_model
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_camera
        ;;
    test-rknn)
        test_rknn
        ;;
    test-rtsp)
        test_rtsp
        ;;
    monitor)
        monitor_system
        ;;
    config)
        edit_config
        ;;
    uninstall)
        uninstall_service
        ;;
    *)
        show_usage
        ;;
esac