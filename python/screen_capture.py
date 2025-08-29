#!/usr/bin/env python3
"""
屏幕窗口捕获模块
提供屏幕截图、窗口捕获和窗口检测功能
"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple, List, Dict, Any
import logging
import tempfile
import os
import platform

# 在导入pyautogui之前设置环境变量，防止它自动设置DPI感知
os.environ.setdefault("PYAUTOGUI_NO_FAILSAFE", "1")

# 延迟导入pyautogui，并在导入时禁用DPI设置
import pyautogui


# 禁用pyautogui的fail-safe功能
pyautogui.FAILSAFE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreenCaptureEngine:
    """
    屏幕捕获引擎
    支持全屏截图、窗口截图和窗口检测
    """

    def __init__(self):
        # 默认配置
        self.default_config = {
            "screenshot_delay": 0.1,  # 截图延迟
            "window_detection_method": "pyautogui",  # 窗口检测方法
            "save_screenshots": True,  # 是否保存截图
            "screenshot_format": "png",  # 截图格式
        }

        # 获取DPI缩放因子
        self.dpi_scale = self._get_dpi_scale()
        logger.info(f"检测到DPI缩放因子: {self.dpi_scale}")

    def _get_dpi_scale(self) -> float:
        """获取当前系统的DPI缩放因子"""
        try:
            if platform.system() == "Windows":
                import ctypes

                # 获取DPI
                user32 = ctypes.windll.user32
                user32.SetProcessDPIAware()
                dc = user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                user32.ReleaseDC(0, dc)
                scale = dpi / 96.0  # 96 DPI是标准DPI
                return scale
            else:
                # Linux/Mac系统的处理
                return 1.0
        except Exception as e:
            logger.warning(f"无法获取DPI缩放因子: {e}")
            return 1.0

    def capture_screen(
        self, region: Tuple[int, int, int, int] = None
    ) -> Optional[np.ndarray]:
        """
        捕获屏幕截图

        Args:
            region: 截图区域 (x, y, width, height)，None表示全屏

        Returns:
            截图的numpy数组，失败返回None
        """
        try:
            logger.info(f"开始截图，区域: {region}，DPI缩放: {self.dpi_scale}")

            # 添加延迟确保界面稳定
            time.sleep(self.default_config["screenshot_delay"])

            if region:
                # 指定区域截图，应用DPI缩放
                x, y, width, height = region

                # 对于高DPI显示器，需要调整坐标和尺寸
                if self.dpi_scale != 1.0:
                    # 方法1：尝试使用PIL直接截图（更准确的DPI处理）
                    try:
                        from PIL import ImageGrab

                        # PIL的ImageGrab能更好地处理高DPI
                        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
                        logger.info(f"使用PIL截图，尺寸: {screenshot.size}")
                    except ImportError:
                        # 回退到pyautogui，但调整坐标
                        logger.info("PIL不可用，使用pyautogui截图")
                        screenshot = pyautogui.screenshot(region=(x, y, width, height))
                else:
                    screenshot = pyautogui.screenshot(region=(x, y, width, height))
            else:
                # 全屏截图
                try:
                    from PIL import ImageGrab

                    screenshot = ImageGrab.grab()
                    logger.info(f"使用PIL全屏截图，尺寸: {screenshot.size}")
                except ImportError:
                    screenshot = pyautogui.screenshot()

            # 转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            logger.info(f"截图成功，最终尺寸: {screenshot_cv.shape}")
            return screenshot_cv

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    def capture_window(
        self, window_title: str, window_rect: Dict[str, int] = None
    ) -> Optional[np.ndarray]:
        """
        捕获指定窗口的截图

        Args:
            window_title: 窗口标题
            window_rect: 窗口矩形区域 {"x": x, "y": y, "width": width, "height": height}

        Returns:
            窗口截图的numpy数组，失败返回None
        """
        try:
            logger.info(f"开始捕获窗口: {window_title}")

            if window_rect:
                # 使用提供的窗口矩形
                region = (
                    window_rect["x"],
                    window_rect["y"],
                    window_rect["width"],
                    window_rect["height"],
                )
                screenshot = self.capture_screen(region)
            else:
                # 尝试查找窗口
                window_info = self.find_window_by_title(window_title)
                if window_info:
                    region = (
                        window_info["x"],
                        window_info["y"],
                        window_info["width"],
                        window_info["height"],
                    )
                    screenshot = self.capture_screen(region)
                else:
                    logger.warning(f"未找到窗口: {window_title}")
                    # 使用全屏截图作为备选
                    screenshot = self.capture_screen()

            if screenshot is not None:
                logger.info(f"窗口截图成功: {window_title}")
                return screenshot
            else:
                logger.error(f"窗口截图失败: {window_title}")
                return None

        except Exception as e:
            logger.error(f"捕获窗口失败: {e}")
            return None

    def find_window_by_title(self, window_title: str) -> Optional[Dict[str, Any]]:
        """
        根据标题查找窗口

        Args:
            window_title: 窗口标题

        Returns:
            窗口信息字典，未找到返回None
        """
        try:
            from .windows_select import window_selector

            logger.info(f"查找窗口: {window_title}")

            # 使用真实的Windows API查找窗口
            window = window_selector.get_window_by_title(window_title)

            if window:
                window_info = {
                    "title": window.title,
                    "x": window.rect["x"],
                    "y": window.rect["y"],
                    "width": window.rect["width"],
                    "height": window.rect["height"],
                    "hwnd": window.hwnd,
                    "process_name": window.process_name,
                }
                logger.info(f"找到窗口: {window_info}")
                return window_info
            else:
                logger.warning(f"未找到窗口: {window_title}")
                return None

        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            # 如果Windows API失败，使用备用方案
            return self._fallback_find_window(window_title)

    def _fallback_find_window(self, window_title: str) -> Optional[Dict[str, Any]]:
        """
        备用窗口查找方案

        Args:
            window_title: 窗口标题

        Returns:
            窗口信息字典，未找到返回None
        """
        try:
            logger.warning(f"窗口查找功能开发中: {window_title}")
            return None

        except Exception as e:
            logger.error(f"备用方案查找窗口失败: {e}")
            return None

    def get_window_list(self) -> List[Dict[str, Any]]:
        """
        获取当前所有窗口的列表

        Returns:
            窗口信息列表
        """
        try:
            from .windows_select import window_selector

            logger.info("获取窗口列表")

            # 使用真实的Windows API获取窗口列表
            windows = window_selector.get_all_windows()
            windows_data = []

            for window in windows:
                windows_data.append(
                    {
                        "title": window.title,
                        "x": window.rect["x"],
                        "y": window.rect["y"],
                        "width": window.rect["width"],
                        "height": window.rect["height"],
                        "hwnd": window.hwnd,
                        "process_name": window.process_name,
                    }
                )

            logger.info(f"找到 {len(windows_data)} 个窗口")
            return windows_data

        except Exception as e:
            logger.error(f"获取窗口列表失败: {e}")
            # 如果Windows API失败，返回空列表
            return []

    def save_screenshot(self, image: np.ndarray, filename: str = None) -> str:
        """
        保存截图到临时文件

        Args:
            image: 图像数组
            filename: 文件名，None则自动生成

        Returns:
            保存的文件路径
        """
        try:
            if filename is None:
                # 生成临时文件名
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{self.default_config['screenshot_format']}"
                )
                filename = temp_file.name
                temp_file.close()

            # 保存图像
            success = cv2.imwrite(filename, image)

            if success:
                logger.info(f"截图已保存: {filename}")
                return filename
            else:
                logger.error(f"保存截图失败: {filename}")
                return ""

        except Exception as e:
            logger.error(f"保存截图异常: {e}")
            return ""

    def get_screen_size(self) -> Tuple[int, int]:
        """
        获取屏幕尺寸

        Returns:
            屏幕宽度和高度
        """
        try:
            size = pyautogui.size()
            logger.info(f"屏幕尺寸: {size}")
            return size
        except Exception as e:
            logger.error(f"获取屏幕尺寸失败: {e}")
            return (1920, 1080)  # 默认尺寸

    def capture_window_with_matching(
        self,
        window_title: str,
        template_image: np.ndarray,
        matcher_engine,
        config: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        捕获窗口并执行模板匹配

        Args:
            window_title: 窗口标题
            template_image: 模板图像
            matcher_engine: 匹配引擎（template_matcher 或 orb_matcher）
            config: 匹配配置

        Returns:
            匹配结果字典
        """
        try:
            logger.info(f"开始窗口匹配: {window_title}")

            # 捕获窗口
            window_screenshot = self.capture_window(window_title)
            if window_screenshot is None:
                logger.error("窗口截图失败")
                return None

            # 执行匹配
            if hasattr(matcher_engine, "match_features"):
                # ORB匹配
                result = matcher_engine.match_features(
                    template_image, window_screenshot, config
                )
            elif hasattr(matcher_engine, "find_template_in_image"):
                # 模板匹配 - 需要先保存图像
                template_path = self.save_screenshot(
                    template_image, "temp_template.png"
                )
                target_path = self.save_screenshot(window_screenshot, "temp_target.png")

                if template_path and target_path:
                    # 使用OpenCV模板匹配
                    result = self._opencv_template_match(
                        template_image, window_screenshot, config
                    )

                    # 清理临时文件
                    try:
                        os.remove(template_path)
                        os.remove(target_path)
                    except:
                        pass
                else:
                    logger.error("保存临时文件失败")
                    return None
            else:
                logger.error("不支持的匹配引擎")
                return None

            if result:
                # 添加窗口信息到结果中
                result["window_title"] = window_title
                result["window_screenshot_path"] = self.save_screenshot(
                    window_screenshot
                )
                logger.info(f"窗口匹配成功: {window_title}")
            else:
                logger.warning(f"窗口匹配失败: {window_title}")

            return result

        except Exception as e:
            logger.error(f"窗口匹配异常: {e}")
            return None

    def _opencv_template_match(
        self, template: np.ndarray, target: np.ndarray, config: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用OpenCV进行模板匹配

        Args:
            template: 模板图像
            target: 目标图像
            config: 匹配配置

        Returns:
            匹配结果字典
        """
        try:
            if config is None:
                config = {"method": "TM_CCOEFF_NORMED", "threshold": 0.8}

            # 方法映射
            methods = {
                "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
                "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
                "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
            }

            method = methods.get(
                config.get("method", "TM_CCOEFF_NORMED"), cv2.TM_CCOEFF_NORMED
            )
            threshold = config.get("threshold", 0.8)

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

            if confidence >= threshold:
                template_h, template_w = template.shape[:2]
                center_x = match_loc[0] + template_w // 2
                center_y = match_loc[1] + template_h // 2

                return {
                    "method": "template_matching",
                    "confidence": float(confidence),
                    "left": int(match_loc[0]),
                    "top": int(match_loc[1]),
                    "width": int(template_w),
                    "height": int(template_h),
                    "center_x": int(center_x),
                    "center_y": int(center_y),
                }
            else:
                return None

        except Exception as e:
            logger.error(f"OpenCV模板匹配失败: {e}")
            return None


# 创建全局实例
screen_capture = ScreenCaptureEngine()


def capture_screen_region(
    region: Tuple[int, int, int, int] = None
) -> Optional[np.ndarray]:
    """便捷函数：截图"""
    return screen_capture.capture_screen(region)


def capture_window_by_title(
    window_title: str, window_rect: Dict[str, int] = None
) -> Optional[np.ndarray]:
    """便捷函数：窗口截图"""
    return screen_capture.capture_window(window_title, window_rect)


def find_window(window_title: str) -> Optional[Dict[str, Any]]:
    """便捷函数：查找窗口"""
    return screen_capture.find_window_by_title(window_title)


def get_all_windows() -> List[Dict[str, Any]]:
    """便捷函数：获取所有窗口"""
    return screen_capture.get_window_list()
