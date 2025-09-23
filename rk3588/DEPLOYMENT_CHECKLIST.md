# 🚀 RK3588 火烟检测系统 - 部署检查清单

## ✅ 文件清单验证

### 核心脚本文件 (5个)
- [x] `detect.py` - 原始YOLOv5检测脚本
- [x] `detect_rk3588.py` - RK3588优化检测脚本  
- [x] `convert_to_rknn.py` - PyTorch→RKNN转换脚本
- [x] `detect_rknn.py` - RKNN NPU推理脚本
- [x] `quick_start.sh` - 一键部署启动脚本

### 管理脚本文件 (3个)
- [x] `install.sh` - 环境自动安装脚本
- [x] `scripts/deploy_rk3588.sh` - 系统部署脚本
- [x] `scripts/rk3588_manager.sh` - 服务管理脚本

### 配置文件 (3个)
- [x] `requirements.txt` - Python依赖包配置
- [x] `config/fire-detect.service` - systemd服务配置
- [x] `README.md` - 详细部署说明文档

### 模型文件 (1个)
- [x] `models/best.pt` - 原始PyTorch模型文件

### 支持文件夹 (3个)
- [x] `utils/` - YOLOv5工具包
- [x] `yolov5_models/` - YOLOv5模型定义
- [x] `config/` - 配置文件目录

## 📋 部署步骤简要版

### 在PC端 (已完成)
```bash
# 1. 打包部署文件
cd /Users/yuanyuexiang/Desktop/workspace/fire-smoke-detect/
tar -czf rk3588-deploy.tar.gz rk3588/
```

### 在RK3588端 (待执行)
```bash
# 2. 传输并解压
scp rk3588-deploy.tar.gz root@RK3588_IP:~/
ssh root@RK3588_IP
tar -xzf rk3588-deploy.tar.gz
cd rk3588

# 3. 一键部署 (推荐)
./quick_start.sh

# 或者分步执行:
# 3a. 安装环境
./install.sh

# 3b. 转换模型
python3 convert_to_rknn.py --input models/best.pt --output rknn_models

# 3c. 测试运行
python3 detect_rknn.py --source 0 --weights rknn_models/best.rknn --conf 0.4

# 3d. 部署服务 (可选)
./scripts/rk3588_manager.sh install
./scripts/rk3588_manager.sh start
```

## 🎯 预期结果

### 性能指标
- **检测速度**: 15-30 FPS (NPU加速)
- **延迟**: 30-50ms (vs CPU的200-300ms)  
- **功耗**: 显著降低 (NPU vs CPU)
- **精度**: 99%+ (接近原始模型)

### 系统服务
- 开机自启动
- 后台自动检测
- 系统监控和日志
- 远程管理和控制

### 支持功能
- 本地摄像头检测
- RTSP网络摄像头
- 实时检测显示
- 结果保存和录制
- 多种输入源切换

## 🔧 快速验证命令

```bash
# 检查环境安装
python3 -c "import rknn_toolkit2; print('RKNN OK')"
python3 -c "import cv2; print('OpenCV OK')" 
python3 -c "import torch; print('PyTorch OK')"

# 检查模型转换
ls -la rknn_models/best.rknn

# 检查权限
ls -la *.sh scripts/*.sh

# 测试检测 (无显示)
python3 detect_rknn.py --source 0 --weights rknn_models/best.rknn --conf 0.4 --save-vid --nosave

# 查看服务状态
./scripts/rk3588_manager.sh status
```

## 📞 支持联系

如果遇到问题：
1. 查看 `README.md` 详细说明
2. 检查 `logs/` 目录下的日志文件  
3. 运行 `./scripts/rk3588_manager.sh monitor` 查看系统状态
4. 联系技术支持: QQ群 958083853

---

**🎉 部署包已准备就绪！现在可以将 `rk3588/` 整个文件夹复制到RK3588设备上开始部署了！**