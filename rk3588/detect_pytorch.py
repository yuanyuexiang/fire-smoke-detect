#!/usr/bin/env python3
"""
火灾烟雾检测 - PyTorch版本
支持YOLOv5 .pt模型格式，CPU推理
"""

import argparse
import time
import cv2
import numpy as np
from pathlib import Path

def check_pytorch():
    """检查PyTorch是否可用"""
    try:
        import torch
        return True, torch.__version__
    except ImportError:
        return False, None

def load_model(weights):
    """加载PyTorch模型"""
    try:
        import torch
        
        # 加载模型
        model = torch.hub.load('.', 'custom', path=weights, source='local', force_reload=True)
        model.conf = 0.4  # 置信度阈值
        model.iou = 0.45  # NMS IOU阈值
        
        print(f"✅ 成功加载PyTorch模型: {weights}")
        print(f"📊 模型类别: {model.names}")
        return model
        
    except Exception as e:
        print(f"❌ 加载模型失败: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default='0', help='输入源')
    parser.add_argument('--weights', type=str, required=True, help='模型权重路径')
    parser.add_argument('--conf', type=float, default=0.4, help='置信度阈值')
    parser.add_argument('--show', action='store_true', help='显示结果')
    parser.add_argument('--save', action='store_true', help='保存结果')
    args = parser.parse_args()

    print("🔥 火灾检测系统 - PyTorch版本")
    print("=" * 50)

    # 检查PyTorch
    pytorch_ok, version = check_pytorch()
    if not pytorch_ok:
        print("❌ PyTorch未安装")
        print("💡 安装命令: pip3 install torch torchvision")
        return

    print(f"✅ PyTorch版本: {version}")

    # 加载模型
    model = load_model(args.weights)
    if model is None:
        return

    # 设置置信度
    model.conf = args.conf

    # 打开视频源
    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        print(f"❌ 无法打开视频源: {args.source}")
        return

    print(f"✅ 视频源已连接: {args.source}")

    # 检测循环
    frame_count = 0
    fps_counter = 0
    fps_start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️  无法读取帧")
                break

            frame_count += 1
            
            # YOLOv5推理
            start_time = time.time()
            results = model(frame)
            inference_time = time.time() - start_time

            # 解析结果
            detections = results.pandas().xyxy[0]
            
            # 绘制检测框
            annotated_frame = frame.copy()
            fire_count = 0
            smoke_count = 0
            
            for _, detection in detections.iterrows():
                x1, y1, x2, y2 = map(int, [detection['xmin'], detection['ymin'], 
                                          detection['xmax'], detection['ymax']])
                conf = detection['confidence']
                class_name = detection['name']
                
                if class_name == 'fire':
                    color = (0, 0, 255)  # 红色
                    fire_count += 1
                elif class_name == 'smoke':
                    color = (128, 128, 128)  # 灰色
                    smoke_count += 1
                else:
                    continue
                
                # 绘制边界框
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                # 绘制标签
                label = f"{class_name}: {conf:.2f}"
                cv2.putText(annotated_frame, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # 计算FPS
            fps_counter += 1
            if time.time() - fps_start_time >= 1.0:
                fps = fps_counter / (time.time() - fps_start_time)
                fps_counter = 0
                fps_start_time = time.time()
                
                # 打印状态
                print(f"帧{frame_count:6d} | "
                      f"推理: {inference_time*1000:5.1f}ms | "
                      f"FPS: {fps:4.1f} | "
                      f"火灾: {fire_count} | "
                      f"烟雾: {smoke_count}")

            # 显示结果
            if args.show:
                # 添加信息文本
                info_text = f"PyTorch CPU | FPS: {fps:.1f} | Fire: {fire_count} | Smoke: {smoke_count}"
                cv2.putText(annotated_frame, info_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('火灾检测', annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # 保存结果（可选）
            if args.save and (fire_count > 0 or smoke_count > 0):
                timestamp = int(time.time())
                save_path = f"detection_{timestamp}.jpg"
                cv2.imwrite(save_path, annotated_frame)

    except KeyboardInterrupt:
        print("\n⏹️  检测中断")
    finally:
        cap.release()
        if args.show:
            cv2.destroyAllWindows()
        print("✅ 资源已清理")

if __name__ == '__main__':
    main()