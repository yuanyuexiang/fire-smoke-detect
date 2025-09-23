#!/usr/bin/env python3
"""
RKNN模型转换主脚本
专门用于在普通Ubuntu系统上转换YOLOv5模型为RKNN格式
"""

import os
import sys
import argparse
import logging
import torch
import numpy as np
from rknn.api import RKNN
import traceback
from datetime import datetime

# 设置日志
def setup_logging():
    """设置日志系统"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class YOLOv5ToRKNN:
    def __init__(self, verbose=True):
        """初始化转换器"""
        self.logger = setup_logging()
        self.rknn = RKNN(verbose=verbose)
        self.logger.info("RKNN Toolkit2 initialized")
        
    def load_pytorch_model(self, model_path):
        """加载PyTorch模型"""
        self.logger.info(f"Loading PyTorch model: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            device = torch.device('cpu')
            checkpoint = torch.load(model_path, map_location=device)
            
            if isinstance(checkpoint, dict):
                if 'model' in checkpoint:
                    model = checkpoint['model'].float()
                    self.logger.info("YOLOv5 training checkpoint detected")
                else:
                    model = checkpoint
                    self.logger.info("Standard PyTorch model detected")
            else:
                model = checkpoint
                self.logger.info("Direct model object detected")
            
            # 设置为评估模式
            if hasattr(model, 'eval'):
                model.eval()
            
            # 设置导出模式
            if hasattr(model, 'model'):
                for m in model.model.modules():
                    if hasattr(m, 'export'):
                        m.export = True
            else:
                for m in model.modules():
                    if hasattr(m, 'export'):
                        m.export = True
            
            self.logger.info("Model loaded and configured for export")
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
    
    def export_to_onnx(self, model, onnx_path, input_size=(1, 3, 640, 640)):
        """导出为ONNX格式"""
        self.logger.info(f"Exporting to ONNX: {onnx_path}")
        self.logger.info(f"Input size: {input_size}")
        
        try:
            # 创建输出目录
            os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
            
            # 创建示例输入
            dummy_input = torch.randn(input_size)
            
            # 导出ONNX
            with torch.no_grad():
                torch.onnx.export(
                    model,
                    dummy_input,
                    onnx_path,
                    export_params=True,
                    opset_version=11,
                    do_constant_folding=True,
                    input_names=['input'],
                    output_names=['output'],
                    dynamic_axes={
                        'input': {0: 'batch_size'},
                        'output': {0: 'batch_size'}
                    },
                    verbose=False
                )
            
            # 验证ONNX文件
            import onnx
            onnx_model = onnx.load(onnx_path)
            onnx.checker.check_model(onnx_model)
            
            file_size = os.path.getsize(onnx_path) / (1024 * 1024)
            self.logger.info(f"ONNX export successful: {file_size:.1f} MB")
            return True
            
        except Exception as e:
            self.logger.error(f"ONNX export failed: {e}")
            traceback.print_exc()
            return False
    
    def convert_to_rknn(self, onnx_path, rknn_path, input_size_list=[[1,3,640,640]], quantize=False):
        """转换ONNX为RKNN格式"""
        self.logger.info(f"Converting ONNX to RKNN: {onnx_path} -> {rknn_path}")
        
        try:
            # RKNN配置
            self.logger.info("Configuring RKNN conversion parameters...")
            ret = self.rknn.config(
                target_platform='rk3588',
                optimization_level=2,
                output_optimize=1,
                quantize_input_node=quantize,
                quantize_output_node=quantize,
                compress_weight=True
            )
            
            if ret != 0:
                raise RuntimeError("RKNN configuration failed")
            
            # 加载ONNX模型
            self.logger.info("Loading ONNX model...")
            ret = self.rknn.load_onnx(model=onnx_path)
            if ret != 0:
                raise RuntimeError("Failed to load ONNX model")
            
            # 构建RKNN模型
            self.logger.info("Building RKNN model...")
            if quantize:
                self.logger.info("Quantization enabled")
            
            ret = self.rknn.build(do_quantization=quantize)
            if ret != 0:
                raise RuntimeError("RKNN model build failed")
            
            # 导出RKNN模型
            self.logger.info("Exporting RKNN model...")
            os.makedirs(os.path.dirname(rknn_path), exist_ok=True)
            ret = self.rknn.export_rknn(rknn_path)
            if ret != 0:
                raise RuntimeError("RKNN model export failed")
            
            file_size = os.path.getsize(rknn_path) / (1024 * 1024)
            self.logger.info(f"RKNN export successful: {file_size:.1f} MB")
            
            # 简单验证
            self.logger.info("Performing basic validation...")
            ret = self.rknn.init_runtime()
            if ret == 0:
                # 创建测试输入
                input_data = [np.random.randint(0, 256, input_size_list[0], dtype=np.uint8)]
                outputs = self.rknn.inference(inputs=input_data)
                if outputs is not None:
                    self.logger.info(f"Validation passed - Output shapes: {[out.shape for out in outputs]}")
                else:
                    self.logger.warning("Validation failed - No outputs")
            else:
                self.logger.warning("Cannot initialize runtime (may not be on RK3588)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"RKNN conversion failed: {e}")
            traceback.print_exc()
            return False
        finally:
            self.rknn.release()
    
    def convert_full_pipeline(self, pytorch_path, output_dir, input_size=(1, 3, 640, 640), quantize=False):
        """完整的转换管道"""
        self.logger.info("="*60)
        self.logger.info("Starting YOLOv5 to RKNN conversion pipeline")
        self.logger.info(f"Input model: {pytorch_path}")
        self.logger.info(f"Output directory: {output_dir}")
        self.logger.info(f"Input size: {input_size}")
        self.logger.info(f"Quantization: {'Enabled' if quantize else 'Disabled'}")
        self.logger.info("="*60)
        
        try:
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件路径
            model_name = os.path.splitext(os.path.basename(pytorch_path))[0]
            onnx_path = os.path.join(output_dir, f"{model_name}.onnx")
            rknn_path = os.path.join(output_dir, f"{model_name}.rknn")
            
            # Step 1: 加载PyTorch模型
            self.logger.info("Step 1/3: Loading PyTorch model...")
            model = self.load_pytorch_model(pytorch_path)
            
            # Step 2: 转换为ONNX
            self.logger.info("Step 2/3: Converting to ONNX...")
            if not self.export_to_onnx(model, onnx_path, input_size):
                raise RuntimeError("ONNX conversion failed")
            
            # Step 3: 转换为RKNN
            self.logger.info("Step 3/3: Converting to RKNN...")
            if not self.convert_to_rknn(onnx_path, rknn_path, [list(input_size)], quantize):
                raise RuntimeError("RKNN conversion failed")
            
            # 成功总结
            self.logger.info("="*60)
            self.logger.info("🎉 CONVERSION COMPLETED SUCCESSFULLY!")
            self.logger.info("="*60)
            self.logger.info(f"✅ ONNX Model: {onnx_path}")
            self.logger.info(f"✅ RKNN Model: {rknn_path}")
            
            if os.path.exists(onnx_path):
                onnx_size = os.path.getsize(onnx_path) / (1024 * 1024)
                self.logger.info(f"📊 ONNX Size: {onnx_size:.1f} MB")
            
            if os.path.exists(rknn_path):
                rknn_size = os.path.getsize(rknn_path) / (1024 * 1024)
                self.logger.info(f"📊 RKNN Size: {rknn_size:.1f} MB")
            
            self.logger.info("📋 Next Steps:")
            self.logger.info(f"   1. Copy {rknn_path} to RK3588")
            self.logger.info("   2. Use RKNN model for NPU inference")
            self.logger.info("   3. Expected performance: 15-30 FPS on RK3588")
            
            return True
            
        except Exception as e:
            self.logger.error("="*60)
            self.logger.error("❌ CONVERSION FAILED!")
            self.logger.error("="*60)
            self.logger.error(f"Error: {e}")
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='YOLOv5 to RKNN Model Converter')
    parser.add_argument('--input', type=str, required=True, 
                       help='Input PyTorch model path (.pt file)')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for converted models')
    parser.add_argument('--input-size', type=int, default=640,
                       help='Input image size (default: 640)')
    parser.add_argument('--quantize', action='store_true',
                       help='Enable quantization for smaller model size')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # 验证输入文件
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)
    
    # 构造输入尺寸
    input_size = (1, 3, args.input_size, args.input_size)
    
    # 创建转换器
    converter = YOLOv5ToRKNN(verbose=args.verbose)
    
    # 开始转换
    success = converter.convert_full_pipeline(
        args.input, 
        args.output, 
        input_size, 
        args.quantize
    )
    
    if success:
        print("\n🎉 Model conversion completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Model conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()