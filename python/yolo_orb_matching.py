#!/usr/bin/env python3
"""
YOLO+ORB混合匹配模块
结合YOLO目标检测和ORB特征匹配的高级匹配算法
"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple, List, Dict, Any, Union
import logging
from .feature_matching import orb_matcher

# 配置日志
logger = logging.getLogger(__name__)


class YOLOORBMatchingEngine:
    """
    YOLO+ORB混合匹配引擎
    先使用YOLO检测目标区域，再使用ORB进行精确匹配
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

        # 默认ORB配置（复用feature_matching的配置）
        self.default_orb_config = {
            "nfeatures": 500,  # 减少特征点数量以提高速度
            "scaleFactor": 1.2,
            "nlevels": 8,
            "edgeThreshold": 15,
            "fastThreshold": 10,
            "distance_threshold": 0.75,
            "min_matches": 8,
            "max_retries": 2,
            "use_ratio_test": True,
            "use_cross_check": False,
        }

        # 默认混合匹配配置
        self.default_hybrid_config = {
            "use_yolo_preprocessing": True,  # 是否使用YOLO预处理
            "yolo_roi_expansion": 0.1,  # YOLO检测区域扩展比例
            "min_yolo_confidence": 0.3,  # 最小YOLO置信度
            "orb_fallback": True,  # YOLO失败时是否回退到纯ORB匹配
            "multi_scale_matching": True,  # 多尺度匹配
            "scale_factors": [0.8, 1.0, 1.2],  # 尺度因子
        }

        # YOLO网络（如果可用）
        self.yolo_net = None
        self.yolo_classes = []
        self.yolo_output_layers = []
        
        # 设备设置
        self.device = "cpu"  # 默认使用CPU

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
                # 返回默认类别信息
                classes_dict = {i: name for i, name in enumerate(self.yolo_classes)}
                return {
                    "classes": classes_dict,
                    "num_classes": len(self.yolo_classes),
                    "model_type": "default_yolo_orb"
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
                            "model_type": "ultralytics_yolo_orb"
                        }
                except ImportError:
                    logger.warning("ultralytics库不可用，无法获取详细模型信息")
                except Exception as e:
                    logger.warning(f"加载PT模型信息失败: {e}")

            # 默认返回内置类别
            classes_dict = {i: name for i, name in enumerate(self.yolo_classes)}
            return {
                "classes": classes_dict,
                "num_classes": len(self.yolo_classes),
                "model_type": "builtin_yolo_orb"
            }

        except Exception as e:
            logger.error(f"获取YOLO+ORB模型信息失败: {e}")
            classes_dict = {i: f"class_{i}" for i in range(80)}
            return {
                "classes": classes_dict,
                "num_classes": 80,
                "model_type": "error_fallback_yolo_orb"
            }
    
    def set_device(self, device_id: str):
        """
        设置计算设备
        
        Args:
            device_id: 设备ID (如 "cpu", "cuda:0", "cuda:1" 等)
        """
        try:
            self.device = device_id
            logger.info(f"YOLO+ORB匹配器设备设置为: {device_id}")
            
            # 如果设备改变，可能需要重新加载模型
            # 这里可以添加模型重新加载的逻辑
            
        except Exception as e:
            logger.error(f"设置YOLO+ORB设备失败: {e}")
            self.device = "cpu"  # 回退到CPU

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

            # YOLO检测功能开发中
            logger.warning("YOLO检测功能开发中")
            detections = []

            logger.info(f"YOLO检测到 {len(detections)} 个目标")
            return detections

        except Exception as e:
            logger.error(f"YOLO检测失败: {e}")
            return []

    def match_with_yolo_orb(
        self,
        template_image: np.ndarray,
        target_image: np.ndarray,
        config: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        使用YOLO+ORB混合匹配

        Args:
            template_image: 模板图像
            target_image: 目标图像
            config: 匹配配置

        Returns:
            匹配结果字典
        """
        try:
            if config is None:
                config = self.default_hybrid_config.copy()

            # 合并配置
            hybrid_config = self.default_hybrid_config.copy()
            hybrid_config.update(config)

            logger.info("开始YOLO+ORB混合匹配")

            # 第一阶段：YOLO目标检测
            if hybrid_config.get("use_yolo_preprocessing", True):
                yolo_detections = self.detect_objects_yolo(target_image, config)

                if yolo_detections:
                    # 在YOLO检测区域内进行ORB匹配
                    best_result = None
                    best_confidence = 0

                    for detection in yolo_detections:
                        roi_result = self._match_in_roi(
                            template_image, target_image, detection, config
                        )

                        if (
                            roi_result
                            and roi_result.get("confidence", 0) > best_confidence
                        ):
                            best_result = roi_result
                            best_confidence = roi_result["confidence"]

                    if best_result:
                        logger.info("YOLO+ORB匹配成功")
                        return best_result

            # 第二阶段：回退到纯ORB匹配
            if hybrid_config.get("orb_fallback", True):
                logger.info("回退到纯ORB匹配")

                # 使用ORB匹配器进行匹配
                orb_result = orb_matcher.match_features(
                    template_image, target_image, hybrid_config
                )

                if orb_result:
                    orb_result["method"] = "YOLO+ORB_fallback"
                    logger.info("ORB回退匹配成功")
                    return orb_result

            logger.warning("YOLO+ORB混合匹配失败")
            return None

        except Exception as e:
            logger.error(f"YOLO+ORB混合匹配异常: {e}")
            return None

    def _match_in_roi(
        self,
        template_image: np.ndarray,
        target_image: np.ndarray,
        detection: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        在YOLO检测的ROI区域内进行ORB匹配

        Args:
            template_image: 模板图像
            target_image: 目标图像
            detection: YOLO检测结果
            config: 匹配配置

        Returns:
            匹配结果字典
        """
        try:
            # 获取ROI区域
            x = detection["x"]
            y = detection["y"]
            w = detection["width"]
            h = detection["height"]

            # 扩展ROI区域
            expansion = config.get("yolo_roi_expansion", 0.1)
            expand_w = int(w * expansion)
            expand_h = int(h * expansion)

            roi_x = max(0, x - expand_w)
            roi_y = max(0, y - expand_h)
            roi_w = min(target_image.shape[1] - roi_x, w + 2 * expand_w)
            roi_h = min(target_image.shape[0] - roi_y, h + 2 * expand_h)

            # 提取ROI
            roi = target_image[roi_y : roi_y + roi_h, roi_x : roi_x + roi_w]

            # 在ROI内进行ORB匹配
            roi_result = orb_matcher.match_features(template_image, roi, config)

            if roi_result:
                # 调整坐标到原图坐标系
                if "x" in roi_result:
                    roi_result["x"] += roi_x
                if "y" in roi_result:
                    roi_result["y"] += roi_y

                # 添加YOLO信息
                roi_result["yolo_confidence"] = detection["confidence"]
                roi_result["method"] = "YOLO+ORB"

                return roi_result

            return None

        except Exception as e:
            logger.error(f"ROI内ORB匹配失败: {e}")
            return None

    def draw_yolo_orb_result(
        self,
        template_image: np.ndarray,
        target_image: np.ndarray,
        result: Dict[str, Any],
        show_yolo_info: bool = True,
    ) -> np.ndarray:
        """
        绘制YOLO+ORB匹配结果

        Args:
            template_image: 模板图像
            target_image: 目标图像
            result: 匹配结果
            show_yolo_info: 是否显示YOLO信息

        Returns:
            绘制了结果的图像
        """
        try:
            if result.get("method") == "YOLO+ORB":
                # 使用ORB的绘制方法作为基础
                result_image = orb_matcher.draw_matches(
                    template_image, target_image, result
                )

                # 添加YOLO检测框
                if show_yolo_info and "yolo_confidence" in result:
                    x, y = result.get("x", 0), result.get("y", 0)
                    w, h = result.get("width", 100), result.get("height", 100)

                    # 绘制YOLO检测框（蓝色）
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    # 添加YOLO标签
                    yolo_conf = result["yolo_confidence"]
                    label = f"YOLO: {yolo_conf:.3f}"

                    cv2.putText(
                        result_image,
                        label,
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 0, 0),
                        2,
                    )

                return result_image
            else:
                # 使用标准ORB绘制
                return orb_matcher.draw_matches(template_image, target_image, result)

        except Exception as e:
            logger.error(f"绘制YOLO+ORB结果失败: {e}")
            return target_image


# 创建全局实例
yolo_orb_matcher = YOLOORBMatchingEngine()


def match_yolo_orb(template_image, target_image, **kwargs):
    """便捷函数：YOLO+ORB混合匹配"""
    return yolo_orb_matcher.match_with_yolo_orb(template_image, target_image, kwargs)


def detect_yolo_objects(image, **kwargs):
    """便捷函数：YOLO目标检测"""
    return yolo_orb_matcher.detect_objects_yolo(image, kwargs)
