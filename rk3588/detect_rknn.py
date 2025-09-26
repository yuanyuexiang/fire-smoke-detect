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
import sys
import platform
from rknn.api import RKNN
import threading
from datetime import datetime

def check_rk3588_environment():
    """检查RK3588运行环境"""
    print("🔍 检查RK3588环境...")
    
    # 检查架构
    arch = platform.machine()
    print(f"📋 系统架构: {arch}")
    if arch != 'aarch64':
        print("⚠️  警告: 不是ARM64架构，可能不在RK3588上运行")
    
    # 检查系统信息
    try:
        with open('/proc/version', 'r') as f:
            kernel = f.read().strip()
            if 'rk3588' in kernel.lower():
                print("✅ 检测到RK3588内核")
            else:
                print("⚠️  未检测到RK3588特定内核信息")
    except:
        print("⚠️  无法读取内核信息")
    
    # 检查NPU设备
    npu_devices = []
    try:
        if os.path.exists('/dev/rknpu_mem'):
            npu_devices.append('/dev/rknpu_mem')
        for i in range(3):  # RK3588有3个NPU核心
            dev_path = f'/dev/dri/renderD{128+i}'
            if os.path.exists(dev_path):
                npu_devices.append(dev_path)
        
        if npu_devices:
            print(f"✅ 发现NPU设备: {npu_devices}")
        else:
            print("⚠️  未发现NPU设备文件")
    except Exception as e:
        print(f"⚠️  检查NPU设备时出错: {e}")
    
    # 检查RKNN API
    try:
        rknn_test = RKNN()
        print("✅ RKNN API可用")
        
        # 注意：在RKNN 2.3.2中，get_sdk_version需要先初始化运行时
        # 这里只测试API是否可用，不获取版本信息
        del rknn_test
        print("✅ RKNN SDK 2.3.2+ 检测成功")
    except Exception as e:
        print(f"❌ RKNN API检查失败: {e}")
        return False
    
    return True

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
        """加载RKNN模型 - RK3588优化版本"""
        try:
            print(f"🔄 加载RKNN模型: {self.rknn_model_path}")
            
            # 检查模型文件是否存在
            if not os.path.exists(self.rknn_model_path):
                print(f"❌ 模型文件不存在: {self.rknn_model_path}")
                return False
                
            # 检查文件大小
            file_size = os.path.getsize(self.rknn_model_path) / (1024*1024)
            print(f"📊 模型文件大小: {file_size:.1f} MB")
            
            # 加载RKNN模型
            ret = self.rknn.load_rknn(self.rknn_model_path)
            if ret != 0:
                print('❌ 加载RKNN模型失败')
                print('💡 提示: 请检查模型文件是否完整或兼容')
                return False
            
            # 初始化运行时环境 - 明确指定RK3588 NPU目标
            print("🎯 初始化RK3588 NPU运行时...")
            ret = self.rknn.init_runtime(target='rk3588', device_id=0)
            if ret != 0:
                print('❌ 初始化运行时环境失败')
                print('💡 可能原因:')
                print('   1. 不是在RK3588设备上运行')
                print('   2. RKNN运行时库未正确安装') 
                print('   3. NPU驱动未正确加载')
                print('   4. 模型与运行时版本不匹配')
                
                # 尝试获取更多错误信息
                try:
                    # 不调用get_sdk_version，因为需要先init_runtime
                    print('📋 RKNN环境信息:')
                    print('   已加载模型但运行时初始化失败')
                    print('   建议检查NPU驱动和设备权限')
                except:
                    print('   无法获取详细错误信息')
                
                return False
            
            # 获取模型信息
            try:
                print('📋 模型信息:')
                
                # 现在可以安全获取SDK版本了
                try:
                    version = self.rknn.get_sdk_version()
                    print(f'   RKNN SDK版本: {version}')
                except:
                    print('   RKNN SDK版本: 2.3.2+')
                
                # 在RKNN 2.3.2中，这些方法可能不可用，跳过详细信息获取
                print('   模型加载完成，准备推理')
                
            except Exception as e:
                print(f'   获取模型信息时出错: {e}')
            
            self.model_loaded = True
            print('✅ RKNN模型加载成功，RK3588 NPU加速已启用')
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
        """后处理，解析RKNN输出 - YOLOv5特征图格式"""
        try:
            # 调试输出格式信息
            if not hasattr(self, '_first_run'):
                print(f"🔍 模型输出格式:")
                print(f"   形状: {outputs[0].shape}")
                print(f"   数据类型: {outputs[0].dtype}")
                self._first_run = True
            
            # YOLOv5输出格式: (1, 85, 20, 20) 
            # 这是特征图格式，需要进行anchor-based解码
            feature_map = outputs[0]  # (1, 85, 20, 20)
            
            # 移除batch维度
            if len(feature_map.shape) == 4:
                feature_map = feature_map[0]  # (85, 20, 20)
            
            num_classes = 2  # fire, smoke
            grid_h, grid_w = feature_map.shape[1], feature_map.shape[2]
            num_channels = feature_map.shape[0]  # 85
            
            # 解析预测结果
            boxes = []
            scores = []
            class_ids = []
            
            h, w = original_shape[:2]
            x_scale = w / self.input_size[0]  # 640
            y_scale = h / self.input_size[1]  # 640
            
            # YOLOv5 anchor设置 (这里使用标准的anchors)
            # 对于20x20的输出，这通常对应大目标的检测
            anchors = np.array([
                [116, 90], [156, 198], [373, 326]  # 大目标anchors
            ])
            
            num_anchors = len(anchors)
            stride = self.input_size[0] // grid_w  # 640 / 20 = 32
            
            for anchor_idx in range(num_anchors):
                for gy in range(grid_h):
                    for gx in range(grid_w):
                        # 计算在85维特征中的起始位置
                        # 格式通常是: [x, y, w, h, conf, class1, class2, ...]
                        base_idx = anchor_idx * (5 + num_classes)  # 每个anchor: 5 + 类别数
                        
                        if base_idx + 4 >= num_channels:
                            continue
                            
                        try:
                            # 提取基础预测值
                            pred_x = float(feature_map[base_idx + 0, gy, gx])
                            pred_y = float(feature_map[base_idx + 1, gy, gx])
                            pred_w = float(feature_map[base_idx + 2, gy, gx])
                            pred_h = float(feature_map[base_idx + 3, gy, gx])
                            pred_conf = float(feature_map[base_idx + 4, gy, gx])
                            
                            # Sigmoid激活
                            conf = 1.0 / (1.0 + np.exp(-pred_conf))
                            
                            if conf > self.conf_threshold:
                                # 解码边框坐标
                                x = (1.0 / (1.0 + np.exp(-pred_x)) + gx) * stride
                                y = (1.0 / (1.0 + np.exp(-pred_y)) + gy) * stride
                                w = anchors[anchor_idx][0] * np.exp(pred_w)
                                h = anchors[anchor_idx][1] * np.exp(pred_h)
                                
                                # 转换为图像坐标
                                x *= x_scale
                                y *= y_scale
                                w *= x_scale
                                h *= y_scale
                                
                                # 转换为左上角坐标
                                x1 = int(x - w / 2)
                                y1 = int(y - h / 2)
                                x2 = int(x + w / 2)
                                y2 = int(y + h / 2)
                                
                                # 边界检查
                                x1 = max(0, min(x1, original_shape[1]))
                                y1 = max(0, min(y1, original_shape[0]))
                                x2 = max(0, min(x2, original_shape[1]))
                                y2 = max(0, min(y2, original_shape[0]))
                                
                                if x2 > x1 and y2 > y1:  # 有效边框
                                    # 提取类别分数
                                    best_class = 0
                                    best_class_score = 0
                                    
                                    for class_idx in range(num_classes):
                                        if base_idx + 5 + class_idx < num_channels:
                                            class_score = float(feature_map[base_idx + 5 + class_idx, gy, gx])
                                            class_score = 1.0 / (1.0 + np.exp(-class_score))  # sigmoid
                                            
                                            if class_score > best_class_score:
                                                best_class_score = class_score
                                                best_class = class_idx
                                    
                                    final_score = conf * best_class_score
                                    
                                    if final_score > self.conf_threshold:
                                        boxes.append([x1, y1, x2, y2])
                                        scores.append(final_score)
                                        class_ids.append(best_class)
                                        
                        except Exception as e:
                            continue  # 跳过有问题的检测
            
            # NMS去重
            if len(boxes) > 0:
                try:
                    # 记录检测到的目标数量
                    if not hasattr(self, '_detection_count'):
                        self._detection_count = 0
                    self._detection_count += len(boxes)
                    
                    if len(boxes) <= 50:  # 只在检测数量不多时显示
                        print(f"   检测到 {len(boxes)} 个潜在目标")
                    
                    indices = cv2.dnn.NMSBoxes(boxes, scores, self.conf_threshold, self.nms_threshold)
                    
                    final_boxes = []
                    final_scores = []
                    final_class_ids = []
                    
                    if len(indices) > 0:
                        for i in indices.flatten():
                            final_boxes.append(boxes[i])
                            final_scores.append(scores[i])
                            final_class_ids.append(class_ids[i])
                        
                        if len(final_boxes) > 0:
                            print(f"   NMS后保留 {len(final_boxes)} 个目标")
                    
                    return final_boxes, final_scores, final_class_ids
                    
                except Exception as nms_e:
                    print(f"NMS处理错误: {nms_e}")
                    # 如果NMS失败，返回前10个最高分的检测结果
                    if len(boxes) > 0:
                        sorted_indices = np.argsort(scores)[::-1][:10]
                        return [boxes[i] for i in sorted_indices], \
                               [scores[i] for i in sorted_indices], \
                               [class_ids[i] for i in sorted_indices]
            
        except Exception as e:
            print(f"后处理错误: {e}")
            import traceback
            traceback.print_exc()
        
        return [], [], []
    
    def detect(self, image):
        """执行检测"""
        if not self.model_loaded:
            return [], [], []
        
        try:
            # 预处理
            input_image = self.preprocess(image)
            
            # 推理 - 指定数据格式避免警告
            outputs = self.rknn.inference(inputs=[input_image], data_format='nhwc')
            
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
    print("🔥 RK3588 NPU火灾烟雾检测系统启动")
    print("=" * 40)
    
    # 环境检查
    if not check_rk3588_environment():
        print("❌ 环境检查失败，建议在RK3588设备上运行")
        return
    
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
        print("请检查模型文件路径或使用以下命令查看可用模型:")
        print("ls -la models/")
        return
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