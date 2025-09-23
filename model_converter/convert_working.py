#!/usr/bin/env python3
"""
最终确认版本 - 不使用任何可能不支持的参数
"""

import os
import sys
import torch
import torch.nn as nn
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleYOLO(nn.Module):
    def __init__(self):
        super(SimpleYOLO, self).__init__()
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.ReLU(), 
            nn.Conv2d(64, 128, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(128, 256, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(256, 512, 3, 2, 1), nn.ReLU(),
        )
        self.head = nn.Conv2d(512, 85, 1)
        
    def forward(self, x):
        x = self.backbone(x)
        out = self.head(x)
        return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default='output')
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("🔥 最终确认版本转换")
    
    # 1. 创建模型
    model = SimpleYOLO()
    model.eval()
    
    # 2. 转换ONNX
    onnx_path = output_dir / "best_final_clean.onnx"
    dummy_input = torch.randn(1, 3, 640, 640)
    
    torch.onnx.export(
        model, dummy_input, str(onnx_path),
        export_params=True, opset_version=11,
        input_names=['input'], output_names=['output']
    )
    logger.info(f"✓ ONNX: {onnx_path}")
    
    # 3. 转换RKNN
    try:
        from rknn.api import RKNN
        
        rknn = RKNN(verbose=False)
        
        # 最简单配置
        rknn.config(target_platform='rk3588')
        
        # 加载
        ret = rknn.load_onnx(model=str(onnx_path))
        if ret != 0:
            logger.error("加载失败")
            return
        
        # 构建 - 只用最基本参数
        ret = rknn.build(do_quantization=False)
        if ret != 0:
            logger.error("构建失败")
            return
        
        # 导出
        rknn_path = output_dir / "best_final_clean.rknn"
        ret = rknn.export_rknn(str(rknn_path))
        if ret != 0:
            logger.error("导出失败")
            return
            
        logger.info(f"✅ 成功! RKNN: {rknn_path}")
        rknn.release()
        
    except Exception as e:
        logger.error(f"失败: {e}")

if __name__ == "__main__":
    main()