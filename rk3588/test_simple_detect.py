#!/usr/bin/env python3
"""
简化版RKNN检测脚本 - 用于快速测试
"""

import cv2
import numpy as np
import time
import argparse
import os
from rknn.api import RKNN

class SimpleRKNNDetector:
    def __init__(self, rknn_model_path, conf_threshold=0.4):
        self.rknn_model_path = rknn_model_path
        self.conf_threshold = conf_threshold
        self.rknn = RKNN()
        self.model_loaded = False
        self.input_size = (640, 640)
        self.class_names = ['fire', 'smoke']
        
        self.load_model()
    
    def load_model(self):
        """加载RKNN模型"""
        try:
            print(f"🔄 加载模型: {self.rknn_model_path}")
            
            ret = self.rknn.load_rknn(self.rknn_model_path)
            if ret != 0:
                return False
                
            ret = self.rknn.init_runtime(target='rk3588', device_id=0)
            if ret != 0:
                return False
                
            self.model_loaded = True
            print('✅ 模型加载成功')
            return True
            
        except Exception as e:
            print(f"❌ 模型加载错误: {e}")
            return False
    
    def simple_postprocess(self, outputs, original_shape):
        """简化的后处理 - 基于置信度阈值"""
        try:
            feature_map = outputs[0]  # (1, 85, 20, 20)
            
            if len(feature_map.shape) == 4:
                feature_map = feature_map[0]  # (85, 20, 20)
            
            h, w = original_shape[:2]
            grid_h, grid_w = feature_map.shape[1], feature_map.shape[2]
            
            boxes = []
            scores = []
            class_ids = []
            
            # 简单扫描整个特征图
            for channel in range(4, min(feature_map.shape[0], 20)):  # 从第5个通道开始扫描
                conf_map = feature_map[channel]  # (20, 20)
                
                # 应用sigmoid
                conf_map = 1.0 / (1.0 + np.exp(-conf_map))
                
                # 找到高置信度区域
                high_conf_positions = np.where(conf_map > self.conf_threshold)
                
                for gy, gx in zip(high_conf_positions[0], high_conf_positions[1]):
                    confidence = float(conf_map[gy, gx])
                    
                    # 生成简单的边框（基于网格位置）
                    stride = 32  # 640/20
                    center_x = (gx + 0.5) * stride
                    center_y = (gy + 0.5) * stride
                    
                    # 固定大小的边框
                    box_size = stride * 2  # 64像素
                    
                    x1 = int((center_x - box_size/2) * w / 640)
                    y1 = int((center_y - box_size/2) * h / 640)
                    x2 = int((center_x + box_size/2) * w / 640)
                    y2 = int((center_y + box_size/2) * h / 640)
                    
                    # 边界检查
                    x1 = max(0, min(x1, w))
                    y1 = max(0, min(y1, h))
                    x2 = max(0, min(x2, w))
                    y2 = max(0, min(y2, h))
                    
                    if x2 > x1 and y2 > y1:
                        boxes.append([x1, y1, x2, y2])
                        scores.append(confidence)
                        class_ids.append(0 if channel < 10 else 1)  # 简单分类
            
            # 简单NMS
            if len(boxes) > 0:
                indices = cv2.dnn.NMSBoxes(boxes, scores, self.conf_threshold, 0.5)
                if len(indices) > 0:
                    final_boxes = [boxes[i] for i in indices.flatten()]
                    final_scores = [scores[i] for i in indices.flatten()]
                    final_class_ids = [class_ids[i] for i in indices.flatten()]
                    return final_boxes, final_scores, final_class_ids
                    
        except Exception as e:
            print(f"简化后处理错误: {e}")
            
        return [], [], []
    
    def detect(self, image):
        """执行检测"""
        if not self.model_loaded:
            return [], [], []
        
        try:
            # 简单预处理
            input_image = cv2.resize(image, self.input_size)
            input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
            
            # 推理
            outputs = self.rknn.inference(inputs=[input_image], data_format='nhwc')
            
            # 后处理
            boxes, scores, class_ids = self.simple_postprocess(outputs, image.shape)
            
            return boxes, scores, class_ids
            
        except Exception as e:
            print(f"检测错误: {e}")
            return [], [], []

def main():
    print("🔥 简化版RK3588火灾检测测试")
    
    model_path = "./models/best_final_clean.rknn"
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return
    
    # 创建检测器
    detector = SimpleRKNNDetector(model_path, conf_threshold=0.3)
    
    if not detector.model_loaded:
        print("❌ 模型加载失败")
        return
    
    # 测试RTSP
    source = "rtsp://admin:sual116y@192.168.86.19:554/Streaming/Channels/102"
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print("❌ 无法打开视频源")
        return
    
    print("🚀 开始检测...")
    frame_count = 0
    detection_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # 检测
            boxes, scores, class_ids = detector.detect(frame)
            
            # 绘制结果
            for i, (box, score, class_id) in enumerate(zip(boxes, scores, class_ids)):
                x1, y1, x2, y2 = box
                label = f"{detector.class_names[class_id]}: {score:.2f}"
                
                color = (0, 255, 0) if class_id == 0 else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                detection_count += 1
            
            # 显示FPS
            if frame_count % 30 == 0:
                print(f"处理了 {frame_count} 帧，检测到 {detection_count} 个目标")
            
            # 显示结果
            cv2.imshow('Simple Fire Detection', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("检测中断")
        
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()