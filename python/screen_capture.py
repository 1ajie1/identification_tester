#!/usr/bin/env python3
"""
屏幕窗口捕获模块
使用mss + ctypes实现高效的屏幕截图，正确处理DPI缩放
"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple, List, Dict, Any
import logging
import tempfile
import os
import platform
import ctypes
from ctypes import wintypes

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreenCaptureEngine:
    """
    屏幕捕获引擎
    使用mss + ctypes实现高效截图，正确处理DPI缩放
    """

    def __init__(self):
        # 初始化mss
        try:
            import mss
            self.mss = mss.mss()
            logger.info("MSS截图引擎初始化成功")
        except ImportError:
            logger.error("MSS库未安装，请运行: pip install mss")
            self.mss = None
        
        # 获取DPI缩放信息
        self.dpi_scale = self._get_dpi_scale()
        self.screen_info = self._get_screen_info()
        
        logger.info(f"DPI缩放因子: {self.dpi_scale}")
        logger.info(f"屏幕信息: {self.screen_info}")
        
        # Windows API函数
        if platform.system() == "Windows":
            self.user32 = ctypes.windll.user32
            self.gdi32 = ctypes.windll.gdi32

    def _get_dpi_scale(self) -> float:
        """获取当前系统的DPI缩放因子"""
        try:
            if platform.system() == "Windows":
                import ctypes
                from ctypes import wintypes
                
                # 方法1: 使用GetDpiForSystem (Windows 10 1607+)
                try:
                    dpi = ctypes.windll.user32.GetDpiForSystem()
                    if dpi > 0:
                        scale = dpi / 96.0
                        logger.info(f"使用GetDpiForSystem获取DPI: {dpi}, 缩放: {scale}")
                        return scale
                except:
                    pass
                
                # 方法2: 使用GetDeviceCaps
                try:
                    dc = self.user32.GetDC(0)
                    dpi_x = self.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                    dpi_y = self.gdi32.GetDeviceCaps(dc, 90)  # LOGPIXELSY
                    self.user32.ReleaseDC(0, dc)
                    scale = dpi_x / 96.0
                    logger.info(f"使用GetDeviceCaps获取DPI: X={dpi_x}, Y={dpi_y}, 缩放: {scale}")
                    return scale
                except Exception as e:
                    logger.warning(f"GetDeviceCaps方法失败: {e}")
                
                # 方法3: 使用GetDpiForMonitor (Windows 8.1+)
                try:
                    # 获取主显示器句柄
                    monitor = self.user32.MonitorFromPoint(ctypes.wintypes.POINT(0, 0), 1)  # MONITOR_DEFAULTTOPRIMARY
                    if monitor:
                        # 定义MONITOR_DPI_TYPE枚举
                        MDT_EFFECTIVE_DPI = 0
                        dpi_x = ctypes.c_uint()
                        dpi_y = ctypes.c_uint()
                        
                        # 调用GetDpiForMonitor
                        shcore = ctypes.windll.shcore
                        result = shcore.GetDpiForMonitor(monitor, MDT_EFFECTIVE_DPI, 
                                                       ctypes.byref(dpi_x), ctypes.byref(dpi_y))
                        if result == 0:  # S_OK
                            scale = dpi_x.value / 96.0
                            logger.info(f"使用GetDpiForMonitor获取DPI: X={dpi_x.value}, Y={dpi_y.value}, 缩放: {scale}")
                            return scale
                except Exception as e:
                    logger.warning(f"GetDpiForMonitor方法失败: {e}")
                
                # 方法4: 使用tkinter获取DPI (通常很可靠)
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()  # 隐藏窗口
                    dpi = root.winfo_fpixels('1i')  # 获取每英寸的像素数
                    root.destroy()
                    scale = dpi / 96.0
                    logger.info(f"使用tkinter获取DPI: {dpi}, 缩放: {scale}")
                    return scale
                except Exception as e:
                    logger.warning(f"tkinter方法失败: {e}")
                
                # 方法5: 使用注册表方法
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                       r"Control Panel\Desktop\WindowMetrics")
                    value, _ = winreg.QueryValueEx(key, "AppliedDPI")
                    winreg.CloseKey(key)
                    scale = value / 96.0
                    logger.info(f"使用注册表获取DPI: {value}, 缩放: {scale}")
                    return scale
                except Exception as e:
                    logger.warning(f"注册表方法失败: {e}")
                
                logger.warning("所有DPI获取方法都失败，使用默认值1.0")
                return 1.0
            else:
                return 1.0
        except Exception as e:
            logger.error(f"获取DPI缩放因子时发生错误: {e}")
            return 1.0
    
    def _get_screen_info(self) -> Dict[str, Any]:
        """获取屏幕信息"""
        try:
            if platform.system() == "Windows":
                # 获取虚拟屏幕尺寸（包括所有显示器）
                virtual_width = self.user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
                virtual_height = self.user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
                virtual_left = self.user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
                virtual_top = self.user32.GetSystemMetrics(77)    # SM_YVIRTUALSCREEN
                
                # 获取主显示器尺寸
                primary_width = self.user32.GetSystemMetrics(0)   # SM_CXSCREEN
                primary_height = self.user32.GetSystemMetrics(1)  # SM_CYSCREEN
                
                return {
                    "virtual": {
                        "left": virtual_left,
                        "top": virtual_top,
                        "width": virtual_width,
                        "height": virtual_height
                    },
                    "primary": {
                        "width": primary_width,
                        "height": primary_height
                    }
                }
            else:
                return {"primary": {"width": 1920, "height": 1080}}
        except Exception as e:
            logger.warning(f"无法获取屏幕信息: {e}")
            return {"primary": {"width": 1920, "height": 1080}}

    def capture_screen(
        self, region: Tuple[int, int, int, int] = None
    ) -> Optional[np.ndarray]:
        """
        捕获屏幕截图，使用多种方法确保成功

        Args:
            region: 截图区域 (x, y, width, height)，None表示全屏

        Returns:
            截图的numpy数组，失败返回None
        """
        try:
            # 方法1：尝试使用MSS
            if self.mss:
                try:
                    result = self._capture_with_mss(region)
                    if result is not None:
                        return result
                except Exception as e:
                    logger.warning(f"MSS截图失败: {e}")
            
            # 方法2：回退到Windows GDI API
            try:
                result = self._capture_with_gdi(region)
                if result is not None:
                    logger.info("GDI截图成功")
                    return result
            except Exception as e:
                logger.warning(f"GDI截图失败: {e}")
            
            # 方法3：最后回退到PIL
            try:
                result = self._capture_with_pil(region)
                if result is not None:
                    logger.info("PIL截图成功")
                    return result
            except Exception as e:
                logger.warning(f"PIL截图失败: {e}")
            
            logger.error("所有截图方法都失败了")
            return None
            
        except Exception as e:
            logger.error(f"截图异常: {e}")
            return None

    def _capture_with_mss(self, region: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """使用MSS截图"""
        if region:
            x, y, width, height = region
            monitor = {
                "left": int(x),
                "top": int(y),
                "width": int(width),
                "height": int(height)
            }
            screenshot_mss = self.mss.grab(monitor)
        else:
            screenshot_mss = self.mss.grab(self.mss.monitors[1])
        
        # 转换为OpenCV格式
        screenshot_np = np.array(screenshot_mss)
        if screenshot_np.shape[2] == 4:  # BGRA
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_BGRA2BGR)
        else:
            screenshot_cv = screenshot_np
        
        return screenshot_cv

    def _capture_with_gdi(self, region: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """使用Windows GDI API截图"""
        if platform.system() != "Windows":
            return None
            
        try:
            if region:
                x, y, width, height = region
            else:
                # 全屏
                x, y = 0, 0
                width = self.screen_info["primary"]["width"]
                height = self.screen_info["primary"]["height"]
            
            # 获取屏幕DC
            screen_dc = self.user32.GetDC(0)
            mem_dc = self.gdi32.CreateCompatibleDC(screen_dc)
            
            # 创建位图
            bitmap = self.gdi32.CreateCompatibleBitmap(screen_dc, width, height)
            old_bitmap = self.gdi32.SelectObject(mem_dc, bitmap)
            
            # 复制屏幕内容
            self.gdi32.BitBlt(mem_dc, 0, 0, width, height, screen_dc, x, y, 0x00CC0020)  # SRCCOPY
            
            # 获取位图数据
            bmp_info = wintypes.BITMAPINFO()
            bmp_info.bmiHeader.biSize = ctypes.sizeof(bmp_info.bmiHeader)
            bmp_info.bmiHeader.biWidth = width
            bmp_info.bmiHeader.biHeight = -height  # 负值表示从上到下
            bmp_info.bmiHeader.biPlanes = 1
            bmp_info.bmiHeader.biBitCount = 32
            bmp_info.bmiHeader.biCompression = 0  # BI_RGB
            
            buffer_size = width * height * 4
            buffer = (ctypes.c_char * buffer_size)()
            
            lines = self.gdi32.GetDIBits(
                mem_dc, bitmap, 0, height, buffer,
                ctypes.byref(bmp_info), 0
            )
            
            # 清理资源
            self.gdi32.SelectObject(mem_dc, old_bitmap)
            self.gdi32.DeleteObject(bitmap)
            self.gdi32.DeleteDC(mem_dc)
            self.user32.ReleaseDC(0, screen_dc)
            
            if lines == height:
                # 转换为numpy数组
                img_data = np.frombuffer(buffer, dtype=np.uint8)
                img_data = img_data.reshape((height, width, 4))
                # BGRA -> BGR
                screenshot_cv = cv2.cvtColor(img_data, cv2.COLOR_BGRA2BGR)
                return screenshot_cv
            
            return None
            
        except Exception as e:
            logger.error(f"GDI截图失败: {e}")
            return None

    def _capture_with_pil(self, region: Tuple[int, int, int, int] = None) -> Optional[np.ndarray]:
        """使用PIL截图"""
        try:
            from PIL import ImageGrab
            
            if region:
                x, y, width, height = region
                screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            else:
                screenshot = ImageGrab.grab()
            
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot_cv
            
        except ImportError:
            logger.error("PIL未安装")
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
                # 使用提供的窗口矩形进行截图
                region = (
                    window_rect["x"],
                    window_rect["y"],
                    window_rect["width"],
                    window_rect["height"],
                )
                return self.capture_screen(region)
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
                    return self.capture_screen(region)
                else:
                    logger.warning(f"未找到窗口: {window_title}")
                    return None

        except Exception as e:
            logger.error(f"捕获窗口失败: {e}")
            return None

    def find_window_by_title(self, window_title: str) -> Optional[Dict[str, Any]]:
        """根据标题查找窗口"""
        try:
            from .windows_select import window_selector
            window = window_selector.get_window_by_title(window_title)
            if window:
                return {
                    "title": window.title,
                    "x": window.rect["x"],
                    "y": window.rect["y"],
                    "width": window.rect["width"],
                    "height": window.rect["height"],
                    "hwnd": window.hwnd,
                    "process_name": window.process_name,
                }
            return None
        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            return None

    def get_window_list(self) -> List[Dict[str, Any]]:
        """获取窗口列表"""
        try:
            from .windows_select import window_selector
            windows = window_selector.get_all_windows()
            return [
                {
                    "title": w.title,
                    "x": w.rect["x"],
                    "y": w.rect["y"],
                    "width": w.rect["width"],
                    "height": w.rect["height"],
                    "hwnd": w.hwnd,
                    "process_name": w.process_name,
                }
                for w in windows
            ]
        except Exception as e:
            logger.error(f"获取窗口列表失败: {e}")
            return []

    def save_screenshot(self, image: np.ndarray, filename: str = None) -> str:
        """保存截图"""
        try:
            if filename is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                filename = temp_file.name
                temp_file.close()

            success = cv2.imwrite(filename, image)
            return filename if success else ""
        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            return ""


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
