#!/usr/bin/env python3
"""
智能火灾检测启动脚本
自动选择最佳可用的模型格式和推理方式
"""

import os
import sys
import subprocess

def check_rknn_available():
    """检查RKNN是否可用"""
    try:
        from rknn.api import RKNN
        return True
    except ImportError:
        return False

def check_onnx_available():
    """检查ONNX Runtime是否可用"""
    try:
        import onnxruntime
        return True
    except ImportError:
        return False

def check_pytorch_available():
    """检查PyTorch是否可用"""
    try:
        import torch
        return True
    except ImportError:
        return False

def find_best_model():
    """查找最佳可用模型"""
    model_priority = [
        ("RKNN", "./models/best_final_clean.rknn", "detect_rknn.py"),
        ("ONNX", "./models/best_final_clean.onnx", "detect_onnx.py"),
        ("ONNX", "./models/best.onnx", "detect_onnx.py"),
        ("PyTorch", "../yolov5/best.pt", "detect_pytorch.py"),
    ]
    
    for model_type, model_path, script in model_priority:
        if os.path.exists(model_path):
            return model_type, model_path, script
    
    return None, None, None

def main():
    print("🔥 智能火灾检测系统 - 自动模式")
    print("=" * 50)
    
    # 检查可用的推理框架
    print("🔍 检查推理环境...")
    rknn_available = check_rknn_available()
    onnx_available = check_onnx_available()
    pytorch_available = check_pytorch_available()
    
    print(f"   RKNN (NPU):    {'✅' if rknn_available else '❌'}")
    print(f"   ONNX (CPU):    {'✅' if onnx_available else '❌'}")
    print(f"   PyTorch (CPU): {'✅' if pytorch_available else '❌'}")
    
    # 查找最佳模型
    print("\n📁 搜索可用模型...")
    model_type, model_path, script_name = find_best_model()
    
    if model_type is None:
        print("❌ 未找到任何可用模型！")
        print("\n💡 可用模型路径:")
        print("   RKNN: ./models/best_final_clean.rknn")
        print("   ONNX: ./models/best_final_clean.onnx 或 ./models/best.onnx")
        print("   PyTorch: ../yolov5/best.pt")
        return
    
    print(f"✅ 找到模型: {model_type} - {model_path}")
    
    # 检查对应的推理框架是否可用
    if model_type == "RKNN" and not rknn_available:
        print("❌ RKNN模型存在但RKNN框架不可用")
        # 尝试ONNX备选
        if os.path.exists("./models/best_final_clean.onnx") and onnx_available:
            model_type = "ONNX"
            model_path = "./models/best_final_clean.onnx"
            script_name = "detect_onnx.py"
            print(f"🔄 切换到备选: {model_type} - {model_path}")
        else:
            print("❌ 没有可用的备选方案")
            return
    
    elif model_type == "ONNX" and not onnx_available:
        print("❌ ONNX模型存在但ONNXRuntime不可用")
        print("💡 请安装: pip3 install onnxruntime")
        return
        
    elif model_type == "PyTorch" and not pytorch_available:
        print("❌ PyTorch模型存在但PyTorch不可用")
        return
    
    # 推荐性能说明
    print(f"\n🎯 使用 {model_type} 推理:")
    if model_type == "RKNN":
        print("   性能: ⭐⭐⭐⭐⭐ (NPU加速，30-60 FPS)")
        print("   功耗: 低")
    elif model_type == "ONNX":
        print("   性能: ⭐⭐⭐ (CPU推理，5-15 FPS)")  
        print("   功耗: 中等")
    elif model_type == "PyTorch":
        print("   性能: ⭐⭐ (CPU推理，2-5 FPS)")
        print("   功耗: 较高")
    
    # 构建启动命令
    if not os.path.exists(script_name):
        print(f"❌ 检测脚本不存在: {script_name}")
        return
    
    # 获取命令行参数
    import sys
    args = sys.argv[1:]  # 移除脚本名称
    
    # 默认参数
    if not any('--source' in arg for arg in args):
        args.extend(['--source', 'rtsp://admin:sual116y@192.168.86.19:554/Streaming/Channels/102'])
    
    if not any('--conf' in arg for arg in args):
        args.extend(['--conf', '0.4'])
    
    if not any('--weights' in arg for arg in args):
        args.extend(['--weights', model_path])
    
    # 启动检测
    cmd = ['python3', script_name] + args
    print(f"\n🚀 启动命令: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️  检测中断")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == '__main__':
    main()