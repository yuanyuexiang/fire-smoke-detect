#!/usr/bin/env python3
"""
RK3588优化版火灾烟雾检测脚本
- 针对ARM64架构优化
- 支持多种输入源
- 内存和CPU使用优化
- 支持无头模式运行
"""

import argparse
import cv2
import torch
import numpy as np
import time
import os
import threading
import json
from datetime import datetime
import signal
import sys

class RK3588FireDetector:
    def __init__(self, weights_path, img_size=416, conf_thres=0.4, device='cpu'):
        self.weights_path = weights_path
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.device = device
        self.model = None
        self.running = False
        
        # 性能监控
        self.fps_counter = 0
        self.start_time = time.time()
        self.detection_count = 0
        
        # 加载模型
        self.load_model()
        
    def load_model(self):
        """加载YOLOv5模型"""
        try:
            print(f"🔄 加载模型: {self.weights_path}")
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                      path=self.weights_path, force_reload=True)
            self.model.conf = self.conf_thres
            self.model.iou = 0.5
            
            # 优化设置
            if self.device == 'cpu':
                self.model.cpu()
                # ARM64 CPU优化
                torch.set_num_threads(4)  # RK3588有8核，使用4个线程
            
            print("✅ 模型加载完成")
            return True
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            return False
    
    def detect_frame(self, frame):
        """检测单帧"""
        try:
            # 预处理
            img_resized = cv2.resize(frame, (self.img_size, self.img_size))
            
            # 推理
            results = self.model(img_resized)
            
            # 解析结果
            detections = results.pandas().xyxy[0]
            
            fire_detections = []
            if len(detections) > 0:
                for _, detection in detections.iterrows():
                    if detection['confidence'] > self.conf_thres:
                        # 将坐标缩放回原始图像
                        h, w = frame.shape[:2]
                        x1 = int(detection['xmin'] * w / self.img_size)
                        y1 = int(detection['ymin'] * h / self.img_size)
                        x2 = int(detection['xmax'] * w / self.img_size)
                        y2 = int(detection['ymax'] * h / self.img_size)
                        
                        fire_detections.append({
                            'bbox': [x1, y1, x2, y2],
                            'confidence': detection['confidence'],
                            'class': detection['name']
                        })
                        
                        self.detection_count += 1
            
            return fire_detections
        except Exception as e:
            print(f"检测错误: {e}")
            return []
    
    def draw_detections(self, frame, detections):
        """绘制检测结果"""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            class_name = det['class']
            
            # 绘制边框
            color = (0, 0, 255) if 'fire' in class_name.lower() else (0, 255, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def run(self, source, save_video=False, show_display=False, log_detections=True):
        """运行检测"""
        print(f"🎥 启动检测 - 输入源: {source}")
        
        # 打开视频源
        if source == '0' or source == 0:
            cap = cv2.VideoCapture(0)
        elif source.startswith('rtsp://'):
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少延迟
        else:
            cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print(f"❌ 无法打开视频源: {source}")
            return False
        
        # 获取视频信息
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"📹 视频信息: {width}x{height} @ {fps:.2f}FPS")
        
        # 设置视频保存
        out = None
        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_filename = f"fire_detection_{timestamp}.mp4"
            out = cv2.VideoWriter(out_filename, fourcc, 20.0, (width, height))
            print(f"💾 保存视频到: {out_filename}")
        
        self.running = True
        frame_count = 0
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("📺 视频流结束或读取失败")
                    break
                
                frame_count += 1
                
                # 检测
                detections = self.detect_frame(frame)
                
                # 绘制结果
                if detections:
                    frame = self.draw_detections(frame, detections)
                    
                    # 记录检测结果
                    if log_detections:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"🔥 [{timestamp}] 检测到 {len(detections)} 个目标")
                        for i, det in enumerate(detections):
                            print(f"   目标{i+1}: {det['class']} (置信度: {det['confidence']:.3f})")
                
                # 显示FPS和状态信息
                elapsed_time = time.time() - self.start_time
                if elapsed_time > 1:
                    current_fps = frame_count / elapsed_time
                    
                    # 在画面上显示信息
                    info_text = f"FPS: {current_fps:.1f} | Detections: {self.detection_count}"
                    cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # 重置计数器
                    if elapsed_time > 5:  # 每5秒重置一次
                        self.start_time = time.time()
                        frame_count = 0
                
                # 保存视频
                if save_video and out:
                    out.write(frame)
                
                # 显示图像（如果启用）
                if show_display:
                    cv2.imshow('RK3588 Fire Detection', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:  # q键或ESC键退出
                        break
                
                # CPU使用率控制
                time.sleep(0.01)  # 10ms延迟，避免CPU占用过高
        
        except KeyboardInterrupt:
            print("\n⏹️  收到停止信号")
        
        finally:
            self.running = False
            cap.release()
            if out:
                out.release()
            if show_display:
                cv2.destroyAllWindows()
            
            print("✅ 检测结束")
            print(f"📊 总计检测到 {self.detection_count} 个目标")

def signal_handler(sig, frame):
    """信号处理函数"""
    print('\n🛑 接收到退出信号，正在停止...')
    global detector
    if detector:
        detector.running = False
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='RK3588火灾烟雾检测系统')
    parser.add_argument('--source', type=str, default='0', help='输入源')
    parser.add_argument('--weights', type=str, default='./best.pt', help='模型权重文件')
    parser.add_argument('--img-size', type=int, default=416, help='输入图像大小')
    parser.add_argument('--conf', type=float, default=0.4, help='置信度阈值')
    parser.add_argument('--device', type=str, default='cpu', help='设备')
    parser.add_argument('--save-vid', action='store_true', help='保存检测视频')
    parser.add_argument('--view-img', action='store_true', help='显示检测窗口')
    parser.add_argument('--no-log', action='store_true', help='不记录检测日志')
    
    args = parser.parse_args()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 检查模型文件
    if not os.path.exists(args.weights):
        print(f"❌ 模型文件不存在: {args.weights}")
        return
    
    print("🚀 RK3588火灾烟雾检测系统启动")
    print(f"   模型: {args.weights}")
    print(f"   输入源: {args.source}")
    print(f"   图像大小: {args.img_size}")
    print(f"   置信度阈值: {args.conf}")
    print(f"   设备: {args.device}")
    print("-" * 50)
    
    # 创建检测器
    global detector
    detector = RK3588FireDetector(
        weights_path=args.weights,
        img_size=args.img_size,
        conf_thres=args.conf,
        device=args.device
    )
    
    # 运行检测
    detector.run(
        source=args.source,
        save_video=args.save_vid,
        show_display=args.view_img,
        log_detections=not args.no_log
    )

if __name__ == '__main__':
    main()