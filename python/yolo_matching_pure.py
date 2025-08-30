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
            "device": "cpu",  # 设备选择: cpu, cuda
        }

        # YOLO网络（如果可用）
        self.yolo_net = None
        self.yolo_classes = []
        self.yolo_output_layers = []
        
        # 设备设置
        self.device = "cpu"  # 默认使用CPU

        # 性能统计
        self.performance_stats = {
            "fps": 0.0,
            "latency_ms": 0.0,
            "last_inference_time": 0.0,
            "inference_count": 0,
            "total_time": 0.0
        }

        # 初始化YOLO（如果模型可用）
        self._init_yolo()

    def update_performance_stats(self, inference_time: float):
        """
        更新性能统计数据
        
        Args:
            inference_time: 推理时间（秒）
        """
        self.performance_stats["last_inference_time"] = inference_time
        self.performance_stats["latency_ms"] = inference_time * 1000  # 转换为毫秒
        self.performance_stats["inference_count"] += 1
        self.performance_stats["total_time"] += inference_time
        
        # 计算平均FPS（基于最近的推理时间）
        if inference_time > 0:
            self.performance_stats["fps"] = 1.0 / inference_time

    def get_performance_stats(self) -> Dict[str, float]:
        """
        获取性能统计数据
        
        Returns:
            包含FPS和延迟信息的字典
        """
        return self.performance_stats.copy()

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

    def get_model_info(self, model_path: str = ""):
        """
        获取模型信息，包括类别数量和类别名称

        Args:
            model_path: YOLO模型文件路径

        Returns:
            dict: 包含模型信息的字典，包括classes等
        """
        try:
            if not model_path or not model_path.strip():
                # 返回COCO数据集的默认类别信息
                return {
                    "classes": {i: f"class_{i}" for i in range(80)},
                    "num_classes": 80,
                    "model_type": "default_coco"
                }

            # 尝试加载模型获取类别信息
            if model_path.endswith('.pt'):
                try:
                    # 尝试使用ultralytics加载
                    from ultralytics import YOLO
                    model = YOLO(model_path)
                    if hasattr(model, 'names') and model.names:
                        return {
                            "classes": model.names,
                            "num_classes": len(model.names),
                            "model_type": "ultralytics_pt"
                        }
                except ImportError:
                    logger.warning("ultralytics库不可用，无法获取详细模型信息")
                except Exception as e:
                    logger.warning(f"加载PT模型信息失败: {e}")

            elif model_path.endswith('.onnx'):
                try:
                    # 对于ONNX模型，尝试从文件名或其他方式推断
                    # 这里可以根据实际需要扩展
                    return {
                        "classes": {i: f"class_{i}" for i in range(80)},
                        "num_classes": 80,
                        "model_type": "onnx_inferred"
                    }
                except Exception as e:
                    logger.warning(f"获取ONNX模型信息失败: {e}")

            # 默认返回COCO类别
            return {
                "classes": {i: f"class_{i}" for i in range(80)},
                "num_classes": 80,
                "model_type": "default_fallback"
            }

        except Exception as e:
            logger.error(f"获取模型信息失败: {e}")
            return {
                "classes": {i: f"class_{i}" for i in range(80)},
                "num_classes": 80,
                "model_type": "error_fallback"
            }
    
    def set_device(self, device_id: str):
        """
        设置计算设备
        
        Args:
            device_id: 设备ID (如 "cpu", "cuda:0", "cuda:1" 等)
        """
        try:
            self.device = device_id
            logger.info(f"纯YOLO匹配器设备设置为: {device_id}")
            
            # 如果设备改变，可能需要重新加载模型
            # 这里可以添加模型重新加载的逻辑
            
        except Exception as e:
            logger.error(f"设置纯YOLO设备失败: {e}")
            self.device = "cpu"  # 回退到CPU

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

            # 只使用PyTorch后端进行推理
            logger.info("使用PyTorch后端")
            return self._detect_with_pytorch(image, config)

        except Exception as e:
            logger.error(f"真实YOLO检测失败: {e}")
            return []





    def _detect_with_pytorch(
        self, image: np.ndarray, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        使用PyTorch模型检测（支持.pt和.onnx格式）
        """
        try:
            # 尝试导入PyTorch相关库
            try:
                import torch
                import torchvision
            except ImportError as e:
                logger.error(f"PyTorch库未安装: {e}")
                logger.error("请使用命令安装: pip install torch torchvision")
                return []

            model_path = config.get("model_path", "")
            confidence_threshold = config.get("confidence_threshold", 0.5)

            logger.info(f"使用PyTorch加载模型: {model_path}")

            # 支持的格式：.pt 和 .onnx
            if model_path.endswith((".pt", ".onnx")):
                return self._load_ultralytics_model(image, model_path, confidence_threshold)
            else:
                logger.error(f"不支持的模型格式: {model_path}")
                logger.error("支持的格式: .pt（推荐）, .onnx")
                return []

        except Exception as e:
            logger.error(f"PyTorch检测失败: {e}")
            return []

    def _load_ultralytics_model(
        self, image: np.ndarray, model_path: str, confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """使用ultralytics加载YOLO模型（支持.pt和.onnx格式）"""
        try:
            from ultralytics import YOLO
            import torch

            model = YOLO(model_path)
            
            # 智能设备选择
            device = self.device
            
            # 检查CUDA可用性
            if device.startswith('cuda') and not torch.cuda.is_available():
                logger.warning(f"CUDA设备 {device} 不可用，回退到CPU")
                device = 'cpu'
            
            # 根据模型格式设置设备
            if model_path.endswith('.onnx'):
                # ONNX模型需要检查ONNX Runtime的CUDA支持
                try:
                    import onnxruntime as ort
                    providers = ort.get_available_providers()
                    if device.startswith('cuda') and 'CUDAExecutionProvider' in providers:
                        logger.info(f"ONNX模型将使用CUDA设备: {device}")
                        logger.info(f"ONNX Runtime providers: {providers}")
                    elif device.startswith('cuda'):
                        logger.warning("ONNX Runtime不支持CUDA，使用CPU")
                        device = 'cpu'
                    else:
                        logger.info(f"ONNX模型使用CPU设备")
                except ImportError:
                    logger.warning("未找到onnxruntime，ONNX推理可能失败")
            else:
                # .pt模型可以使用model.to()移动到设备
                if device != "cpu":
                    model.to(device)
                    logger.info(f"PyTorch模型已移动到设备: {device}")
            
            # 执行推理并记录时间
            logger.info(f"开始推理，使用设备: {device}")
            start_time = time.time()
            results = model(image, conf=confidence_threshold, verbose=False, device=device)
            inference_time = time.time() - start_time
            
            # 更新性能统计
            self.update_performance_stats(inference_time)

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

            # 记录性能信息
            stats = self.get_performance_stats()
            logger.info(f"Ultralytics YOLO检测到 {len(detections)} 个目标")
            logger.info(f"推理性能 - FPS: {stats['fps']:.1f}, 延迟: {stats['latency_ms']:.1f}ms")
            return detections

        except ImportError:
            logger.error("未安装ultralytics库")
            logger.error("请使用命令安装: pip install ultralytics")
            return []
        except Exception as e:
            logger.error(f"ultralytics模型加载失败: {e}")
            logger.error("建议：如果使用ONNX模型遇到问题，请尝试使用.pt格式的模型")
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

                # 获取性能统计
                stats = self.get_performance_stats()

                # 构造匹配结果，包含所有检测结果和性能数据
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
                    "performance": stats,  # 添加性能数据
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
