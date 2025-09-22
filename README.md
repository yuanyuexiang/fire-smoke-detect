## fire-smoke-detect-yolov4-v5 and fire-smoke-detect-dataset

* author is leilei
* [**README_ZN 中文版说明**](./readmes/README_ZN.md)
* [**README_EN English Description**](./readmes/README_EN.md)
* [**yolov4 tensorrt python inference**](https://github.com/gengyanlei/onnx2tensorRt)
* [**Note: 百度Paddle智慧城市生态使用本人烟火检测数据集(PS:明明是我的数据还要感谢别人一下)**](https://github.com/PaddlePaddle/awesome-DeepLearning/tree/master/Paddle_Industry_Practice_Sample_Library/Fire_and_Smoke_Detection)

* This repository code has stopped updating, please use the dataset to retrain the detection model directly!
* This repository code has stopped updating, please use the dataset to retrain the detection model directly!
* This repository code has stopped updating, please use the dataset to retrain the detection model directly!

### fire-smoke-detect-demo
|![fire-smoke-detect-demo](./result/result_demo.jpg)|
|----|

### Data Label Tool
+ [CVAT](https://github.com/openvinotoolkit/cvat)
+ [CVAT-Tutorial](https://blog.csdn.net/LEILEI18A/article/details/113385510)

### Other
* [leilei's blog](https://blog.csdn.net/LEILEI18A/article/details/107334474)
* [VSCode Remote SSH 安装教程](https://blog.csdn.net/LEILEI18A/article/details/102524181)
* [segmentation_pytorch 语义分割](https://github.com/gengyanlei/segmentation_pytorch)
* [building-segmentation-dataset 遥感影像建筑语义分割](https://github.com/gengyanlei/build_segmentation_dataset)
* [reflective-clothes-detect-dataset 安全帽反光衣检测](https://github.com/gengyanlei/reflective-clothes-detect)


## YOLOv5 检测使用方法

### 本地摄像头检测
```bash
cd /Users/yuanyuexiang/Desktop/workspace/fire-smoke-detect/yolov5 && python3 detect.py --source 0 --weights ./best.pt --device cpu --view-img --conf 0.4
```

### RTSP网络摄像头检测
```bash
# 海康威视摄像头 - 多种路径格式
# 主码流
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/1" --weights ./best.pt --device cpu --view-img --conf 0.5

# 子码流 (当前使用)
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/102" --weights ./best.pt --device cpu --view-img --conf 0.5

# 备用路径1
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/h264/ch1/main/av_stream" --weights ./best.pt --device cpu --view-img --conf 0.5

# 备用路径2
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/cam1/mpeg4" --weights ./best.pt --device cpu --view-img --conf 0.5

# 大华摄像头
python3 detect.py --source "rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0" --weights ./best.pt --device cpu --view-img --conf 0.4

# 通用RTSP摄像头
python3 detect.py --source "rtsp://admin:123456@192.168.1.100:554/stream1" --weights ./best.pt --device cpu --view-img --conf 0.4
```

### 视频文件检测
```bash
python3 detect.py --source ../result/fire1.mp4 --weights ./best.pt --device cpu --conf 0.4
```

### 参数说明
- `--source`: 输入源（0=摄像头, RTSP地址, 视频文件路径）
- `--weights`: 模型权重文件
- `--device`: 设备选择（cpu/cuda）
- `--view-img`: 显示检测窗口
- `--conf`: 置信度阈值（0.1-1.0）
- `--img-size`: 输入图像大小（默认640）

## RK3588部署指南

### RK3588环境准备
```bash
# 系统要求：Ubuntu 20.04/22.04 或 Debian 11
# Python 3.8+

# 安装基础依赖
sudo apt update
sudo apt install -y python3-pip python3-dev cmake build-essential
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y ffmpeg v4l-utils

# 安装Python依赖
pip3 install numpy pillow pyyaml tqdm matplotlib seaborn pandas
```

### RK3588优化版本
```bash
# RK3588专用命令（CPU优化）
python3 detect.py --source 0 --weights ./best.pt --device cpu --img-size 416 --conf 0.4

# RTSP摄像头（RK3588优化）
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/102" --weights ./best.pt --device cpu --img-size 416 --conf 0.5 --half

# 无GUI版本（适合SSH连接）
python3 detect.py --source 0 --weights ./best.pt --device cpu --img-size 416 --conf 0.4 --save-vid --nosave
```

### 性能优化建议
- **图像尺寸**: 使用416x416而不是640x640，提升推理速度
- **半精度**: 添加`--half`参数启用FP16推理
- **无显示模式**: 去掉`--view-img`减少GPU负担
- **批处理**: 设置合适的batch size

### RKNN加速（推荐，性能提升5-10倍）
```bash
# 安装RKNN工具包 (在RK3588上操作)
# 1. 下载RKNN Toolkit2
wget https://github.com/rockchip-linux/rknn-toolkit2/releases/download/v1.5.2/rknn_toolkit2-1.5.2+b642f30c-cp38-cp38-linux_aarch64.whl
pip3 install rknn_toolkit2-1.5.2+b642f30c-cp38-cp38-linux_aarch64.whl

# 2. 转换PyTorch模型为RKNN格式（NPU加速）
python3 convert_to_rknn.py --input ./best.pt --output ./rknn_models

# 3. 使用RKNN模型进行NPU加速推理（比CPU快5-10倍）
python3 detect_rknn.py --source 0 --weights ./rknn_models/best.rknn --conf 0.4

# 4. RTSP摄像头 + NPU加速
python3 detect_rknn.py --source "rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/102" --weights ./rknn_models/best.rknn --conf 0.5

# 5. 无GUI版本（适合SSH连接）+ NPU加速
python3 detect_rknn.py --source 0 --weights ./rknn_models/best.rknn --conf 0.4 --save-vid --no-display
```

### 性能对比
| 推理方式 | FPS | 功耗 | 延迟 |
|---------|-----|------|------|
| CPU推理 | 3-5 | 高 | 200-300ms |
| NPU推理 | 15-30 | 低 | 30-50ms |

### 模型转换流程
```bash
# 完整转换流程：PyTorch → ONNX → RKNN
# 1. 转换模型（一次性操作）
python3 convert_to_rknn.py --input ./best.pt --output ./rknn_models --test-image ../result/test_image.jpg

# 2. 验证RKNN模型
python3 detect_rknn.py --source ../result/fire1.mp4 --weights ./rknn_models/best.rknn --conf 0.4
```

### 快速部署到RK3588
```bash
# 1. 上传项目文件到RK3588
scp -r fire-smoke-detect/ root@RK3588_IP:~/

# 2. SSH连接到RK3588
ssh root@RK3588_IP

# 3. 运行自动部署脚本
cd ~/fire-smoke-detect
chmod +x deploy_rk3588.sh rk3588_manager.sh
./rk3588_manager.sh install

# 4. 启动检测服务
./rk3588_manager.sh start

# 5. 查看运行状态
./rk3588_manager.sh status
```

### RK3588管理命令
```bash
# 系统管理
./rk3588_manager.sh start      # 启动服务
./rk3588_manager.sh stop       # 停止服务  
./rk3588_manager.sh restart    # 重启服务
./rk3588_manager.sh status     # 查看状态
./rk3588_manager.sh logs       # 查看日志
./rk3588_manager.sh monitor    # 系统监控

# 测试功能
./rk3588_manager.sh test       # 测试本地摄像头
./rk3588_manager.sh test-rtsp  # 测试RTSP摄像头

# 配置管理
./rk3588_manager.sh config     # 编辑配置
./rk3588_manager.sh uninstall  # 卸载服务
```

### 性能调优建议
- **CPU绑定**: 使用`taskset`将进程绑定到特定CPU核心
- **内存优化**: 设置合适的缓冲区大小，避免内存泄漏  
- **温度监控**: 定期检查CPU温度，必要时增加散热
- **存储优化**: 使用高速存储设备，定期清理日志文件