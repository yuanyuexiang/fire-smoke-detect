# 🚀 RK3588 快速部署指南

## 📋 部署前准备

本版本包含**预转换的RKNN模型**，无需在RK3588上进行模型转换，可直接部署使用。

## 🎯 模型文件说明

- `models/best_final_clean.rknn` - 主要的NPU加速模型 (约5MB)
- `models/best_final_clean.onnx` - ONNX格式备用 (约14MB)

## 🚀 快速部署步骤

### 1. 复制文件夹到RK3588
```bash
# 将整个rk3588文件夹复制到设备
scp -r rk3588/ linaro@RK3588_IP:~/fire-smoke-detect/
```

### 2. SSH登录设备并运行
```bash
ssh linaro@RK3588_IP
cd ~/fire-smoke-detect/
chmod +x *.sh
./quick_start.sh
```

### 3. 选择测试方式
- 选项1: USB摄像头测试
- 选项2: RTSP网络摄像头测试  
- 选项3: 跳过测试，直接启动服务

## ✅ 预期结果

- 🔥 实时火焰检测
- 💨 实时烟雾检测
- ⚡ NPU加速推理 (约30-60 FPS)
- 📊 实时FPS显示

## 🔧 故障排除

如果遇到问题，检查：
1. 模型文件是否完整复制
2. RKNN运行时是否正确安装
3. 摄像头权限是否正确

## 📈 性能优化

- 模型已针对RK3588 NPU优化
- 使用640x640输入分辨率，平衡精度和速度
- 支持多线程处理，提升整体性能