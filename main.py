import ctypes
import sys
import os
import json
import numpy as np
import logging


from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QmlElement, QQmlApplicationEngine
from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl, Qt
print("策略：", QGuiApplication.highDpiScaleFactorRoundingPolicy())

from python.template_matching import template_matcher
from python.feature_matching import orb_matcher
from python.screen_capture import screen_capture
from python.yolo_orb_matching import yolo_orb_matcher
from python.yolo_matching_pure import pure_yolo_matcher

QML_IMPORT_NAME = "ImageMatcher"

# 配置日志
logger = logging.getLogger(__name__)
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ImageMatcherController(QObject):
    # 信号定义
    modeChanged = Signal(int)  # 模式改变信号 (0: 双图片模式, 1: 屏幕窗口模式)
    algorithmModeChanged = Signal(
        int
    )  # 算法模式改变信号 (0: 模板匹配, 1: ORB, 2: YOLO+ORB, 3: 纯YOLO)
    needleImage = Signal(str)  # 第一张图片选择信号
    haystackImage = Signal(str)  # 第二张图片选择信号
    windowSelected = Signal(str)  # 屏幕窗口选择信号
    screenAreaImageChanged = Signal(str)  # 屏幕区域图片变更信号
    logAdded = Signal(str, str)  # 日志添加信号 (message, type)
    showMatchResult = Signal(str, str)  # 显示匹配结果信号 (image_path, title)
    showScreenMatchOverlay = Signal(
        int, int, int, int, float, str
    )  # 显示屏幕匹配覆盖层 (x, y, width, height, confidence, title)
    showMultipleDetections = Signal(str)  # 显示多个检测结果 (detections_json)
    realtimeDetectionStateChanged = Signal(bool)  # 实时检测状态变化 (active)
    clearAllDetections = Signal()  # 清除所有检测结果

    def __init__(self):
        super().__init__()
        self._current_mode = 0  # 0: 双图片模式, 1: 屏幕窗口模式
        self._algorithm_mode = 0  # 0: 模板匹配, 1: ORB, 2: YOLO+ORB, 3: 纯YOLO
        self._image1_path = ""
        self._image2_path = ""
        self._selected_window = ""
        self._selected_window_rect = {"x": 0, "y": 0, "width": 0, "height": 0}
        self._screen_area_image_path = ""  # 屏幕区域截图路径
        self._area_capture_timer = None  # 区域截取定时器
        
        # 实时检测相关
        self._realtime_detection_active = False
        self._realtime_timer = None
        self._realtime_interval = 500  # 毫秒，检测间隔
        
        # 动态颜色映射
        self._class_colors = {}  # 类别ID到颜色的映射
        self._model_classes = {}  # 模型类别信息

        # 算法配置参数
        self._algorithm_settings = {
            0: {  # 模板匹配
                "method": "TM_CCOEFF_NORMED",
                "threshold": 0.8,
                "max_retries": 3,
                "retry_delay": 1.0,
            },
            1: {  # ORB特征匹配
                "nfeatures": 1000,
                "scaleFactor": 1.2,
                "nlevels": 8,
                "edgeThreshold": 15,
                "fastThreshold": 10,
                "distance_threshold": 0.8,
                "min_matches": 4,
                "max_retries": 3,
                "use_ratio_test": False,
                "use_cross_check": False,
            },
            2: {  # YOLO+ORB混合
                "yolo_confidence": 0.5,
                "nms_threshold": 0.4,
                "orb_nfeatures": 500,
                "model_path": "",
            },
            3: {  # 纯YOLO
                "confidence_threshold": 0.5,
                "nms_threshold": 0.4,
                "model_path": "",
            },
        }

    # 当前模式属性
    @Property(int, notify=modeChanged)
    def currentMode(self):
        return self._current_mode

    @currentMode.setter
    def currentMode(self, mode):
        if self._current_mode != mode:
            self._current_mode = mode
            self.modeChanged.emit(mode)

    # 算法模式属性
    @Property(int, notify=algorithmModeChanged)
    def algorithmMode(self):
        return self._algorithm_mode

    @algorithmMode.setter
    def algorithmMode(self, mode):
        if self._algorithm_mode != mode:
            self._algorithm_mode = mode
            self.algorithmModeChanged.emit(mode)

    # 图片路径属性
    @Property(str, notify=needleImage)
    def image1Path(self):
        return self._image1_path

    @Property(str, notify=haystackImage)
    def image2Path(self):
        return self._image2_path

    @Property(str, notify=windowSelected)
    def selectedWindow(self):
        return self._selected_window

    @Property('QVariant', notify=windowSelected)
    def selectedWindowRect(self):
        return self._selected_window_rect

    @Property(str, notify=screenAreaImageChanged)
    def screenAreaImagePath(self):
        return self._screen_area_image_path

    @Slot(int)
    def switchMode(self, mode):
        """切换输入模式"""
        # 如果切换到双图片模式，停止区域截取
        if mode == 0 and self._area_capture_timer:
            self._area_capture_timer.stop()
            self._area_capture_timer = None
            self._screen_area_image_path = ""
            self.screenAreaImageChanged.emit("")
            self.logAdded.emit("已停止屏幕区域实时显示", "info")

        self.currentMode = mode
        print(f"切换到输入模式: {'双图片匹配' if mode == 0 else '屏幕窗口匹配'}")

    @Slot(int)
    def switchAlgorithmMode(self, mode):
        """切换算法模式"""
        self.algorithmMode = mode
        algorithm_names = [
            "模板匹配",
            "OpenCV ORB特征匹配",
            "YOLO+ORB混合匹配",
            "纯YOLO匹配",
        ]
        print(f"切换到算法模式: {algorithm_names[mode]}")

    @Slot(str)
    def selectImage1(self, path):
        """选择第一张图片"""
        self._image1_path = path
        self.needleImage.emit(path)
        print(f"选择第一张图片: {path}")

    @Slot(str)
    def selectImage2(self, path):
        """选择第二张图片"""
        self._image2_path = path
        self.haystackImage.emit(path)
        print(f"选择第二张图片: {path}")

    @Slot(str, str, result=str)
    def selectWindow(self, window_title, window_rect_json=""):
        """选择屏幕窗口"""
        self._selected_window = window_title

        # 解析窗口矩形信息
        if window_rect_json:
            try:
                import json

                rect_data = json.loads(window_rect_json)
                self._selected_window_rect = {
                    "x": rect_data.get("x", 0),
                    "y": rect_data.get("y", 0),
                    "width": rect_data.get("width", 0),
                    "height": rect_data.get("height", 0),
                }
            except:
                self._selected_window_rect = {"x": 0, "y": 0, "width": 0, "height": 0}

        self.windowSelected.emit(window_title)
        print(f"选择窗口: {window_title}, 区域: {self._selected_window_rect}")
        return "success"

    @Slot(str, result=str)
    def selectScreenArea(self, area_rect_json):
        """选择屏幕区域"""
        try:
            import json
            import os
            import tempfile
            from PySide6.QtCore import QTimer

            rect_data = json.loads(area_rect_json)

            # 保留一位小数
            x = round(rect_data.get("x", 0), 1)
            y = round(rect_data.get("y", 0), 1)
            width = round(rect_data.get("width", 0), 1)
            height = round(rect_data.get("height", 0), 1)

            self._selected_window_rect = {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }

            area_info = f"屏幕区域 ({x}, {y}, {width}×{height})"
            self._selected_window = area_info

            # 停止之前的定时器
            if self._area_capture_timer:
                self._area_capture_timer.stop()
                self._area_capture_timer = None

            # 创建定时器，每33ms截取一次屏幕区域（30FPS）
            self._area_capture_timer = QTimer()
            self._area_capture_timer.timeout.connect(self._captureScreenArea)
            self._area_capture_timer.start(33)  # 33ms间隔，约30FPS

            # 立即截取一次
            self._captureScreenArea()

            self.windowSelected.emit(area_info)
            self.logAdded.emit(f"开始实时显示屏幕区域: {area_info}", "success")
            print(f"选择屏幕区域: {self._selected_window_rect}")
            return "success"

        except Exception as e:
            print(f"解析屏幕区域失败: {e}")
            self._selected_window_rect = {"x": 0, "y": 0, "width": 0, "height": 0}
            self.logAdded.emit(f"选择屏幕区域失败: {str(e)}", "error")
            return "error"

    def _captureScreenArea(self):
        """截取屏幕区域"""
        try:
            import os
            import tempfile
            import cv2
            import logging
            from datetime import datetime
            
            logger = logging.getLogger(__name__)

            if (
                self._selected_window_rect["width"] <= 0
                or self._selected_window_rect["height"] <= 0
            ):
                return

            # 获取QML传递的逻辑坐标
            logical_x = self._selected_window_rect["x"]
            logical_y = self._selected_window_rect["y"]
            logical_width = self._selected_window_rect["width"]
            logical_height = self._selected_window_rect["height"]
            
            # 将逻辑坐标转换为物理坐标
            # QML返回的是逻辑坐标，需要乘以DPI缩放因子得到物理像素坐标
            physical_x = int(logical_x * screen_capture.dpi_scale)
            physical_y = int(logical_y * screen_capture.dpi_scale)
            physical_width = int(logical_width * screen_capture.dpi_scale)
            physical_height = int(logical_height * screen_capture.dpi_scale)
            
            region = (physical_x, physical_y, physical_width, physical_height)
          
            # 使用我们修复的截图功能
            screenshot_cv = screen_capture.capture_screen(region)
            
            if screenshot_cv is None:
                print("屏幕区域截图失败")
                return

            # 保存到临时文件
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"screen_area_{timestamp}.png"
            filepath = os.path.join(temp_dir, filename)

            # 使用OpenCV保存图像
            success = cv2.imwrite(filepath, screenshot_cv)
            if not success:
                print(f"保存截图失败: {filepath}")
                return
            
            # 清理旧文件（保留最近5个）
            self._cleanupOldScreenshots(temp_dir)

            # 更新路径并发送信号
            old_path = self._screen_area_image_path
            self._screen_area_image_path = filepath
            self.screenAreaImageChanged.emit(filepath)

            # 删除旧文件
            if old_path and os.path.exists(old_path) and old_path != filepath:
                try:
                    os.remove(old_path)
                except:
                    pass

        except Exception as e:
            print(f"截取屏幕区域失败: {e}")
            self.logAdded.emit(f"截取屏幕区域失败: {str(e)}", "error")

    def _cleanupOldScreenshots(self, temp_dir):
        """清理旧的截图文件"""
        try:
            import glob
            import os

            # 找到所有screen_area_开头的文件
            pattern = os.path.join(temp_dir, "screen_area_*.png")
            files = glob.glob(pattern)

            # 按修改时间排序，保留最新的5个
            files.sort(key=os.path.getmtime, reverse=True)

            # 删除多余的文件
            for file_to_delete in files[5:]:
                try:
                    os.remove(file_to_delete)
                except:
                    pass
        except Exception as e:
            print(f"清理旧截图失败: {e}")

    @Slot()
    def startMatching(self):
        """开始匹配"""
        # 清除之前的检测结果
        self.clearAllDetections.emit()
        
        algorithm_names = [
            "模板匹配",
            "OpenCV ORB特征匹配",
            "YOLO+ORB混合匹配",
            "纯YOLO匹配",
        ]
        current_settings = self.getCurrentAlgorithmSettings()

        self.logAdded.emit(
            f"开始执行匹配 - 算法: {algorithm_names[self._algorithm_mode]}", "info"
        )
        self.logAdded.emit(f"算法参数: {current_settings}", "info")

        if self._current_mode == 0:
            # 双图片匹配模式
            if not self._image1_path or not self._image2_path:
                self.logAdded.emit("请先选择两张图片", "error")
                return

            if not os.path.exists(self._image1_path) or not os.path.exists(
                self._image2_path
            ):
                self.logAdded.emit("图片文件不存在", "error")
                return

            self.logAdded.emit(
                f"模板图片: {os.path.basename(self._image1_path)}", "info"
            )
            self.logAdded.emit(
                f"目标图片: {os.path.basename(self._image2_path)}", "info"
            )

            if self._algorithm_mode == 0:  # 模板匹配
                self._executeImageTemplateMatching()
            elif self._algorithm_mode == 1:  # ORB特征匹配
                self._executeORBMatching()
            elif self._algorithm_mode == 2:  # YOLO+ORB混合
                self._executeYOLOORBMatching()
            elif self._algorithm_mode == 3:  # 纯YOLO
                self._executePureYOLOMatching()

        else:
            # 屏幕窗口匹配模式
            if not self._selected_window:
                self.logAdded.emit("请先选择目标窗口", "error")
                return

            # 对于纯YOLO模式，不需要模板图片
            if self._algorithm_mode != 3:  # 非纯YOLO模式需要模板图片
                if not self._image1_path:
                    self.logAdded.emit("请先选择模板图片", "error")
                    return

                if not os.path.exists(self._image1_path):
                    self.logAdded.emit("模板图片文件不存在", "error")
                    return

                self.logAdded.emit(
                    f"模板图片: {os.path.basename(self._image1_path)}", "info"
                )

            self.logAdded.emit(f"目标窗口: {self._selected_window}", "info")

            if self._algorithm_mode == 0:  # 模板匹配
                self._executeScreenTemplateMatching()
            elif self._algorithm_mode == 1:  # ORB特征匹配
                self._executeScreenORBMatching()
            elif self._algorithm_mode == 2:  # YOLO+ORB混合
                self._executeScreenYOLOORBMatching()
            elif self._algorithm_mode == 3:  # 纯YOLO
                self._executeScreenPureYOLOMatching()

    def _executeImageTemplateMatching(self):
        """执行图片间的模板匹配"""
        try:
            import cv2
            import numpy as np

            config = self.getCurrentAlgorithmSettings()

            # 读取图片
            template = cv2.imread(self._image1_path, cv2.IMREAD_COLOR)
            target = cv2.imread(self._image2_path, cv2.IMREAD_COLOR)

            if template is None or target is None:
                self.logAdded.emit("无法读取图片文件", "error")
                return

            # 获取匹配参数
            method_name = config.get("method", "TM_CCOEFF_NORMED")
            threshold = config.get("threshold", 0.8)
            max_retries = config.get("max_retries", 3)
            retry_delay = config.get("retry_delay", 1.0)

            # 方法映射
            methods = {
                "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
                "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
                "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
            }

            method = methods.get(method_name, cv2.TM_CCOEFF_NORMED)

            self.logAdded.emit(f"开始模板匹配，方法: {method_name}", "info")

            # 执行匹配
            result = cv2.matchTemplate(target, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 根据方法选择合适的值和位置
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                match_val = min_val
                match_loc = min_loc
                confidence = 1 - match_val
            else:
                match_val = max_val
                match_loc = max_loc
                confidence = match_val

            template_h, template_w = template.shape[:2]

            if confidence >= threshold:
                # 匹配成功
                center_x = match_loc[0] + template_w // 2
                center_y = match_loc[1] + template_h // 2

                self.logAdded.emit(f"匹配成功！", "success")
                self.logAdded.emit(
                    f"匹配位置: ({match_loc[0]}, {match_loc[1]})", "success"
                )
                self.logAdded.emit(f"中心点: ({center_x}, {center_y})", "success")
                self.logAdded.emit(f"置信度: {confidence:.3f}", "success")
                self.logAdded.emit(f"模板尺寸: {template_w} x {template_h}", "info")

                # 创建结果图片并显示
                self._showMatchResult(
                    target, match_loc, template_w, template_h, confidence
                )

            else:
                self.logAdded.emit(
                    f"匹配失败，置信度 {confidence:.3f} 低于阈值 {threshold}", "warning"
                )

        except Exception as e:
            self.logAdded.emit(f"模板匹配过程中发生错误: {str(e)}", "error")

    def _executeScreenTemplateMatching(self):
        """执行屏幕模板匹配"""
        try:
            config = self.getCurrentAlgorithmSettings()
            result = template_matcher.find_template_on_screen(self._image1_path, config)

            if result:
                self.logAdded.emit("屏幕匹配成功！", "success")
                self.logAdded.emit(
                    f"匹配位置: ({result['left']}, {result['top']})", "success"
                )
                self.logAdded.emit(
                    f"中心点: ({result['center_x']}, {result['center_y']})", "success"
                )
                self.logAdded.emit(f"置信度: {result['confidence']:.3f}", "success")
                self.logAdded.emit(f"匹配方法: {result['method']}", "info")

                # 创建屏幕截图结果并显示
                self._showScreenMatchResult(result)
            else:
                self.logAdded.emit("屏幕匹配失败，未找到匹配项", "warning")

        except Exception as e:
            self.logAdded.emit(f"屏幕匹配过程中发生错误: {str(e)}", "error")

    def _executeORBMatching(self):
        """执行ORB特征匹配"""
        try:
            import cv2
            import tempfile

            config = self.getCurrentAlgorithmSettings()

            # 读取图片
            template = cv2.imread(self._image1_path, cv2.IMREAD_COLOR)
            target = cv2.imread(self._image2_path, cv2.IMREAD_COLOR)

            if template is None or target is None:
                self.logAdded.emit("无法读取图片文件", "error")
                return

            self.logAdded.emit("开始ORB特征匹配", "info")
            self.logAdded.emit(
                f"ORB参数: nfeatures={config.get('nfeatures', 1000)}, "
                f"scaleFactor={config.get('scaleFactor', 1.2)}",
                "info",
            )

            # 执行ORB匹配
            result = orb_matcher.match_features(template, target, config)

            if result and result["num_matches"] >= config.get("min_matches", 10):
                # 匹配成功
                self.logAdded.emit("✅ ORB特征匹配成功！", "success")
                self.logAdded.emit(f"📊 匹配统计信息:", "info")
                self.logAdded.emit(
                    f"  • 总匹配点数: {result['num_matches']}", "success"
                )
                self.logAdded.emit(f"  • 内点数量: {result['num_inliers']}", "success")
                self.logAdded.emit(
                    f"  • 内点比例: {result['inlier_ratio']:.3f}", "success"
                )
                self.logAdded.emit(f"  • 置信度: {result['confidence']:.3f}", "success")
                self.logAdded.emit(
                    f"  • 平均距离: {result['avg_distance']:.2f}", "info"
                )

                if result["center_point"]:
                    center = result["center_point"]
                    self.logAdded.emit(
                        f"  • 匹配中心: ({center['x']}, {center['y']})", "success"
                    )

                if result["bounding_box"]:
                    bbox = result["bounding_box"]
                    self.logAdded.emit(
                        f"  • 边界框: {bbox['width']}x{bbox['height']} 像素", "info"
                    )

                # 创建结果图片并显示
                self._showORBMatchResult(template, target, result)

            else:
                if result:
                    self.logAdded.emit(
                        f"ORB匹配失败，匹配点数 {result['num_matches']} 少于最小要求 {config.get('min_matches', 10)}",
                        "warning",
                    )
                else:
                    self.logAdded.emit("ORB匹配失败，未找到足够的匹配点", "warning")

        except Exception as e:
            self.logAdded.emit(f"ORB特征匹配过程中发生错误: {str(e)}", "error")

    def _executeScreenORBMatching(self):
        """执行屏幕ORB特征匹配"""
        try:
            import cv2
            import tempfile

            config = self.getCurrentAlgorithmSettings()

            # 读取模板图片
            template = cv2.imread(self._image1_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logAdded.emit("无法读取模板图片文件", "error")
                return

            self.logAdded.emit("开始屏幕ORB特征匹配", "info")
            self.logAdded.emit(
                f"ORB参数: nfeatures={config.get('nfeatures', 1000)}, "
                f"scaleFactor={config.get('scaleFactor', 1.2)}",
                "info",
            )

            # 捕获窗口截图
            window_screenshot = screen_capture.capture_window(
                self._selected_window, self._selected_window_rect
            )

            if window_screenshot is None:
                self.logAdded.emit("窗口截图失败", "error")
                return

            # 执行ORB匹配
            result = orb_matcher.match_features(template, window_screenshot, config)

            if result and result["num_matches"] >= config.get("min_matches", 10):
                # 匹配成功
                self.logAdded.emit("✅ 屏幕ORB特征匹配成功！", "success")
                self.logAdded.emit(f"📊 匹配统计信息:", "info")
                self.logAdded.emit(
                    f"  • 总匹配点数: {result['num_matches']}", "success"
                )
                self.logAdded.emit(f"  • 内点数量: {result['num_inliers']}", "success")
                self.logAdded.emit(
                    f"  • 内点比例: {result['inlier_ratio']:.3f}", "success"
                )
                self.logAdded.emit(f"  • 置信度: {result['confidence']:.3f}", "success")
                self.logAdded.emit(
                    f"  • 平均距离: {result['avg_distance']:.2f}", "info"
                )

                if result["center_point"]:
                    center = result["center_point"]
                    # 物理坐标转换为逻辑坐标，再调整到屏幕坐标
                    logical_x = center["x"] / screen_capture.dpi_scale
                    logical_y = center["y"] / screen_capture.dpi_scale
                    screen_x = logical_x + self._selected_window_rect["x"]
                    screen_y = logical_y + self._selected_window_rect["y"]
                    
                    logger.info(f"ORB匹配坐标转换:")
                    logger.info(f"  物理坐标: ({center['x']}, {center['y']})")
                    logger.info(f"  逻辑坐标: ({logical_x:.1f}, {logical_y:.1f})")
                    logger.info(f"  屏幕坐标: ({screen_x:.1f}, {screen_y:.1f})")
                    logger.info(f"  DPI缩放: {screen_capture.dpi_scale}")
                    
                    self.logAdded.emit(
                        f"  • 屏幕坐标: ({screen_x:.1f}, {screen_y:.1f})", "success"
                    )

                if result["bounding_box"]:
                    bbox = result["bounding_box"]
                    self.logAdded.emit(
                        f"  • 边界框: {bbox['width']}x{bbox['height']} 像素", "info"
                    )

                # 创建结果图片并显示
                self._showScreenORBMatchResult(template, window_screenshot, result)

                # 显示屏幕覆盖层
                if result["bounding_box"]:
                    bbox = result["bounding_box"]
                    # 物理坐标转换为逻辑坐标
                    logical_left = bbox["left"] / screen_capture.dpi_scale
                    logical_top = bbox["top"] / screen_capture.dpi_scale
                    logical_width = bbox["width"] / screen_capture.dpi_scale
                    logical_height = bbox["height"] / screen_capture.dpi_scale
                    
                    screen_x = logical_left + self._selected_window_rect["x"]
                    screen_y = logical_top + self._selected_window_rect["y"]
                    
                    self.showScreenMatchOverlay.emit(
                        screen_x,
                        screen_y,
                        logical_width,
                        logical_height,
                        result["confidence"],
                        "ORB特征匹配",
                    )

            else:
                if result:
                    self.logAdded.emit(
                        f"屏幕ORB匹配失败，匹配点数 {result['num_matches']} 少于最小要求 {config.get('min_matches', 10)}",
                        "warning",
                    )
                else:
                    self.logAdded.emit("屏幕ORB匹配失败，未找到足够的匹配点", "warning")

        except Exception as e:
            self.logAdded.emit(f"屏幕ORB特征匹配过程中发生错误: {str(e)}", "error")

    def _executeScreenYOLOORBMatching(self):
        """执行屏幕YOLO+ORB混合匹配"""
        try:
            import cv2
            import tempfile

            config = self.getCurrentAlgorithmSettings()

            # 读取模板图片
            template = cv2.imread(self._image1_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logAdded.emit("无法读取模板图片文件", "error")
                return

            self.logAdded.emit("开始屏幕YOLO+ORB混合匹配", "info")

            # 获取当前算法配置
            config = self._algorithm_settings.get(self._algorithm_mode, {})

            # 检查模型文件路径
            model_path = config.get("model_path", "")
            if model_path:
                self.logAdded.emit(f"使用YOLO模型: {model_path}", "info")

            # 捕获窗口截图
            window_screenshot = screen_capture.capture_window(
                self._selected_window, self._selected_window_rect
            )

            if window_screenshot is None:
                self.logAdded.emit("窗口截图失败", "error")
                return

            # 执行YOLO+ORB匹配
            result = yolo_orb_matcher.match_with_yolo_orb(
                template, window_screenshot, config
            )

            if result and result.get("confidence", 0) > 0.5:
                # 匹配成功
                method = result.get("method", "YOLO+ORB")
                self.logAdded.emit(f"✅ 屏幕{method}匹配成功！", "success")
                self.logAdded.emit(f"📊 匹配统计信息:", "info")

                if "num_matches" in result:
                    self.logAdded.emit(
                        f"  • 总匹配点数: {result['num_matches']}", "success"
                    )
                if "num_inliers" in result:
                    self.logAdded.emit(
                        f"  • 内点数量: {result['num_inliers']}", "success"
                    )

                self.logAdded.emit(f"  • 置信度: {result['confidence']:.3f}", "success")

                if "yolo_confidence" in result:
                    self.logAdded.emit(
                        f"  • YOLO置信度: {result['yolo_confidence']:.3f}", "info"
                    )
                if "orb_confidence" in result:
                    self.logAdded.emit(
                        f"  • ORB置信度: {result['orb_confidence']:.3f}", "info"
                    )

                if result.get("center_point"):
                    center = result["center_point"]
                    # 物理坐标转换为逻辑坐标，再调整到屏幕坐标
                    logical_x = center["x"] / screen_capture.dpi_scale
                    logical_y = center["y"] / screen_capture.dpi_scale
                    screen_x = logical_x + self._selected_window_rect["x"]
                    screen_y = logical_y + self._selected_window_rect["y"]
                    
                    logger.info(f"YOLO+ORB匹配坐标转换:")
                    logger.info(f"  物理坐标: ({center['x']}, {center['y']})")
                    logger.info(f"  逻辑坐标: ({logical_x:.1f}, {logical_y:.1f})")
                    logger.info(f"  屏幕坐标: ({screen_x:.1f}, {screen_y:.1f})")
                    logger.info(f"  DPI缩放: {screen_capture.dpi_scale}")
                    
                    self.logAdded.emit(
                        f"  • 屏幕坐标: ({screen_x:.1f}, {screen_y:.1f})", "success"
                    )

                if result.get("bounding_box"):
                    bbox = result["bounding_box"]
                    self.logAdded.emit(
                        f"  • 边界框: {bbox['width']}x{bbox['height']} 像素", "info"
                    )

                # 创建结果图片并显示
                self._showScreenYOLOORBMatchResult(template, window_screenshot, result)

                # 显示屏幕覆盖层
                if result.get("bounding_box"):
                    bbox = result["bounding_box"]
                    # 物理坐标转换为逻辑坐标
                    logical_left = bbox["left"] / screen_capture.dpi_scale
                    logical_top = bbox["top"] / screen_capture.dpi_scale
                    logical_width = bbox["width"] / screen_capture.dpi_scale
                    logical_height = bbox["height"] / screen_capture.dpi_scale
                    
                    screen_x = logical_left + self._selected_window_rect["x"]
                    screen_y = logical_top + self._selected_window_rect["y"]
                    
                    self.showScreenMatchOverlay.emit(
                        screen_x,
                        screen_y,
                        logical_width,
                        logical_height,
                        result["confidence"],
                        method,
                    )

            else:
                self.logAdded.emit("屏幕YOLO+ORB混合匹配失败", "warning")

        except Exception as e:
            self.logAdded.emit(f"屏幕YOLO+ORB匹配过程中发生错误: {str(e)}", "error")

    def _executeScreenPureYOLOMatching(self):
        """执行屏幕纯YOLO匹配"""
        try:
            import cv2
            import tempfile

            # 检查屏幕区域截图
            if not self._screen_area_image_path:
                self.logAdded.emit("请先选择屏幕区域", "error")
                return

            self.logAdded.emit("开始屏幕纯YOLO检测", "info")

            # 获取当前算法配置
            config = self._algorithm_settings.get(self._algorithm_mode, {})

            # 检查模型文件路径
            model_path = config.get("model_path", "")
            if model_path:
                self.logAdded.emit(f"使用YOLO模型: {model_path}", "info")
            else:
                self.logAdded.emit("使用模拟YOLO检测进行演示", "info")

            # 读取屏幕截图
            window_screenshot = cv2.imread(
                self._screen_area_image_path, cv2.IMREAD_COLOR
            )

            if window_screenshot is None:
                self.logAdded.emit("屏幕截图加载失败", "error")
                return

            # 对于纯YOLO，我们只需要检测窗口截图中的对象，不需要模板
            # 直接使用YOLO检测器检测所有对象
            detections = pure_yolo_matcher.detect_objects_yolo(
                window_screenshot, config
            )

            if detections:
                # 构造结果，使用置信度最高的检测作为主要结果
                best_detection = max(detections, key=lambda x: x.get("confidence", 0))
                result = {
                    "x": best_detection["x"],
                    "y": best_detection["y"],
                    "width": best_detection["width"],
                    "height": best_detection["height"],
                    "confidence": best_detection["confidence"],
                    "class_name": best_detection.get("class_name", "unknown"),
                    "class_id": best_detection.get("class_id", -1),
                    "method": "Pure_YOLO_Screen",
                    "detection_count": len(detections),
                    "all_detections": detections,
                }
            else:
                result = None
                # 检测失败，输出详细错误信息
                model_path = config.get("model_path", "")
                if not model_path or not model_path.strip():
                    self.logAdded.emit("❌ YOLO检测失败：未设置模型文件", "error")
                    self.logAdded.emit("请在算法参数设置中选择YOLO模型文件", "info")
                    self.logAdded.emit("支持格式：.pt（推荐）、.onnx、.weights", "info")
                elif not os.path.exists(model_path):
                    self.logAdded.emit(f"❌ YOLO检测失败：模型文件不存在", "error")
                    self.logAdded.emit(f"文件路径：{model_path}", "error")
                    self.logAdded.emit("请检查文件路径是否正确", "info")
                elif not any(
                    model_path.endswith(ext) for ext in [".onnx", ".pt", ".weights"]
                ):
                    self.logAdded.emit(f"❌ YOLO检测失败：不支持的模型格式", "error")
                    self.logAdded.emit(
                        f"当前文件：{os.path.basename(model_path)}", "error"
                    )
                    self.logAdded.emit("支持格式：.pt（推荐）、.onnx、.weights", "info")
                else:
                    self.logAdded.emit("❌ YOLO检测失败：模型加载或推理错误", "error")
                    self.logAdded.emit(
                        "可能原因：模型文件损坏、格式不兼容或缺少依赖", "warning"
                    )
                    if model_path.endswith(".pt"):
                        self.logAdded.emit(
                            "建议安装: pip install torch ultralytics", "info"
                        )
                    elif model_path.endswith(".onnx"):
                        self.logAdded.emit(
                            "建议安装: pip install ultralytics（优先）或使用OpenCV",
                            "info",
                        )
                    elif model_path.endswith(".weights"):
                        self.logAdded.emit(
                            "建议转换为.pt格式或提供.cfg和.names文件", "info"
                        )
                return

            if result:
                confidence = result.get("confidence", 0)
                class_name = result.get("class_name", "unknown")
                detection_count = result.get("detection_count", 1)
                all_detections = result.get("all_detections", [])

                self.logAdded.emit("✅ 屏幕纯YOLO匹配成功！", "success")
                self.logAdded.emit(f"  • 检测到 {detection_count} 个目标", "info")
                self.logAdded.emit(f"  • 主要类别: {class_name}", "info")
                self.logAdded.emit(f"  • 最高置信度: {confidence:.3f}", "info")

                if result.get("x") is not None:
                    x, y = result["x"], result["y"]
                    w, h = result["width"], result["height"]
                    self.logAdded.emit(f"  • 主要位置: ({x}, {y})", "success")
                    self.logAdded.emit(f"  • 主要尺寸: {w}x{h} 像素", "info")

                # 创建结果图片并显示
                self._showScreenPureYOLOMatchResult(None, window_screenshot, result)

                # 发送多个检测结果到前端显示
                if all_detections:
                    # 转换坐标到屏幕坐标系和相对坐标
                    screen_detections = []
                    
                    # 获取区域尺寸
                    area_width = self._selected_window_rect["width"]
                    area_height = self._selected_window_rect["height"]
                    
                    for detection in all_detections:
                        screen_detection = detection.copy()
                        
                        # YOLO检测返回的是物理像素坐标，需要转换为逻辑坐标再加上偏移
                        # 物理坐标 -> 逻辑坐标
                        logical_x = detection["x"] / screen_capture.dpi_scale
                        logical_y = detection["y"] / screen_capture.dpi_scale
                        logical_width = detection["width"] / screen_capture.dpi_scale
                        logical_height = detection["height"] / screen_capture.dpi_scale
                        
                        # 逻辑坐标 + 逻辑偏移 = 屏幕逻辑坐标
                        screen_detection["screen_x"] = (
                            self._selected_window_rect["x"] + logical_x
                        )
                        screen_detection["screen_y"] = (
                            self._selected_window_rect["y"] + logical_y
                        )
                        # 更新尺寸为逻辑坐标
                        screen_detection["width"] = logical_width
                        screen_detection["height"] = logical_height
                        
                        # 计算相对坐标（0-1范围）
                        screen_detection["relative_x"] = logical_x / area_width
                        screen_detection["relative_y"] = logical_y / area_height
                        screen_detection["relative_width"] = logical_width / area_width
                        screen_detection["relative_height"] = logical_height / area_height
                        
                        # 添加动态颜色信息
                        class_id = detection.get("class_id", 0)
                        screen_detection["border_color"] = self._get_class_color(class_id)
                        
                        screen_detections.append(screen_detection)

                    # 发送检测结果到前端
                    detections_json = json.dumps(screen_detections)
                    self.showMultipleDetections.emit(detections_json)
                else:
                    # 显示单个屏幕匹配覆盖层（向后兼容）
                    # 物理坐标转换为逻辑坐标
                    logical_x = x / screen_capture.dpi_scale
                    logical_y = y / screen_capture.dpi_scale
                    logical_w = w / screen_capture.dpi_scale
                    logical_h = h / screen_capture.dpi_scale
                    
                    # 逻辑坐标 + 逻辑偏移 = 屏幕逻辑坐标
                    screen_x = self._selected_window_rect["x"] + logical_x
                    screen_y = self._selected_window_rect["y"] + logical_y

                    logger.info(f"单个YOLO检测坐标转换:")
                    logger.info(f"  物理坐标: ({x}, {y}, {w}, {h})")
                    logger.info(f"  逻辑坐标: ({logical_x:.1f}, {logical_y:.1f}, {logical_w:.1f}, {logical_h:.1f})")
                    logger.info(f"  屏幕坐标: ({screen_x:.1f}, {screen_y:.1f})")

                    self.showScreenMatchOverlay.emit(
                        screen_x,
                        screen_y,
                        logical_w,
                        logical_h,
                        confidence,
                        "纯YOLO匹配",
                    )

            else:
                self.logAdded.emit("屏幕纯YOLO匹配失败", "warning")

        except Exception as e:
            self.logAdded.emit(f"屏幕纯YOLO匹配过程中发生错误: {str(e)}", "error")

    def _executeYOLOORBMatching(self):
        """执行YOLO+ORB混合匹配"""
        try:
            import cv2
            import tempfile

            config = self.getCurrentAlgorithmSettings()

            # 读取图片
            template = cv2.imread(self._image1_path, cv2.IMREAD_COLOR)
            target = cv2.imread(self._image2_path, cv2.IMREAD_COLOR)

            if template is None or target is None:
                self.logAdded.emit("无法读取图片文件", "error")
                return

            self.logAdded.emit("开始YOLO+ORB混合匹配", "info")

            # 检查模型文件路径
            model_path = config.get("model_path", "")
            if model_path:
                self.logAdded.emit(f"使用YOLO模型: {model_path}", "info")

            # 执行YOLO+ORB匹配
            result = yolo_orb_matcher.match_with_yolo_orb(template, target, config)

            if result and result.get("confidence", 0) > 0.5:
                # 匹配成功
                method = result.get("method", "YOLO+ORB")
                self.logAdded.emit(f"✅ {method}匹配成功！", "success")
                self.logAdded.emit(f"📊 匹配统计信息:", "info")

                if "num_matches" in result:
                    self.logAdded.emit(
                        f"  • 总匹配点数: {result['num_matches']}", "success"
                    )
                if "num_inliers" in result:
                    self.logAdded.emit(
                        f"  • 内点数量: {result['num_inliers']}", "success"
                    )

                self.logAdded.emit(f"  • 置信度: {result['confidence']:.3f}", "success")

                if "yolo_confidence" in result:
                    self.logAdded.emit(
                        f"  • YOLO置信度: {result['yolo_confidence']:.3f}", "info"
                    )
                if "orb_confidence" in result:
                    self.logAdded.emit(
                        f"  • ORB置信度: {result['orb_confidence']:.3f}", "info"
                    )

                if result.get("center_point"):
                    center = result["center_point"]
                    self.logAdded.emit(
                        f"  • 匹配中心: ({center['x']}, {center['y']})", "success"
                    )

                if result.get("bounding_box"):
                    bbox = result["bounding_box"]
                    self.logAdded.emit(
                        f"  • 边界框: {bbox['width']}x{bbox['height']} 像素", "info"
                    )

                # 创建结果图片并显示
                self._showYOLOORBMatchResult(template, target, result)

            else:
                self.logAdded.emit("YOLO+ORB混合匹配失败", "warning")

        except Exception as e:
            self.logAdded.emit(f"YOLO+ORB匹配过程中发生错误: {str(e)}", "error")

    def _executePureYOLOMatching(self):
        """执行纯YOLO匹配"""
        try:
            import cv2

            # 检查图片路径
            if not self._image1_path or not self._image2_path:
                self.logAdded.emit("请先选择两张图片", "error")
                return

            # 读取图片
            template = cv2.imread(self._image1_path)
            target = cv2.imread(self._image2_path)

            if template is None or target is None:
                self.logAdded.emit("图片加载失败", "error")
                return

            self.logAdded.emit("开始纯YOLO匹配", "info")

            # 获取当前算法配置
            config = self._algorithm_settings.get(self._algorithm_mode, {})

            # 检查模型文件路径
            model_path = config.get("model_path", "")
            if model_path:
                self.logAdded.emit(f"使用YOLO模型: {model_path}", "info")

            # 执行纯YOLO匹配
            result = pure_yolo_matcher.match_with_pure_yolo(template, target, config)

            if result:
                confidence = result.get("confidence", 0)
                class_name = result.get("class_name", "unknown")

                self.logAdded.emit("✅ 纯YOLO匹配成功！", "success")
                self.logAdded.emit(f"  • 检测类别: {class_name}", "info")
                self.logAdded.emit(f"  • 置信度: {confidence:.3f}", "info")

                if result.get("x") is not None:
                    x, y = result["x"], result["y"]
                    w, h = result["width"], result["height"]
                    self.logAdded.emit(f"  • 位置: ({x}, {y})", "success")
                    self.logAdded.emit(f"  • 尺寸: {w}x{h} 像素", "info")

                # 创建结果图片并显示
                self._showPureYOLOMatchResult(template, target, result)

            else:
                self.logAdded.emit("纯YOLO匹配失败", "warning")

        except Exception as e:
            self.logAdded.emit(f"纯YOLO匹配过程中发生错误: {str(e)}", "error")

    def _showMatchResult(
        self, target_image, match_loc, template_w, template_h, confidence
    ):
        """显示匹配结果"""
        try:
            import cv2
            import tempfile

            # 复制目标图片
            result_image = target_image.copy()

            # 绘制红色矩形框
            top_left = match_loc
            bottom_right = (match_loc[0] + template_w, match_loc[1] + template_h)
            cv2.rectangle(result_image, top_left, bottom_right, (0, 0, 255), 3)

            # 添加置信度标签
            label = f"Confidence: {confidence:.3f}"
            label_pos = (match_loc[0], match_loc[1] - 10)
            cv2.putText(
                result_image,
                label,
                label_pos,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, result_image)

            # 发送信号显示结果
            self.showMatchResult.emit(
                temp_file.name, f"模板匹配结果 - 置信度: {confidence:.3f}"
            )

        except Exception as e:
            self.logAdded.emit(f"创建结果图片失败: {str(e)}", "error")

    def _showScreenMatchResult(self, match_result):
        """显示屏幕匹配结果"""
        try:
            import cv2
            import tempfile

            # 使用修复的截图功能截取全屏
            screenshot_cv = screen_capture.capture_screen()
            if screenshot_cv is None:
                self.logAdded.emit("全屏截图失败", "error")
                return

            # 绘制红色矩形框
            top_left = (match_result["left"], match_result["top"])
            bottom_right = (
                match_result["left"] + match_result["width"],
                match_result["top"] + match_result["height"],
            )
            cv2.rectangle(screenshot_cv, top_left, bottom_right, (0, 0, 255), 3)

            # 添加置信度标签
            label = f"Confidence: {match_result['confidence']:.3f}"
            label_pos = (match_result["left"], match_result["top"] - 10)
            cv2.putText(
                screenshot_cv,
                label,
                label_pos,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, screenshot_cv)

            # 发送信号显示结果
            self.showMatchResult.emit(
                temp_file.name,
                f"屏幕匹配结果 - 置信度: {match_result['confidence']:.3f}",
            )

        except Exception as e:
            self.logAdded.emit(f"创建屏幕结果图片失败: {str(e)}", "error")

    def _showORBMatchResult(self, template_image, target_image, match_result):
        """显示ORB匹配结果"""
        try:
            import cv2
            import tempfile

            # 使用ORB匹配器绘制匹配结果（不显示文字信息）
            result_image = orb_matcher.draw_matches(
                template_image, target_image, match_result, show_info_text=False
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, result_image)

            # 发送信号显示结果
            title = (
                f"ORB特征匹配结果 - 匹配点: {match_result['num_matches']}, "
                f"内点: {match_result['num_inliers']}, "
                f"置信度: {match_result['confidence']:.3f}"
            )

            self.showMatchResult.emit(temp_file.name, title)

        except Exception as e:
            self.logAdded.emit(f"创建ORB结果图片失败: {str(e)}", "error")

    def _showScreenORBMatchResult(
        self, template_image, window_screenshot, match_result
    ):
        """显示屏幕ORB匹配结果"""
        try:
            import cv2
            import tempfile

            # 使用ORB匹配器绘制匹配结果（不显示文字信息）
            result_image = orb_matcher.draw_matches(
                template_image, window_screenshot, match_result, show_info_text=False
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, result_image)

            # 发送信号显示结果
            title = (
                f"屏幕ORB特征匹配结果 - 匹配点: {match_result['num_matches']}, "
                f"内点: {match_result['num_inliers']}, "
                f"置信度: {match_result['confidence']:.3f}"
            )

            self.showMatchResult.emit(temp_file.name, title)

        except Exception as e:
            self.logAdded.emit(f"创建屏幕ORB结果图片失败: {str(e)}", "error")

    def _showScreenYOLOORBMatchResult(
        self, template_image, window_screenshot, match_result
    ):
        """显示屏幕YOLO+ORB匹配结果"""
        try:
            import cv2
            import tempfile

            # 使用YOLO+ORB匹配器绘制匹配结果
            result_image = yolo_orb_matcher.draw_yolo_orb_result(
                template_image, window_screenshot, match_result, show_yolo_info=True
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, result_image)

            # 发送信号显示结果
            method = match_result.get("method", "YOLO+ORB")
            title = f"屏幕{method}匹配结果 - 置信度: {match_result['confidence']:.3f}"

            if "yolo_confidence" in match_result and "orb_confidence" in match_result:
                title += f" (YOLO: {match_result['yolo_confidence']:.3f}, ORB: {match_result['orb_confidence']:.3f})"

            self.showMatchResult.emit(temp_file.name, title)

        except Exception as e:
            self.logAdded.emit(f"创建屏幕YOLO+ORB结果图片失败: {str(e)}", "error")

    def _showYOLOORBMatchResult(self, template_image, target_image, match_result):
        """显示YOLO+ORB匹配结果"""
        try:
            import cv2
            import tempfile

            # 使用YOLO+ORB匹配器绘制匹配结果
            result_image = yolo_orb_matcher.draw_yolo_orb_result(
                template_image, target_image, match_result, show_yolo_info=True
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, result_image)

            # 发送信号显示结果
            method = match_result.get("method", "YOLO+ORB")
            title = f"{method}匹配结果 - 置信度: {match_result['confidence']:.3f}"

            if "yolo_confidence" in match_result and "orb_confidence" in match_result:
                title += f" (YOLO: {match_result['yolo_confidence']:.3f}, ORB: {match_result['orb_confidence']:.3f})"

            self.showMatchResult.emit(temp_file.name, title)

        except Exception as e:
            self.logAdded.emit(f"创建YOLO+ORB结果图片失败: {str(e)}", "error")

    def _showPureYOLOMatchResult(self, template_image, target_image, match_result):
        """显示纯YOLO匹配结果"""
        try:
            import cv2
            import tempfile

            # 使用纯YOLO匹配器绘制匹配结果
            result_image = pure_yolo_matcher.draw_yolo_result(
                target_image, match_result, show_confidence=True
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, result_image)

            # 发送信号显示结果
            class_name = match_result.get("class_name", "unknown")
            confidence = match_result.get("confidence", 0)
            title = f"纯YOLO匹配结果 - 类别: {class_name}, 置信度: {confidence:.3f}"

            self.showMatchResult.emit(temp_file.name, title)

        except Exception as e:
            self.logAdded.emit(f"创建纯YOLO结果图片失败: {str(e)}", "error")

    def _showScreenPureYOLOMatchResult(
        self, template_image, target_image, match_result
    ):
        """显示屏幕纯YOLO匹配结果"""
        try:
            import cv2
            import tempfile

            # 使用纯YOLO匹配器绘制匹配结果
            result_image = pure_yolo_matcher.draw_yolo_result(
                target_image, match_result, show_confidence=True
            )

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            cv2.imwrite(temp_file.name, result_image)

            # 发送信号显示结果
            class_name = match_result.get("class_name", "unknown")
            confidence = match_result.get("confidence", 0)
            title = f"屏幕纯YOLO匹配结果 - 类别: {class_name}, 置信度: {confidence:.3f}"

            self.showMatchResult.emit(temp_file.name, title)

        except Exception as e:
            self.logAdded.emit(f"创建屏幕纯YOLO结果图片失败: {str(e)}", "error")

    @Slot(str, str)
    def addLog(self, message, log_type):
        """添加日志"""
        self.logAdded.emit(message, log_type)

    @Slot(int, str)
    def updateAlgorithmSettings(self, algorithm_index, settings_json):
        """更新算法参数设置"""
        try:
            settings = json.loads(settings_json)
            if algorithm_index in self._algorithm_settings:
                self._algorithm_settings[algorithm_index].update(settings)
                
                # 如果更新了模型路径，需要更新类别颜色映射
                if "model_path" in settings and settings["model_path"]:
                    self._update_model_classes(settings["model_path"])
                
                print(f"算法 {algorithm_index} 参数已更新: {settings}")
                self.logAdded.emit(f"算法参数配置已保存", "success")
            else:
                print(f"未知的算法索引: {algorithm_index}")
                self.logAdded.emit(f"保存参数失败：未知算法", "error")
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            self.logAdded.emit(f"保存参数失败：数据格式错误", "error")
        except Exception as e:
            print(f"更新算法设置时出错: {e}")
            self.logAdded.emit(f"保存参数失败：{str(e)}", "error")

    @Slot(int, result=str)
    def getAlgorithmSettings(self, algorithm_index):
        """获取算法参数设置"""
        if algorithm_index in self._algorithm_settings:
            return json.dumps(self._algorithm_settings[algorithm_index])
        return "{}"

    def getCurrentAlgorithmSettings(self):
        """获取当前算法的参数设置"""
        return self._algorithm_settings.get(self._algorithm_mode, {})
    
    def _generate_class_colors(self, num_classes):
        """
        动态生成类别颜色映射
        
        Args:
            num_classes: 类别数量
            
        Returns:
            dict: 类别ID到颜色的映射
        """
        import colorsys
        
        colors = {}
        
        # 为每个类别生成不同的颜色
        for i in range(num_classes):
            # 使用HSV色彩空间生成均匀分布的颜色
            hue = i / num_classes  # 色相均匀分布
            saturation = 0.8  # 饱和度
            value = 0.9  # 明度
            
            # 转换为RGB
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            
            # 转换为16进制颜色字符串
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            
            colors[i] = hex_color
            
        logger.info(f"为 {num_classes} 个类别生成颜色映射: {colors}")
        return colors
    
    def _update_model_classes(self, model_path):
        """
        更新模型类别信息和颜色映射
        
        Args:
            model_path: 模型文件路径
        """
        try:
            # 尝试从YOLO匹配器获取类别信息
            if self._algorithm_mode == 3:  # 纯YOLO
                model_info = pure_yolo_matcher.get_model_info(model_path)
                if model_info:
                    self._model_classes = model_info.get("classes", {})
                    num_classes = len(self._model_classes) if self._model_classes else 80  # COCO默认80类
                    
                    # 生成颜色映射
                    self._class_colors = self._generate_class_colors(num_classes)
                    
                    self.logAdded.emit(f"加载模型类别信息: {num_classes} 个类别", "success")
                else:
                    # 使用默认设置
                    self._model_classes = {}
                    self._class_colors = self._generate_class_colors(80)  # COCO默认
                    self.logAdded.emit("使用默认类别设置 (80类)", "info")
            elif self._algorithm_mode == 2:  # YOLO+ORB
                model_info = yolo_orb_matcher.get_model_info(model_path)
                if model_info:
                    self._model_classes = model_info.get("classes", {})
                    num_classes = len(self._model_classes) if self._model_classes else 80
                    self._class_colors = self._generate_class_colors(num_classes)
                    self.logAdded.emit(f"加载YOLO+ORB模型类别信息: {num_classes} 个类别", "success")
                else:
                    self._model_classes = {}
                    self._class_colors = self._generate_class_colors(80)
                    self.logAdded.emit("使用默认YOLO+ORB类别设置 (80类)", "info")
                    
        except Exception as e:
            logger.error(f"更新模型类别信息失败: {e}")
            # 使用默认设置
            self._model_classes = {}
            self._class_colors = self._generate_class_colors(80)
            self.logAdded.emit("使用默认类别设置", "warning")
    
    def _get_class_color(self, class_id):
        """
        获取类别对应的颜色
        
        Args:
            class_id: 类别ID
            
        Returns:
            str: 16进制颜色字符串
        """
        if class_id in self._class_colors:
            return self._class_colors[class_id]
        else:
            # 如果没有预定义颜色，动态生成一个
            import colorsys
            hue = (class_id * 137.508) % 360 / 360  # 使用黄金角分割产生均匀分布
            saturation = 0.8
            value = 0.9
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            # 缓存这个颜色
            self._class_colors[class_id] = hex_color
            return hex_color

    @Slot()
    def startRealtimeDetection(self):
        """开始实时检测"""
        if self._realtime_detection_active:
            return
            
        # 清除之前的检测结果
        self.clearAllDetections.emit()
        
        # 检查是否有选择的区域
        if (not self._selected_window_rect or 
            self._selected_window_rect.get("width", 0) <= 0 or 
            self._selected_window_rect.get("height", 0) <= 0):
            self.logAdded.emit("请先选择检测区域", "error")
            return
            
        # 只有纯YOLO模式支持实时检测
        if self._algorithm_mode != 3:
            self.logAdded.emit("实时检测仅支持纯YOLO模式", "warning")
            return
            
        self._realtime_detection_active = True
        self._setupRealtimeTimer()
        self.realtimeDetectionStateChanged.emit(True)
        self.logAdded.emit("开始实时YOLO检测", "success")

    @Slot()
    def stopRealtimeDetection(self):
        """停止实时检测"""
        if not self._realtime_detection_active:
            return
            
        self._realtime_detection_active = False
        if self._realtime_timer:
            self._realtime_timer.stop()
            self._realtime_timer = None
        
        # 清除所有检测结果
        self.clearAllDetections.emit()
        self.realtimeDetectionStateChanged.emit(False)
        self.logAdded.emit("停止实时检测", "info")

    @Slot(int)
    def setRealtimeInterval(self, interval_ms):
        """设置实时检测间隔（毫秒）"""
        self._realtime_interval = max(100, min(5000, interval_ms))  # 限制在100ms-5s之间
        if self._realtime_timer and self._realtime_detection_active:
            self._realtime_timer.setInterval(self._realtime_interval)

    @Property(bool, notify=realtimeDetectionStateChanged)
    def realtimeDetectionActive(self):
        """实时检测状态属性"""
        return self._realtime_detection_active

    def _setupRealtimeTimer(self):
        """设置实时检测定时器"""
        from PySide6.QtCore import QTimer
        
        if self._realtime_timer:
            self._realtime_timer.stop()
            
        self._realtime_timer = QTimer()
        self._realtime_timer.timeout.connect(self._performRealtimeDetection)
        self._realtime_timer.setInterval(self._realtime_interval)
        self._realtime_timer.start()

    def _performRealtimeDetection(self):
        """执行一次实时检测"""
        if not self._realtime_detection_active:
            return
            
        try:
            # 获取当前算法配置
            config = self._algorithm_settings.get(self._algorithm_mode, {})
            
            # 获取QML传递的逻辑坐标
            logical_x = self._selected_window_rect["x"]
            logical_y = self._selected_window_rect["y"]
            logical_width = self._selected_window_rect["width"]
            logical_height = self._selected_window_rect["height"]
            
            # 将逻辑坐标转换为物理坐标
            physical_x = int(logical_x * screen_capture.dpi_scale)
            physical_y = int(logical_y * screen_capture.dpi_scale)
            physical_width = int(logical_width * screen_capture.dpi_scale)
            physical_height = int(logical_height * screen_capture.dpi_scale)
            
            region = (physical_x, physical_y, physical_width, physical_height)
            
            # 截取屏幕区域
            screenshot_cv = screen_capture.capture_screen(region)
            
            if screenshot_cv is None:
                return
                
            # 执行YOLO检测
            result = pure_yolo_matcher.match_with_pure_yolo(None, screenshot_cv, config)
            
            if result and result.get("all_detections"):
                # 转换检测结果坐标
                all_detections = result["all_detections"]
                screen_detections = []
                
                # 获取区域尺寸
                area_width = self._selected_window_rect["width"]
                area_height = self._selected_window_rect["height"]
                
                for detection in all_detections:
                    screen_detection = detection.copy()
                    
                    # 物理坐标转换为逻辑坐标
                    logical_det_x = detection["x"] / screen_capture.dpi_scale
                    logical_det_y = detection["y"] / screen_capture.dpi_scale
                    logical_det_width = detection["width"] / screen_capture.dpi_scale
                    logical_det_height = detection["height"] / screen_capture.dpi_scale
                    
                    # 逻辑坐标 + 逻辑偏移 = 屏幕逻辑坐标
                    screen_detection["screen_x"] = logical_x + logical_det_x
                    screen_detection["screen_y"] = logical_y + logical_det_y
                    screen_detection["width"] = logical_det_width
                    screen_detection["height"] = logical_det_height
                    
                    # 计算相对坐标（0-1范围）
                    screen_detection["relative_x"] = logical_det_x / area_width
                    screen_detection["relative_y"] = logical_det_y / area_height
                    screen_detection["relative_width"] = logical_det_width / area_width
                    screen_detection["relative_height"] = logical_det_height / area_height
                    
                    # 添加动态颜色信息
                    class_id = detection.get("class_id", 0)
                    screen_detection["border_color"] = self._get_class_color(class_id)
                    
                    screen_detections.append(screen_detection)
                
                # 发送检测结果到前端（实时更新）
                detections_json = json.dumps(screen_detections)
                self.showMultipleDetections.emit(detections_json)
            else:
                # 没有检测到目标，清除显示
                self.clearAllDetections.emit()
                
        except Exception as e:
            logger.error(f"实时检测错误: {e}")
            # 发生错误时停止实时检测
            self.stopRealtimeDetection()

    @Slot(str, result=str)
    def executeTemplateMatching(self, template_path):
        """执行模板匹配"""
        try:
            if self._algorithm_mode != 0:
                self.logAdded.emit("当前算法不是模板匹配模式", "error")
                return json.dumps({"success": False, "error": "算法模式错误"})

            if not template_path or not os.path.exists(template_path):
                self.logAdded.emit("模板图片路径无效", "error")
                return json.dumps({"success": False, "error": "图片路径无效"})

            # 获取当前算法设置
            config = self.getCurrentAlgorithmSettings()
            self.logAdded.emit(f"开始模板匹配，配置: {config}", "info")

            # 执行匹配
            result = template_matcher.find_template_on_screen(template_path, config)

            if result:
                self.logAdded.emit(
                    f"匹配成功！位置: ({result['center_x']}, {result['center_y']}), "
                    f"置信度: {result['confidence']:.3f}",
                    "success",
                )
                return json.dumps({"success": True, "result": result})
            else:
                self.logAdded.emit("未找到匹配的模板", "warning")
                return json.dumps({"success": False, "error": "未找到匹配项"})

        except Exception as e:
            error_msg = f"模板匹配过程中发生错误: {str(e)}"
            self.logAdded.emit(error_msg, "error")
            return json.dumps({"success": False, "error": error_msg})

    @Slot(str, result=bool)
    def clickTemplate(self, template_path):
        """查找并点击模板"""
        try:
            if self._algorithm_mode != 0:
                self.logAdded.emit("当前算法不是模板匹配模式", "error")
                return False

            if not template_path or not os.path.exists(template_path):
                self.logAdded.emit("模板图片路径无效", "error")
                return False

            # 获取当前算法设置
            config = self.getCurrentAlgorithmSettings()
            self.logAdded.emit(f"开始查找并点击模板", "info")

            # 执行点击
            success = template_matcher.click_template(template_path, config)

            if success:
                self.logAdded.emit("成功点击模板位置", "success")
            else:
                self.logAdded.emit("点击失败", "error")

            return success

        except Exception as e:
            error_msg = f"点击模板过程中发生错误: {str(e)}"
            self.logAdded.emit(error_msg, "error")
            return False

    @Slot(result=str)
    def getAllWindows(self):
        """获取所有窗口列表"""
        try:
            from python.windows_select import get_all_windows_list

            windows_data = get_all_windows_list()
            return json.dumps(windows_data)

        except Exception as e:
            self.logAdded.emit(f"获取窗口列表失败: {str(e)}", "error")
            return json.dumps([])


class ImageMatcherApp:
    def __init__(self):
        # 启用高DPI支持

        self.app = QGuiApplication(sys.argv)
        self.controller = ImageMatcherController()

        # 设置QML样式为Material以支持自定义样式
        os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"

        # 创建QML引擎
        self.engine = QQmlApplicationEngine()

        # 注册控制器到QML上下文
        self.engine.rootContext().setContextProperty("controller", self.controller)

        # 设置QML文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_qml_path = os.path.join(current_dir, "main.qml")

        # 加载主QML文件
        self.engine.load(QUrl.fromLocalFile(main_qml_path))

        # 检查是否成功加载
        if not self.engine.rootObjects():
            sys.exit(-1)

    def run(self):
        """运行应用程序"""
        return self.app.exec()


if __name__ == "__main__":
    # 1. 首先设置环境变量（必须在任何Qt操作之前）
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # 2. 设置Windows DPI感知（在创建任何GUI之前）
    if os.name == "nt":
        try:
            # 设置进程DPI感知，防止pyautogui和PySide6冲突
            import ctypes
            from ctypes import wintypes

            # 尝试使用最新的DPI感知API
            try:
                # Windows 10 1703及以上版本
                ctypes.windll.user32.SetProcessDpiAwarenessContext(
                    -4
                )  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            except:
                try:
                    # Windows 8.1及以上版本
                    ctypes.windll.shcore.SetProcessDpiAwareness(
                        2
                    )  # PROCESS_PER_MONITOR_DPI_AWARE
                except:
                    try:
                        # Windows Vista及以上版本
                        ctypes.windll.user32.SetProcessDPIAware()
                    except:
                        pass
        except Exception as e:
            print(f"DPI设置警告（可忽略）: {e}")

    # 3. 设置Qt高DPI缩放策略
    # 使用PassThrough策略确保精确的DPI处理
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 4. 配置pyautogui以适应高DPI环境
    try:
        import pyautogui
        # 禁用pyautogui的fail-safe功能
        pyautogui.FAILSAFE = False
        # 设置pyautogui的图像搜索置信度
        pyautogui.MINIMUM_DURATION = 0.1
    except ImportError:
        pass

    app = ImageMatcherApp()
    sys.exit(app.run())
