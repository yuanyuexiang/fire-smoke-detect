#!/usr/bin/env python3
"""
RKNN输出格式调试脚本
用于理解模型输出的具体结构
"""

import cv2
import numpy as np
import os
from rknn.api import RKNN

def debug_rknn_output():
    """调试RKNN模型输出格式"""
    print("🔍 RKNN输出格式调试工具")
    print("=" * 40)
    
    model_path = "./models/best_final_clean.rknn"
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    # 初始化RKNN
    rknn = RKNN()
    
    try:
        # 加载模型
        print("📦 加载RKNN模型...")
        ret = rknn.load_rknn(model_path)
        if ret != 0:
            print("❌ 加载模型失败")
            return
        
        # 初始化运行时
        print("⚡ 初始化NPU运行时...")
        ret = rknn.init_runtime(target='rk3588', device_id=0)
        if ret != 0:
            print("❌ 初始化失败")
            return
        
        print("✅ 模型加载成功")
        
        # 创建测试输入
        print("🎯 创建测试输入...")
        test_input = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        # 推理
        print("🚀 执行推理...")
        outputs = rknn.inference(inputs=[test_input], data_format='nhwc')
        
        # 详细分析输出
        print("\n📊 输出分析:")
        print(f"   输出数量: {len(outputs)}")
        
        for i, output in enumerate(outputs):
            print(f"\n   输出{i}:")
            print(f"     类型: {type(output)}")
            print(f"     形状: {output.shape}")
            print(f"     数据类型: {output.dtype}")
            print(f"     最小值: {output.min():.6f}")
            print(f"     最大值: {output.max():.6f}")
            print(f"     平均值: {output.mean():.6f}")
            
            # 分析第一个输出的结构（通常是主要检测结果）
            if i == 0:
                print(f"   \n   详细结构分析 (输出{i}):")
                if len(output.shape) == 3:
                    batch, detections, features = output.shape
                    print(f"     Batch大小: {batch}")
                    print(f"     检测数量: {detections}")
                    print(f"     特征数量: {features}")
                    
                    if features >= 5:
                        print(f"\n     前5个检测的前10个特征:")
                        for det_idx in range(min(5, detections)):
                            det = output[0, det_idx, :min(10, features)]
                            print(f"       检测{det_idx}: {det}")
                            
                elif len(output.shape) == 2:
                    detections, features = output.shape
                    print(f"     检测数量: {detections}")
                    print(f"     特征数量: {features}")
                    
                    if features >= 5:
                        print(f"\n     前5个检测的前10个特征:")
                        for det_idx in range(min(5, detections)):
                            det = output[det_idx, :min(10, features)]
                            print(f"       检测{det_idx}: {det}")
                
                # 分析可能的置信度分布
                if len(output.shape) >= 2 and output.shape[-1] > 4:
                    confidence_col = output[..., 4] if len(output.shape) == 3 else output[:, 4]
                    print(f"\n     第5列(置信度)统计:")
                    print(f"       最小值: {confidence_col.min():.6f}")
                    print(f"       最大值: {confidence_col.max():.6f}")
                    print(f"       平均值: {confidence_col.mean():.6f}")
                    print(f"       大于0.1的数量: {(confidence_col > 0.1).sum()}")
                    print(f"       大于0.4的数量: {(confidence_col > 0.4).sum()}")
        
        print("\n🎯 推荐的后处理策略:")
        main_output = outputs[0]
        if len(main_output.shape) == 3:
            print("   - 输出是3D格式，需要取 output[0] 去掉batch维度")
        else:
            print("   - 输出是2D格式，直接处理")
            
        if main_output.shape[-1] >= 85:
            print("   - 特征数>=85，符合标准YOLOv5格式 (x,y,w,h,conf,class1,class2,...)")
        elif main_output.shape[-1] >= 7:
            print("   - 特征数>=7，可能是简化格式 (x,y,w,h,conf,class1,class2)")
        else:
            print(f"   - 特征数={main_output.shape[-1]}，需要进一步分析格式")
    
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        rknn.release()

if __name__ == '__main__':
    debug_rknn_output()