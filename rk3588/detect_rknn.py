#!/usr/bin/env python3
"""
RK3588 RKNN模型推理脚本 - 使用预转换的最终模型
使用NPU加速进行火灾烟雾检测
模型文件: best_final_clean.rknn (已优化，无需转换)
"""

import cv2
import numpy as np
import time
import argparse
import os
from rknn.api import RKNN
import threading
from datetime import datetime

class RKNNFireDetector:
    def __init__(self, rknn_model_path, conf_threshold=0.4, nms_threshold=0.5):
        self.rknn_model_path = rknn_model_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.rknn = RKNN()
        self.model_loaded = False
        self.input_size = (640, 640)
        
        # 类别名称（根据您的模型调整）
        self.class_names = ['fire', 'smoke']  # 火灾和烟雾
        
        self.load_model()
    
    def load_model(self):
        """加载RKNN模型"""
        try:
            print(f"🔄 加载RKNN模型: {self.rknn_model_path}")
            
            # 加载RKNN模型
            ret = self.rknn.load_rknn(self.rknn_model_path)
            if ret != 0:
                print('❌ 加载RKNN模型失败')
                return False
            
            # 初始化运行时环境
            ret = self.rknn.init_runtime()
            if ret != 0:
                print('❌ 初始化运行时环境失败')
                return False
            
            self.model_loaded = True
            print('✅ RKNN模型加载成功，NPU加速已启用')
            return True
            
        except Exception as e:
            print(f"❌ 模型加载错误: {e}")
            return False
    
    def preprocess(self, image):
        """图像预处理"""
        # 调整大小
        input_image = cv2.resize(image, self.input_size)
        # 颜色空间转换
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
        return input_image
    
    def postprocess(self, outputs, original_shape):
        """后处理，解析RKNN输出"""
        try:
            # 这里需要根据您的具体模型输出格式进行调整
            # 通常YOLOv5的输出是 (1, 25200, 85) 的形状
            predictions = outputs[0]
            
            # 解析预测结果
            boxes = []
            scores = []
            class_ids = []
            
            h, w = original_shape[:2]
            x_scale = w / self.input_size[0]
            y_scale = h / self.input_size[1]
            
            for detection in predictions:
                # 提取置信度和类别分数
                confidence = detection[4]
                if confidence > self.conf_threshold:
                    # 提取边框坐标
                    x_center = detection[0] * x_scale
                    y_center = detection[1] * y_scale
                    width = detection[2] * x_scale
                    height = detection[3] * y_scale
                    
                    # 转换为左上角坐标
                    x1 = int(x_center - width / 2)
                    y1 = int(y_center - height / 2)
                    x2 = int(x_center + width / 2)
                    y2 = int(y_center + height / 2)
                    
                    # 获取最高分类别
                    class_scores = detection[5:]
                    class_id = np.argmax(class_scores)
                    class_score = class_scores[class_id]
                    
                    final_score = confidence * class_score
                    
                    if final_score > self.conf_threshold:
                        boxes.append([x1, y1, x2, y2])
                        scores.append(float(final_score))
                        class_ids.append(int(class_id))
            
            # NMS去重
            if len(boxes) > 0:
                indices = cv2.dnn.NMSBoxes(boxes, scores, self.conf_threshold, self.nms_threshold)
                
                final_boxes = []
                final_scores = []
                final_class_ids = []
                
                if len(indices) > 0:
                    for i in indices.flatten():
                        final_boxes.append(boxes[i])
                        final_scores.append(scores[i])
                        final_class_ids.append(class_ids[i])
                
                return final_boxes, final_scores, final_class_ids
            
        except Exception as e:
            print(f"后处理错误: {e}")
        
        return [], [], []
    
    def detect(self, image):
        """执行检测"""
        if not self.model_loaded:
            return [], [], []
        
        try:
            # 预处理
            input_image = self.preprocess(image)
            
            # 推理
            outputs = self.rknn.inference(inputs=[input_image])
            
            # 后处理
            boxes, scores, class_ids = self.postprocess(outputs, image.shape)
            
            return boxes, scores, class_ids
            
        except Exception as e:
            print(f"检测错误: {e}")
            return [], [], []
    
    def draw_results(self, image, boxes, scores, class_ids):
        """绘制检测结果"""
        for i, (box, score, class_id) in enumerate(zip(boxes, scores, class_ids)):
            x1, y1, x2, y2 = box
            
            # 选择颜色
            color = (0, 0, 255) if class_id == 0 else (0, 255, 255)  # 红色=火灾，黄色=烟雾
            
            # 绘制边框
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label = f"{self.class_names[class_id]}: {score:.2f}"
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(image, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
            cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return image
    
    def run_detection(self, source, save_video=False, show_display=True):
        """运行检测循环"""
        # 打开视频源
        if source == '0' or source == 0:
            cap = cv2.VideoCapture(0)
        elif source.startswith('rtsp://'):
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print(f"❌ 无法打开视频源: {source}")
            return
        
        # 获取视频信息
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"📹 视频源信息: {width}x{height} @ {fps:.2f}FPS")
        print("🚀 NPU加速推理启动...")
        
        # 视频保存设置
        out = None
        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_filename = f"rknn_fire_detection_{timestamp}.mp4"
            out = cv2.VideoWriter(out_filename, fourcc, 20.0, (width, height))
            print(f"💾 保存视频到: {out_filename}")
        
        # FPS计算
        fps_counter = 0
        start_time = time.time()
        detection_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                fps_counter += 1
                
                # 执行检测
                detect_start = time.time()
                boxes, scores, class_ids = self.detect(frame)
                detect_time = time.time() - detect_start
                
                # 绘制结果
                if len(boxes) > 0:
                    frame = self.draw_results(frame, boxes, scores, class_ids)
                    detection_count += len(boxes)
                    
                    # 打印检测信息
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"🔥 [{timestamp}] NPU检测到 {len(boxes)} 个目标 (推理时间: {detect_time*1000:.1f}ms)")
                
                # 计算并显示FPS
                elapsed = time.time() - start_time
                if elapsed > 1.0:
                    current_fps = fps_counter / elapsed
                    fps_counter = 0
                    start_time = time.time()
                    
                    # 在画面上显示性能信息
                    fps_text = f"NPU FPS: {current_fps:.1f} | Inference: {detect_time*1000:.1f}ms"
                    cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                detection_info = f"Detections: {detection_count}"
                cv2.putText(frame, detection_info, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 保存视频帧
                if save_video and out:
                    out.write(frame)
                
                # 显示图像
                if show_display:
                    cv2.imshow('RK3588 NPU Fire Detection', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:
                        break
        
        except KeyboardInterrupt:
            print("\n⏹️  检测停止")
        
        finally:
            cap.release()
            if out:
                out.release()
            if show_display:
                cv2.destroyAllWindows()
            
            print(f"📊 检测完成，共检测到 {detection_count} 个目标")
    
    def __del__(self):
        if hasattr(self, 'rknn'):
            self.rknn.release()

def main():
    parser = argparse.ArgumentParser(description='RK3588 NPU火灾烟雾检测')
    parser.add_argument('--source', type=str, default='0', help='输入源')
    parser.add_argument('--weights', type=str, default='./models/best_final_clean.rknn', help='RKNN模型路径')
    parser.add_argument('--conf', type=float, default=0.4, help='置信度阈值')
    parser.add_argument('--nms', type=float, default=0.5, help='NMS阈值')
    parser.add_argument('--save-vid', action='store_true', help='保存检测视频')
    parser.add_argument('--no-display', action='store_true', help='不显示检测窗口')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.weights):
        print(f"❌ RKNN模型文件不存在: {args.weights}")
        print("请先运行模型转换:")
        print("python3 convert_to_rknn.py --input ./best.pt")
        return
    
    print("🚀 RK3588 NPU火灾烟雾检测系统")
    print(f"   RKNN模型: {args.weights}")
    print(f"   输入源: {args.source}")
    print(f"   置信度阈值: {args.conf}")
    print("-" * 50)
    
    # 创建检测器
    detector = RKNNFireDetector(args.weights, args.conf, args.nms)
    
    # 运行检测
    detector.run_detection(
        source=args.source,
        save_video=args.save_vid,
        show_display=not args.no_display
    )

if __name__ == '__main__':
    main()