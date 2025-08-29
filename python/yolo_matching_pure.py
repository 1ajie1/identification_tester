#!/usr/bin/env python3
"""
纯YOLO匹配模块
仅使用YOLO目标检测进行匹配，不包含ORB特征匹配
"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple, List, Dict, Any, Union
import logging

# 配置日志
logger = logging.getLogger(__name__)


class PureYOLOMatchingEngine:
    """
    纯YOLO匹配引擎
    仅使用YOLO目标检测进行匹配
    """

    def __init__(self):
        # 默认YOLO配置
        self.default_yolo_config = {
            "confidence_threshold": 0.5,  # 置信度阈值
            "nms_threshold": 0.4,  # NMS阈值
            "input_size": (416, 416),  # 输入尺寸
            "model_path": "",  # YOLO模型路径
            "config_path": "",  # YOLO配置路径
            "classes_path": "",  # 类别文件路径
        }

        # YOLO网络（如果可用）
        self.yolo_net = None
        self.yolo_classes = []
        self.yolo_output_layers = []

        # 初始化YOLO（如果模型可用）
        self._init_yolo()

    def _init_yolo(self, model_path: str = ""):
        """
        初始化YOLO网络

        Args:
            model_path: YOLO模型文件路径
        """
        try:
            if model_path and model_path.strip():
                # 加载真实的YOLO模型
                logger.info(f"尝试加载YOLO模型: {model_path}")
                # 这里应该根据模型文件格式加载模型
                # 示例：
                # if model_path.endswith('.weights'):
                #     self.yolo_net = cv2.dnn.readNet(model_path, config_path)
                # elif model_path.endswith('.pt'):
                #     # 使用torch加载PyTorch模型
                #     pass
                # elif model_path.endswith('.onnx'):
                #     # 使用ONNX Runtime加载
                #     pass
                logger.warning(f"YOLO模型加载功能开发中: {model_path}")
            else:
                logger.info("YOLO模型初始化（模拟模式）")

            # 模拟一些常见的类别
            self.yolo_classes = [
                "person",
                "bicycle",
                "car",
                "motorbike",
                "aeroplane",
                "bus",
                "train",
                "truck",
                "boat",
                "traffic light",
                "fire hydrant",
                "stop sign",
                "parking meter",
                "bench",
                "bird",
                "cat",
                "dog",
                "horse",
                "sheep",
                "cow",
                "elephant",
                "bear",
                "zebra",
                "giraffe",
                "backpack",
                "umbrella",
                "handbag",
                "tie",
                "suitcase",
                "frisbee",
                "skis",
                "snowboard",
                "sports ball",
                "kite",
                "baseball bat",
                "baseball glove",
                "skateboard",
                "surfboard",
                "tennis racket",
                "bottle",
                "wine glass",
                "cup",
                "fork",
                "knife",
                "spoon",
                "bowl",
                "banana",
                "apple",
                "sandwich",
                "orange",
                "broccoli",
                "carrot",
                "hot dog",
                "pizza",
                "donut",
                "cake",
                "chair",
                "sofa",
                "pottedplant",
                "bed",
                "diningtable",
                "toilet",
                "tvmonitor",
                "laptop",
                "mouse",
                "remote",
                "keyboard",
                "cell phone",
                "microwave",
                "oven",
                "toaster",
                "sink",
                "refrigerator",
                "book",
                "clock",
                "vase",
                "scissors",
                "teddy bear",
                "hair drier",
                "toothbrush",
            ]

            logger.info(f"YOLO类别数量: {len(self.yolo_classes)}")

        except Exception as e:
            logger.warning(f"YOLO初始化失败: {e}")

    def reload_model(self, model_path: str):
        """
        重新加载YOLO模型

        Args:
            model_path: YOLO模型文件路径
        """
        try:
            logger.info(f"重新加载YOLO模型: {model_path}")
            self._init_yolo(model_path)
            return True
        except Exception as e:
            logger.error(f"重新加载YOLO模型失败: {e}")
            return False

    def detect_objects_yolo(
        self, image: np.ndarray, config: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        使用YOLO检测图像中的对象

        Args:
            image: 输入图像
            config: YOLO配置参数

        Returns:
            检测结果列表
        """
        try:
            if config is None:
                config = self.default_yolo_config.copy()

            # 合并配置
            yolo_config = self.default_yolo_config.copy()
            yolo_config.update(config)

            logger.info("开始YOLO目标检测")

            # 检查是否需要重新加载模型
            model_path = yolo_config.get("model_path", "")
            if model_path and model_path.strip():
                self.reload_model(model_path)
                # 如果有模型文件，尝试使用真实的YOLO检测
                return self._detect_with_real_yolo(image, yolo_config)
            else:
                # 没有模型文件，无法进行检测
                logger.error("无法进行YOLO检测：未提供模型文件路径")
                logger.error(
                    "请在算法参数设置中选择有效的YOLO模型文件(.onnx, .pt, .weights)"
                )
                return []

        except Exception as e:
            logger.error(f"YOLO检测失败: {e}")
            return []

    def _detect_with_real_yolo(
        self, image: np.ndarray, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        使用真实的YOLO模型进行检测
        """
        try:
            import os

            model_path = config.get("model_path", "")

            if not os.path.exists(model_path):
                logger.error(f"YOLO模型文件不存在: {model_path}")
                logger.error("请检查模型文件路径是否正确")
                return []

            # 优先尝试使用PyTorch加载所有格式的模型
            # PyTorch对YOLO模型支持更全面，包括YOLOv5/v8等
            pytorch_result = self._detect_with_pytorch(image, config)
            if pytorch_result:
                return pytorch_result

            # PyTorch失败或不可用，根据文件格式选择备用方案
            if model_path.endswith(".onnx"):
                logger.info("PyTorch不可用，尝试使用OpenCV DNN加载ONNX模型")
                return self._detect_with_opencv_dnn(image, config)
            elif model_path.endswith(".weights"):
                logger.info("PyTorch不可用，尝试使用Darknet加载权重文件")
                return self._detect_with_darknet(image, config)
            elif model_path.endswith(".pt"):
                logger.error("PyTorch模型加载失败且无备用方案")
                logger.error("请确保已安装PyTorch: pip install torch torchvision")
                return []
            else:
                logger.error(f"不支持的模型格式: {model_path}")
                logger.error("支持的格式: .pt（推荐）, .onnx, .weights")
                return []

        except Exception as e:
            logger.error(f"真实YOLO检测失败: {e}")
            return []

    def _detect_with_opencv_dnn(
        self, image: np.ndarray, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        使用OpenCV DNN模块检测ONNX模型
        """
        try:
            model_path = config.get("model_path", "")
            confidence_threshold = config.get("confidence_threshold", 0.5)
            nms_threshold = config.get("nms_threshold", 0.4)

            # 加载ONNX模型
            net = cv2.dnn.readNetFromONNX(model_path)

            # 预处理图像
            blob = cv2.dnn.blobFromImage(
                image, 1 / 255.0, (640, 640), swapRB=True, crop=False
            )
            net.setInput(blob)

            # 前向推理
            outputs = net.forward()

            # 解析输出
            detections = []
            h, w = image.shape[:2]

            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]

                    if confidence > confidence_threshold:
                        # 转换坐标
                        center_x = int(detection[0] * w)
                        center_y = int(detection[1] * h)
                        width = int(detection[2] * w)
                        height = int(detection[3] * h)

                        x = int(center_x - width / 2)
                        y = int(center_y - height / 2)

                        detections.append(
                            {
                                "x": x,
                                "y": y,
                                "width": width,
                                "height": height,
                                "confidence": float(confidence),
                                "class_id": int(class_id),
                                "class_name": (
                                    self.yolo_classes[class_id]
                                    if class_id < len(self.yolo_classes)
                                    else f"class_{class_id}"
                                ),
                            }
                        )

            # 应用NMS
            if len(detections) > 1:
                boxes = [[d["x"], d["y"], d["width"], d["height"]] for d in detections]
                scores = [d["confidence"] for d in detections]
                indices = cv2.dnn.NMSBoxes(
                    boxes, scores, confidence_threshold, nms_threshold
                )

                if len(indices) > 0:
                    detections = [detections[i] for i in indices.flatten()]

            logger.info(f"OpenCV DNN检测到 {len(detections)} 个目标")
            return detections

        except Exception as e:
            logger.error(f"OpenCV DNN检测失败: {e}")
            logger.error("可能原因：模型文件损坏、格式不兼容或缺少依赖")
            return []

    def _detect_with_darknet(
        self, image: np.ndarray, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        使用Darknet权重文件检测
        """
        try:
            # Darknet检测需要配置文件(.cfg)和类别文件(.names)
            logger.error("Darknet检测功能暂未实现")
            logger.error("需要对应的.cfg配置文件和.names类别文件")
            logger.error("建议使用.onnx格式的模型文件")
            return []
        except Exception as e:
            logger.error(f"Darknet检测失败: {e}")
            return []

    def _detect_with_pytorch(
        self, image: np.ndarray, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        使用PyTorch模型检测
        """
        try:
            # 尝试导入PyTorch相关库
            try:
                import torch
                import torchvision
            except ImportError as e:
                logger.warning(f"PyTorch库未安装: {e}")
                logger.info("可使用命令安装: pip install torch torchvision")
                return []

            model_path = config.get("model_path", "")
            confidence_threshold = config.get("confidence_threshold", 0.5)

            logger.info(f"尝试使用PyTorch加载模型: {model_path}")

            # 尝试加载不同格式的模型
            if model_path.endswith(".pt"):
                return self._load_pytorch_model(image, model_path, confidence_threshold)
            elif model_path.endswith(".onnx"):
                return self._load_onnx_with_torch(
                    image, model_path, confidence_threshold
                )
            elif model_path.endswith(".weights"):
                # 对于weights文件，尝试使用ultralytics
                return self._load_ultralytics_model(
                    image, model_path, confidence_threshold
                )
            else:
                logger.warning(f"PyTorch不支持此格式: {model_path}")
                return []

        except Exception as e:
            logger.warning(f"PyTorch检测失败: {e}")
            return []

    def _load_pytorch_model(
        self, image: np.ndarray, model_path: str, confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """加载PyTorch .pt模型"""
        try:
            import torch

            # 尝试使用ultralytics库（推荐）
            try:
                from ultralytics import YOLO

                model = YOLO(model_path)
                results = model(image, conf=confidence_threshold, verbose=False)

                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = box.conf[0].cpu().numpy()
                            cls = int(box.cls[0].cpu().numpy())

                            detections.append(
                                {
                                    "x": int(x1),
                                    "y": int(y1),
                                    "width": int(x2 - x1),
                                    "height": int(y2 - y1),
                                    "confidence": float(conf),
                                    "class_id": cls,
                                    "class_name": model.names.get(cls, f"class_{cls}"),
                                }
                            )

                logger.info(f"Ultralytics YOLO检测到 {len(detections)} 个目标")
                return detections

            except ImportError:
                logger.warning("未安装ultralytics库，尝试使用torch直接加载")
                # 尝试直接使用torch加载
                model = torch.load(model_path, map_location="cpu")
                logger.warning("直接torch加载暂未实现推理逻辑")
                return []

        except Exception as e:
            logger.error(f"PyTorch模型加载失败: {e}")
            return []

    def _load_onnx_with_torch(
        self, image: np.ndarray, model_path: str, confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """使用PyTorch加载ONNX模型"""
        try:
            # 尝试使用ultralytics加载ONNX
            try:
                from ultralytics import YOLO

                model = YOLO(model_path)
                results = model(image, conf=confidence_threshold, verbose=False)

                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = box.conf[0].cpu().numpy()
                            cls = int(box.cls[0].cpu().numpy())

                            detections.append(
                                {
                                    "x": int(x1),
                                    "y": int(y1),
                                    "width": int(x2 - x1),
                                    "height": int(y2 - y1),
                                    "confidence": float(conf),
                                    "class_id": cls,
                                    "class_name": f"class_{cls}",
                                }
                            )

                logger.info(f"Ultralytics ONNX检测到 {len(detections)} 个目标")
                return detections

            except ImportError:
                logger.warning("ultralytics库不可用，回退到OpenCV")
                return []

        except Exception as e:
            logger.warning(f"PyTorch ONNX加载失败: {e}")
            return []

    def _load_ultralytics_model(
        self, image: np.ndarray, model_path: str, confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """使用ultralytics加载weights文件"""
        try:
            from ultralytics import YOLO

            # ultralytics通常不直接支持.weights文件
            logger.warning("ultralytics不直接支持.weights文件")
            logger.info("建议将.weights转换为.pt格式")
            return []

        except ImportError:
            logger.warning("ultralytics库不可用")
            return []
        except Exception as e:
            logger.warning(f"ultralytics加载失败: {e}")
            return []

    def _detect_with_simulated_yolo(
        self, image: np.ndarray, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        模拟YOLO检测（用于演示和测试）
        """
        try:
            logger.info("使用模拟YOLO检测进行演示")

            # 获取图像尺寸
            h, w = image.shape[:2]

            # 模拟检测一些常见对象
            detections = []

            # 模拟检测结果：在图像的不同区域生成一些假的检测框
            import random

            random.seed(42)  # 固定种子以获得一致的结果

            confidence_threshold = config.get("confidence_threshold", 0.5)

            # 生成1-3个模拟检测
            num_detections = random.randint(1, 3)

            for i in range(num_detections):
                # 随机生成检测框
                x = random.randint(10, max(10, w - 200))
                y = random.randint(10, max(10, h - 200))
                width = random.randint(50, min(150, w - x - 10))
                height = random.randint(50, min(150, h - y - 10))

                # 随机置信度（高于阈值）
                confidence = random.uniform(confidence_threshold + 0.1, 0.95)

                # 随机类别
                class_names = [
                    "person",
                    "car",
                    "bicycle",
                    "dog",
                    "cat",
                    "bottle",
                    "chair",
                    "laptop",
                ]
                class_name = random.choice(class_names)
                class_id = class_names.index(class_name)

                detections.append(
                    {
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": class_name,
                    }
                )

            logger.info(f"模拟YOLO检测到 {len(detections)} 个目标")
            return detections

        except Exception as e:
            logger.error(f"模拟YOLO检测失败: {e}")
            return []

    def match_with_pure_yolo(
        self,
        template_image: np.ndarray,
        target_image: np.ndarray,
        config: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        使用纯YOLO进行匹配

        Args:
            template_image: 模板图像
            target_image: 目标图像
            config: 匹配配置

        Returns:
            匹配结果字典
        """
        try:
            if config is None:
                config = self.default_yolo_config.copy()

            # 合并配置
            yolo_config = self.default_yolo_config.copy()
            yolo_config.update(config)

            logger.info("开始纯YOLO匹配")

            # 对目标图像进行YOLO检测
            detections = self.detect_objects_yolo(target_image, config)

            if detections:
                # 找到置信度最高的检测结果
                best_detection = max(detections, key=lambda x: x.get("confidence", 0))

                # 构造匹配结果，包含所有检测结果
                result = {
                    "x": best_detection["x"],
                    "y": best_detection["y"],
                    "width": best_detection["width"],
                    "height": best_detection["height"],
                    "confidence": best_detection["confidence"],
                    "class_name": best_detection.get("class_name", "unknown"),
                    "class_id": best_detection.get("class_id", -1),
                    "method": "Pure_YOLO",
                    "match_time": time.time(),
                    "detection_count": len(detections),
                    "all_detections": detections,  # 包含所有检测结果
                }

                logger.info("纯YOLO匹配成功")
                return result
            else:
                logger.warning("纯YOLO匹配失败，未检测到任何目标")
                return None

        except Exception as e:
            logger.error(f"纯YOLO匹配异常: {e}")
            return None

    def draw_yolo_result(
        self,
        image: np.ndarray,
        result: Dict[str, Any],
        show_confidence: bool = True,
    ) -> np.ndarray:
        """
        绘制纯YOLO匹配结果

        Args:
            image: 原始图像
            result: 匹配结果
            show_confidence: 是否显示置信度

        Returns:
            绘制了结果的图像
        """
        try:
            result_image = image.copy()

            # 获取所有检测结果
            all_detections = result.get("all_detections", [])

            # 如果没有所有检测结果，回退到单个结果
            if not all_detections:
                all_detections = [
                    {
                        "x": result.get("x", 0),
                        "y": result.get("y", 0),
                        "width": result.get("width", 100),
                        "height": result.get("height", 100),
                        "confidence": result.get("confidence", 0),
                        "class_name": result.get("class_name", "unknown"),
                    }
                ]

            # 绘制所有检测框
            colors = [
                (0, 0, 255),  # 红色
                (0, 255, 0),  # 绿色
                (255, 0, 0),  # 蓝色
                (0, 255, 255),  # 黄色
                (255, 0, 255),  # 洋红色
                (255, 255, 0),  # 青色
            ]

            for i, detection in enumerate(all_detections):
                # 获取检测框信息
                x = int(detection["x"])
                y = int(detection["y"])
                width = int(detection["width"])
                height = int(detection["height"])
                confidence = detection.get("confidence", 0)
                class_name = detection.get("class_name", "unknown")

                # 选择颜色
                color = colors[i % len(colors)]

                # 绘制检测框
                cv2.rectangle(result_image, (x, y), (x + width, y + height), color, 3)

                # 添加标签
                if show_confidence:
                    label = f"{class_name}: {confidence:.3f}"
                else:
                    label = class_name

                # 计算文字位置
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                label_y = y - 10 if y - 10 > 10 else y + height + 25

                # 绘制标签背景
                cv2.rectangle(
                    result_image,
                    (x, label_y - label_size[1] - 10),
                    (x + label_size[0] + 10, label_y + 5),
                    color,
                    -1,
                )

                # 绘制标签文字（白色）
                cv2.putText(
                    result_image,
                    label,
                    (x + 5, label_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

            return result_image

        except Exception as e:
            logger.error(f"绘制纯YOLO结果失败: {e}")
            return image


# 创建全局实例
pure_yolo_matcher = PureYOLOMatchingEngine()


def match_pure_yolo(template_image, target_image, **kwargs):
    """便捷函数：纯YOLO匹配"""
    return pure_yolo_matcher.match_with_pure_yolo(template_image, target_image, kwargs)


def detect_yolo_objects(image, **kwargs):
    """便捷函数：YOLO目标检测"""
    return pure_yolo_matcher.detect_objects_yolo(image, kwargs)
