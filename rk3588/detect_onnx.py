#!/usr/bin/env python3
"""
RK3588 ONNX检测脚本 - 不需要RKNN转换
使用ONNXRuntime进行CPU推理
"""

import cv2
import numpy as np
import time
import argparse
import os
import sys

def check_onnx_requirements():
    """检查ONNX运行环境"""
    try:
        import onnxruntime as ort
        print(f"✅ ONNXRuntime版本: {ort.__version__}")
        
        # 检查可用的执行提供器
        providers = ort.get_available_providers()
        print(f"✅ 可用执行器: {providers}")
        
        if 'CPUExecutionProvider' in providers:
            return True
        else:
            print("❌ 未找到CPU执行器")
            return False
            
    except ImportError:
        print("❌ 未安装ONNXRuntime，请运行:")
        print("pip3 install onnxruntime")
        return False

class ONNXFireDetector:
    def __init__(self, onnx_model_path, conf_threshold=0.4, nms_threshold=0.5):
        self.onnx_model_path = onnx_model_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.session = None
        self.input_size = (640, 640)
        self.class_names = ['fire', 'smoke']
        
        self.load_model()
    
    def load_model(self):
        """加载ONNX模型"""
        try:
            import onnxruntime as ort
            
            print(f"🔄 加载ONNX模型: {self.onnx_model_path}")
            
            # 创建推理会话，优先使用CPU
            providers = ['CPUExecutionProvider']
            self.session = ort.InferenceSession(self.onnx_model_path, providers=providers)
            
            # 获取输入输出信息
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            input_shape = self.session.get_inputs()[0].shape
            print(f"✅ ONNX模型加载成功")
            print(f"   输入: {self.input_name} {input_shape}")
            print(f"   输出: {len(self.output_names)}个")
            
            return True
            
        except Exception as e:
            print(f"❌ ONNX模型加载错误: {e}")
            return False
    
    def preprocess(self, image):
        """图像预处理"""
        # 调整大小
        input_image = cv2.resize(image, self.input_size)
        # 颜色空间转换
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
        # 归一化
        input_image = input_image.astype(np.float32) / 255.0
        # 添加batch维度并转换为NCHW格式
        input_image = np.transpose(input_image, (2, 0, 1))  # HWC -> CHW
        input_image = np.expand_dims(input_image, axis=0)   # CHW -> NCHW
        
        return input_image
    
    def postprocess(self, outputs, original_shape):
        """后处理 - 标准YOLOv5格式"""
        try:
            # YOLOv5 ONNX输出通常是 (1, 25200, 85)
            predictions = outputs[0]  # 获取第一个输出
            
            if len(predictions.shape) == 3:
                predictions = predictions[0]  # 去掉batch维度: (25200, 85)
            
            boxes = []
            scores = []
            class_ids = []
            
            h, w = original_shape[:2]
            x_scale = w / self.input_size[0]
            y_scale = h / self.input_size[1]
            
            for detection in predictions:
                # YOLOv5格式: [x_center, y_center, width, height, confidence, class1_score, class2_score, ...]
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
                    
                    # 获取类别分数
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
                
                if len(indices) > 0:
                    final_boxes = [boxes[i] for i in indices.flatten()]
                    final_scores = [scores[i] for i in indices.flatten()]
                    final_class_ids = [class_ids[i] for i in indices.flatten()]
                    
                    return final_boxes, final_scores, final_class_ids
            
        except Exception as e:
            print(f"后处理错误: {e}")
        
        return [], [], []
    
    def detect(self, image):
        """执行检测"""
        if self.session is None:
            return [], [], []
        
        try:
            # 预处理
            input_image = self.preprocess(image)
            
            # 推理
            outputs = self.session.run(self.output_names, {self.input_name: input_image})
            
            # 后处理
            boxes, scores, class_ids = self.postprocess(outputs, image.shape)
            
            return boxes, scores, class_ids
            
        except Exception as e:
            print(f"检测错误: {e}")
            return [], [], []

def main():
    print("🔥 RK3588 ONNX火灾烟雾检测系统")
    print("=" * 40)
    
    # 检查环境
    if not check_onnx_requirements():
        print("\n💡 安装ONNXRuntime:")
        print("pip3 install onnxruntime")
        return
    
    parser = argparse.ArgumentParser(description='RK3588 ONNX火灾烟雾检测')
    parser.add_argument('--source', type=str, default='0', help='输入源')
    parser.add_argument('--weights', type=str, default='./models/best_final_clean.onnx', help='ONNX模型路径')
    parser.add_argument('--conf', type=float, default=0.4, help='置信度阈值')
    parser.add_argument('--nms', type=float, default=0.5, help='NMS阈值')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.weights):
        print(f"❌ ONNX模型文件不存在: {args.weights}")
        print("请检查模型路径")
        return
    
    # 创建检测器
    detector = ONNXFireDetector(args.weights, args.conf, args.nms)
    
    if detector.session is None:
        print("❌ 模型加载失败")
        return
    
    # 打开视频源
    print(f"\n📹 打开视频源: {args.source}")
    if args.source.isdigit():
        source = int(args.source)
    else:
        source = args.source
    
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print("❌ 无法打开视频源")
        return
    
    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📊 视频信息: {width}x{height} @ {fps:.1f}FPS")
    
    print("🚀 CPU推理启动...")
    print("⚠️  注意: CPU推理速度较慢，请耐心等待")
    
    frame_count = 0
    total_time = 0
    detection_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ 读取视频帧失败")
                break
            
            frame_count += 1
            
            # 检测
            start_time = time.time()
            boxes, scores, class_ids = detector.detect(frame)
            detect_time = time.time() - start_time
            total_time += detect_time
            
            detection_count += len(boxes)
            
            # 绘制检测结果
            for i, (box, score, class_id) in enumerate(zip(boxes, scores, class_ids)):
                x1, y1, x2, y2 = box
                label = f"{detector.class_names[class_id]}: {score:.2f}"
                
                # 颜色设置
                color = (0, 255, 0) if class_id == 0 else (0, 0, 255)  # 绿色=火灾，红色=烟雾
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 显示FPS和性能信息
            if frame_count > 0:
                avg_fps = frame_count / total_time
                current_fps = 1.0 / detect_time if detect_time > 0 else 0
                fps_text = f"CPU FPS: {current_fps:.1f} | Avg: {avg_fps:.1f} | Inference: {detect_time*1000:.0f}ms"
            else:
                fps_text = "CPU FPS: 计算中..."
            
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 显示检测统计
            stats_text = f"Detections: {len(boxes)} | Total: {detection_count}"
            cv2.putText(frame, stats_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # 显示图像
            cv2.imshow('ONNX Fire Detection (CPU)', frame)
            
            # 按'q'退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # 每30帧显示统计信息
            if frame_count % 30 == 0:
                avg_fps = frame_count / total_time
                print(f"📊 已处理 {frame_count} 帧，平均FPS: {avg_fps:.1f}，检测到 {detection_count} 个目标")
    
    except KeyboardInterrupt:
        print("\n⏹️  检测中断")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        if frame_count > 0:
            avg_fps = frame_count / total_time
            print(f"\n📊 检测完成:")
            print(f"   总帧数: {frame_count}")
            print(f"   平均FPS: {avg_fps:.1f}")
            print(f"   检测到目标: {detection_count} 个")
            print(f"   总耗时: {total_time:.1f}秒")

if __name__ == '__main__':
    main()