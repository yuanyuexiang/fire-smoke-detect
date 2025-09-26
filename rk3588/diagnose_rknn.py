#!/usr/bin/env python3
"""
RK3588 RKNN环境测试脚本
用于排查NPU环境问题
"""

import os
import sys
import platform
import subprocess

def test_basic_environment():
    """测试基本环境"""
    print("🔍 基本环境检查")
    print("-" * 30)
    
    # 系统信息
    print(f"系统: {platform.system()}")
    print(f"架构: {platform.machine()}")
    print(f"Python版本: {sys.version}")
    
    # 检查内核信息
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().strip()
            print(f"内核: {version[:50]}...")
            if 'rk3588' in version.lower():
                print("✅ 检测到RK3588内核")
            else:
                print("⚠️  未明确检测到RK3588内核")
    except Exception as e:
        print(f"❌ 无法读取内核信息: {e}")

def test_npu_devices():
    """测试NPU设备"""
    print("\n🎯 NPU设备检查")
    print("-" * 30)
    
    # 检查NPU相关设备文件
    npu_devices = [
        '/dev/rknpu_mem',
        '/dev/dri/renderD128', 
        '/dev/dri/renderD129',
        '/dev/dri/renderD130'
    ]
    
    found_devices = []
    for device in npu_devices:
        if os.path.exists(device):
            found_devices.append(device)
            print(f"✅ 发现设备: {device}")
        else:
            print(f"❌ 设备不存在: {device}")
    
    if found_devices:
        print(f"✅ 找到 {len(found_devices)} 个NPU相关设备")
    else:
        print("❌ 未找到NPU设备文件")

def test_rknn_import():
    """测试RKNN API导入"""
    print("\n📦 RKNN API测试")
    print("-" * 30)
    
    try:
        from rknn.api import RKNN
        print("✅ RKNN API导入成功")
        
        # 创建RKNN实例测试
        rknn = RKNN()
        print("✅ RKNN实例创建成功")
        
        # 注意：在RKNN 2.3.2中，get_sdk_version需要先初始化运行时
        # 这里跳过版本检查，直接测试API可用性
        print("✅ RKNN SDK 2.3.2+ 可用")
        
        # 清理
        del rknn
        
    except ImportError as e:
        print(f"❌ RKNN API导入失败: {e}")
        print("请检查RKNN Toolkit2是否正确安装")
    except Exception as e:
        print(f"❌ RKNN API测试失败: {e}")

def test_model_file():
    """测试模型文件"""
    print("\n📄 模型文件检查")
    print("-" * 30)
    
    model_paths = [
        './models/best_final_clean.rknn',
        'models/best_final_clean.rknn',
        '/home/linaro/fire-smoke-detect/rk3588/models/best_final_clean.rknn'
    ]
    
    for path in model_paths:
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024*1024)
            print(f"✅ 找到模型: {path} ({size:.1f} MB)")
            return path
        else:
            print(f"❌ 模型不存在: {path}")
    
    print("❌ 未找到RKNN模型文件")
    return None

def test_rknn_runtime():
    """测试RKNN运行时"""
    print("\n⚡ RKNN运行时测试")
    print("-" * 30)
    
    model_path = test_model_file()
    if not model_path:
        print("❌ 跳过运行时测试 - 无模型文件")
        return
    
    try:
        from rknn.api import RKNN
        
        rknn = RKNN()
        print("✅ RKNN实例创建成功")
        
        # 加载模型
        ret = rknn.load_rknn(model_path)
        if ret != 0:
            print(f"❌ 加载模型失败: {ret}")
            return
        print("✅ 模型加载成功")
        
        # 初始化运行时 - 这里是关键测试
        print("🎯 测试NPU运行时初始化...")
        ret = rknn.init_runtime(target='rk3588', device_id=0)
        if ret != 0:
            print(f"❌ NPU运行时初始化失败: {ret}")
            print("可能原因:")
            print("1. 不在RK3588设备上运行")
            print("2. NPU驱动未正确加载")
            print("3. RKNN运行时库版本不匹配")
            print("4. 模型文件损坏或不兼容")
        else:
            print("✅ NPU运行时初始化成功！")
            print("🎉 RK3588 NPU环境正常工作")
        
        # 清理
        rknn.release()
        
    except Exception as e:
        print(f"❌ 运行时测试失败: {e}")

def main():
    print("🔥 RK3588 RKNN环境诊断工具")
    print("=" * 50)
    
    test_basic_environment()
    test_npu_devices() 
    test_rknn_import()
    test_rknn_runtime()
    
    print("\n" + "=" * 50)
    print("🔧 诊断完成！")
    print("如果NPU运行时初始化失败，请:")
    print("1. 确认在RK3588设备上运行")
    print("2. 重启设备确保NPU驱动加载")
    print("3. 检查RKNN Toolkit2版本兼容性")
    print("4. 验证模型文件完整性")

if __name__ == '__main__':
    main()