## fire-smoke-detect-yolov4-v5 and fire-smoke-detect-dataset

* author is leilei
* [**README_ZN 中文版说明**](./readmes/README_ZN.md)
* [**README_EN English Description**](./readmes/README_EN.md)
* [**yolov4 tensorrt python inference**](https://github.com/gengyanlei/onnx2tensorRt)
* [**Note: 百度Paddle智慧城市生态使用本人烟火检测数据集(PS:明明是我的数据还要感谢别人一下)**](https://github.com/PaddlePaddle/awesome-DeepLearning/tree/master/Paddle_Industry_Practice_Sample_Library/Fire_and_Smoke_Detection)

* This repository code has stopped updating, please use the dataset to retrain the detection model directly!
* This repository code has stopped updating, please use the dataset to retrain the detection model directly!
* This repository code has stopped updating, please use the dataset to retrain the detection model directly!

### fire-smoke-detect-demo
|![fire-smoke-detect-demo](./result/result_demo.jpg)|
|----|

### Data Label Tool
+ [CVAT](https://github.com/openvinotoolkit/cvat)
+ [CVAT-Tutorial](https://blog.csdn.net/LEILEI18A/article/details/113385510)

### Other
* [leilei's blog](https://blog.csdn.net/LEILEI18A/article/details/107334474)
* [VSCode Remote SSH 安装教程](https://blog.csdn.net/LEILEI18A/article/details/102524181)
* [segmentation_pytorch 语义分割](https://github.com/gengyanlei/segmentation_pytorch)
* [building-segmentation-dataset 遥感影像建筑语义分割](https://github.com/gengyanlei/build_segmentation_dataset)
* [reflective-clothes-detect-dataset 安全帽反光衣检测](https://github.com/gengyanlei/reflective-clothes-detect)


## YOLOv5 检测使用方法

### 本地摄像头检测
```bash
cd /Users/yuanyuexiang/Desktop/workspace/fire-smoke-detect/yolov5 && python3 detect.py --source 0 --weights ./best.pt --device cpu --view-img --conf 0.4
```

### RTSP网络摄像头检测
```bash
# 海康威视摄像头 - 多种路径格式
# 主码流
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/1" --weights ./best.pt --device cpu --view-img --conf 0.5

# 子码流 (当前使用)
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/Streaming/Channels/102" --weights ./best.pt --device cpu --view-img --conf 0.5

# 备用路径1
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/h264/ch1/main/av_stream" --weights ./best.pt --device cpu --view-img --conf 0.5

# 备用路径2
python3 detect.py --source "rtsp://admin:matrix@192.168.86.32:554/cam1/mpeg4" --weights ./best.pt --device cpu --view-img --conf 0.5

# 大华摄像头
python3 detect.py --source "rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0" --weights ./best.pt --device cpu --view-img --conf 0.4

# 通用RTSP摄像头
python3 detect.py --source "rtsp://admin:123456@192.168.1.100:554/stream1" --weights ./best.pt --device cpu --view-img --conf 0.4
```

### 视频文件检测
```bash
python3 detect.py --source ../result/fire1.mp4 --weights ./best.pt --device cpu --conf 0.4
```

### 参数说明
- `--source`: 输入源（0=摄像头, RTSP地址, 视频文件路径）
- `--weights`: 模型权重文件
- `--device`: 设备选择（cpu/cuda）
- `--view-img`: 显示检测窗口
- `--conf`: 置信度阈值（0.1-1.0）
- `--img-size`: 输入图像大小（默认640）