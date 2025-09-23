#!/bin/bash

# RK3588部署包打包脚本
# 将整个部署包打包为便于传输的压缩文件

echo "📦 打包RK3588部署文件..."

cd /Users/yuanyuexiang/Desktop/workspace/fire-smoke-detect/

# 创建压缩包
tar -czf rk3588-fire-smoke-detect-$(date +%Y%m%d-%H%M).tar.gz rk3588/

echo "✅ 打包完成！"
echo "📁 文件位置: $(pwd)/rk3588-fire-smoke-detect-$(date +%Y%m%d-%H%M).tar.gz"
echo ""
echo "📋 下一步操作:"
echo "1. 传输到RK3588: scp rk3588-fire-smoke-detect-*.tar.gz root@RK3588_IP:~/"
echo "2. 在RK3588上解压: tar -xzf rk3588-fire-smoke-detect-*.tar.gz"
echo "3. 运行部署: cd rk3588 && ./quick_start.sh"
echo ""
echo "🎯 预期性能: 15-30 FPS NPU加速检测"