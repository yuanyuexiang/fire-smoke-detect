#!/usr/bin/env python3
"""
RK3588 RKNN模型转换脚本
将YOLOv5 PyTorch模型转换为RKNN格式以使用NPU加速
"""

import os
import sys
import torch
import numpy as np
from rknn.api import RKNN
import cv2

class RKNN_Model_Converter:
    def __init__(self):
        self.rknn = RKNN()
        
    def convert_pytorch_to_onnx(self, pytorch_model_path, onnx_model_path, input_size=(1, 3, 640, 640)):
        """将PyTorch模型转换为ONNX格式"""
        print(f"🔄 转换PyTorch模型到ONNX...")
        
        try:
            # 加载PyTorch模型
            model = torch.hub.load('ultralytics/yolov5', 'custom', path=pytorch_model_path)
            model.eval()
            
            # 创建示例输入
            dummy_input = torch.randn(input_size)
            
            # 导出ONNX
            torch.onnx.export(
                model,
                dummy_input,
                onnx_model_path,
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={
                    'input': {0: 'batch_size'},
                    'output': {0: 'batch_size'}
                }
            )
            print(f"✅ ONNX模型保存到: {onnx_model_path}")
            return True
        except Exception as e:
            print(f"❌ ONNX转换失败: {e}")
            return False
    
    def convert_onnx_to_rknn(self, onnx_model_path, rknn_model_path, quantize=True):
        """将ONNX模型转换为RKNN格式"""
        print(f"🔄 转换ONNX模型到RKNN...")
        
        try:
            # 配置RKNN
            print('--> 配置模型')
            self.rknn.config(
                mean_values=[[0, 0, 0]],
                std_values=[[255, 255, 255]],
                target_platform='rk3588',
                quantized_algorithm='normal',
                quantized_method='channel' if quantize else None,
                optimization_level=3
            )
            print('配置完成')
            
            # 加载ONNX模型
            print('--> 加载ONNX模型')
            ret = self.rknn.load_onnx(model=onnx_model_path)
            if ret != 0:
                print('加载ONNX模型失败！')
                return False
            print('加载完成')
            
            # 构建模型
            print('--> 构建模型')
            ret = self.rknn.build(do_quantization=quantize)
            if ret != 0:
                print('构建模型失败！')
                return False
            print('构建完成')
            
            # 导出RKNN模型
            print(f'--> 导出RKNN模型到 {rknn_model_path}')
            ret = self.rknn.export_rknn(rknn_model_path)
            if ret != 0:
                print('导出RKNN模型失败！')
                return False
            print('导出完成')
            
            return True
        except Exception as e:
            print(f"❌ RKNN转换失败: {e}")
            return False
    
    def test_rknn_model(self, rknn_model_path, test_image_path):
        """测试RKNN模型推理"""
        print(f"🧪 测试RKNN模型...")
        
        try:
            # 初始化运行时环境
            print('--> 初始化运行时环境')
            ret = self.rknn.init_runtime()
            if ret != 0:
                print('初始化运行时环境失败')
                return False
            print('运行时环境初始化成功')
            
            # 加载测试图像
            if os.path.exists(test_image_path):
                img = cv2.imread(test_image_path)
                img = cv2.resize(img, (640, 640))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # 推理
                print('--> 执行推理')
                outputs = self.rknn.inference(inputs=[img])
                print(f'推理输出形状: {[output.shape for output in outputs]}')
                print('✅ RKNN模型测试成功')
                return True
            else:
                print(f'测试图像不存在: {test_image_path}')
                return False
                
        except Exception as e:
            print(f"❌ RKNN模型测试失败: {e}")
            return False
    
    def convert_complete_pipeline(self, pytorch_model_path, output_dir="./rknn_models"):
        """完整的转换流程"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        model_name = os.path.splitext(os.path.basename(pytorch_model_path))[0]
        onnx_path = os.path.join(output_dir, f"{model_name}.onnx")
        rknn_path = os.path.join(output_dir, f"{model_name}.rknn")
        
        print("🚀 开始完整的模型转换流程")
        print(f"输入: {pytorch_model_path}")
        print(f"输出目录: {output_dir}")
        print("-" * 50)
        
        # 步骤1: PyTorch -> ONNX
        if not os.path.exists(onnx_path):
            if not self.convert_pytorch_to_onnx(pytorch_model_path, onnx_path):
                return False
        else:
            print(f"✅ ONNX模型已存在: {onnx_path}")
        
        # 步骤2: ONNX -> RKNN
        if not os.path.exists(rknn_path):
            if not self.convert_onnx_to_rknn(onnx_path, rknn_path):
                return False
        else:
            print(f"✅ RKNN模型已存在: {rknn_path}")
        
        print("🎉 模型转换完成！")
        print(f"ONNX模型: {onnx_path}")
        print(f"RKNN模型: {rknn_path}")
        
        return True
    
    def __del__(self):
        if hasattr(self, 'rknn'):
            self.rknn.release()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RK3588 RKNN模型转换工具')
    parser.add_argument('--input', type=str, default='./best.pt', help='输入PyTorch模型路径')
    parser.add_argument('--output', type=str, default='./rknn_models', help='输出目录')
    parser.add_argument('--test-image', type=str, help='测试图像路径（可选）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ 输入模型文件不存在: {args.input}")
        sys.exit(1)
    
    # 创建转换器
    converter = RKNN_Model_Converter()
    
    # 执行转换
    success = converter.convert_complete_pipeline(args.input, args.output)
    
    if success and args.test_image:
        # 测试模型
        model_name = os.path.splitext(os.path.basename(args.input))[0]
        rknn_path = os.path.join(args.output, f"{model_name}.rknn")
        converter.test_rknn_model(rknn_path, args.test_image)
    
    if success:
        print("\n✅ 转换完成！现在可以使用RKNN模型进行NPU加速推理了")
        print("\n使用方法:")
        model_name = os.path.splitext(os.path.basename(args.input))[0]
        rknn_path = os.path.join(args.output, f"{model_name}.rknn")
        print(f"python3 detect_rknn.py --source 0 --weights {rknn_path}")
    else:
        print("❌ 转换失败")
        sys.exit(1)

if __name__ == '__main__':
    main()