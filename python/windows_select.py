"""
Windows窗口选择模块
使用真实的Windows API获取窗口信息
"""

import ctypes
from ctypes import wintypes, windll
import win32gui
import win32con
import win32api
import win32process
import psutil
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import platform

# 在导入pyautogui之前设置环境变量
os.environ.setdefault("PYAUTOGUI_NO_FAILSAFE", "1")
import pyautogui

# DPI感知由主程序设置，这里不重复设置以避免冲突
# try:
#     ctypes.windll.shcore.SetProcessDpiAwareness(1)
# except:
#     pass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WindowInfo:
    """窗口信息类"""

    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.title = self._get_window_title()
        self.class_name = self._get_class_name()
        self.rect = self._get_window_rect()
        self.process_name = self._get_process_name()
        self.is_visible = self._is_visible()
        self.is_minimized = self._is_minimized()

    def _get_window_title(self) -> str:
        """获取窗口标题"""
        try:
            length = win32gui.GetWindowTextLength(self.hwnd)
            if length == 0:
                return ""
            return win32gui.GetWindowText(self.hwnd)
        except Exception as e:
            logger.debug(f"获取窗口标题失败 (hwnd={self.hwnd}): {e}")
            return ""

    def _get_class_name(self) -> str:
        """获取窗口类名"""
        try:
            return win32gui.GetClassName(self.hwnd)
        except Exception as e:
            logger.debug(f"获取窗口类名失败 (hwnd={self.hwnd}): {e}")
            return ""

    def _get_window_rect(self) -> Dict[str, int]:
        """获取窗口矩形，考虑DPI缩放"""
        try:
            # 首先尝试使用DPI感知的API
            try:
                # 尝试使用DwmGetWindowAttribute获取扩展框架边界
                import ctypes
                from ctypes import wintypes
                
                dwmapi = ctypes.windll.dwmapi
                rect = wintypes.RECT()
                
                # DWMWA_EXTENDED_FRAME_BOUNDS = 9
                result = dwmapi.DwmGetWindowAttribute(
                    wintypes.HWND(self.hwnd),
                    wintypes.DWORD(9),
                    ctypes.byref(rect),
                    ctypes.sizeof(rect)
                )
                
                if result == 0:  # S_OK
                    # DWM API成功，使用更精确的边界
                    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
                    logger.debug(f"使用DWM API获取窗口坐标: ({left}, {top}, {right}, {bottom})")
                else:
                    raise Exception("DWM API失败")
                    
            except Exception:
                # 回退到标准API
                left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
                logger.debug(f"使用标准API获取窗口坐标: ({left}, {top}, {right}, {bottom})")
            
            return {
                "x": left,
                "y": top,
                "width": right - left,
                "height": bottom - top,
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
            }
        except Exception as e:
            logger.debug(f"获取窗口矩形失败 (hwnd={self.hwnd}): {e}")
            return {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0,
                "left": 0,
                "top": 0,
                "right": 0,
                "bottom": 0,
            }

    def _get_process_name(self) -> str:
        """获取进程名称"""
        try:
            _, pid = win32process.GetWindowThreadProcessId(self.hwnd)
            process = psutil.Process(pid)
            return process.name()
        except Exception as e:
            logger.debug(f"获取进程名称失败 (hwnd={self.hwnd}): {e}")
            return ""

    def _is_visible(self) -> bool:
        """检查窗口是否可见"""
        try:
            return win32gui.IsWindowVisible(self.hwnd)
        except Exception as e:
            logger.debug(f"检查窗口可见性失败 (hwnd={self.hwnd}): {e}")
            return False

    def _is_minimized(self) -> bool:
        """检查窗口是否最小化"""
        try:
            return win32gui.IsIconic(self.hwnd)
        except Exception as e:
            logger.debug(f"检查窗口最小化状态失败 (hwnd={self.hwnd}): {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "hwnd": self.hwnd,
            "title": self.title,
            "class_name": self.class_name,
            "rect": self.rect,
            "process_name": self.process_name,
            "is_visible": self.is_visible,
            "is_minimized": self.is_minimized,
        }


class WindowSelector:
    """Windows窗口选择器"""

    def __init__(self):
        self.windows_cache = []
        self.last_update = 0
        self.cache_duration = 1.0  # 缓存1秒
        logger.info("Windows窗口选择器初始化完成")

    def get_all_windows(self, include_invisible: bool = False) -> List[WindowInfo]:
        """
        获取所有窗口列表

        Args:
            include_invisible: 是否包含不可见窗口

        Returns:
            窗口信息列表
        """
        try:
            windows = []

            def enum_windows_proc(hwnd, lParam):
                try:
                    window = WindowInfo(hwnd)

                    # 过滤条件
                    if not include_invisible and not window.is_visible:
                        return True

                    # 过滤没有标题的窗口
                    if not window.title.strip():
                        return True

                    # 过滤尺寸太小的窗口
                    if window.rect["width"] < 50 or window.rect["height"] < 50:
                        return True

                    windows.append(window)
                    logger.debug(
                        f"找到窗口: {window.title} ({window.rect['width']}x{window.rect['height']})"
                    )

                except Exception as e:
                    logger.debug(f"处理窗口 {hwnd} 时出错: {e}")

                return True

            win32gui.EnumWindows(enum_windows_proc, 0)

            # 按Z顺序排序（最上层的窗口在前面）
            # 使用GetWindowLong来获取窗口的Z顺序信息
            def get_z_order(window):
                try:
                    # 使用GetNextWindow来确定Z顺序
                    # 较小的索引表示更靠前（更上层）的窗口
                    hwnd = window.hwnd
                    z_order = 0
                    current = win32gui.GetTopWindow(0)  # 获取最顶层窗口
                    while current:
                        if current == hwnd:
                            return z_order
                        current = win32gui.GetNextWindow(current, win32con.GW_HWNDNEXT)
                        z_order += 1
                    return 999999  # 如果没找到，放到最后
                except:
                    return 999999

            windows.sort(key=get_z_order)

            logger.info(f"找到 {len(windows)} 个有效窗口")
            return windows

        except Exception as e:
            logger.error(f"获取窗口列表失败: {e}")
            raise e

    def get_window_at_position(self, x: int, y: int) -> Optional[WindowInfo]:
        """
        获取指定位置的窗口

        Args:
            x: 屏幕X坐标
            y: 屏幕Y坐标

        Returns:
            窗口信息，未找到返回None
        """
        try:
            # 使用Windows API获取指定点的窗口句柄
            point = wintypes.POINT(x, y)
            hwnd = windll.user32.WindowFromPoint(point)

            if hwnd == 0:
                logger.debug(f"位置 ({x}, {y}) 没有找到窗口")
                return None

            # 获取顶级窗口
            original_hwnd = hwnd
            while True:
                parent = win32gui.GetParent(hwnd)
                if parent == 0:
                    break
                hwnd = parent

            window = WindowInfo(hwnd)

            # 检查窗口是否有效
            if not window.is_visible:
                logger.debug(f"位置 ({x}, {y}) 的窗口不可见: {window.title}")
                return None

            if not window.title.strip():
                logger.debug(f"位置 ({x}, {y}) 的窗口没有标题")
                return None

            # 排除当前应用程序的窗口
            if "图片匹配器" in window.title:
                logger.debug(
                    f"位置 ({x}, {y}) 的窗口是当前应用程序窗口，跳过: {window.title}"
                )
                # 尝试获取下层窗口
                try:
                    # 临时隐藏当前窗口，然后重新获取
                    next_hwnd = windll.user32.WindowFromPoint(point)
                    if next_hwnd != original_hwnd and next_hwnd != 0:
                        # 获取下层窗口的顶级窗口
                        while True:
                            parent = win32gui.GetParent(next_hwnd)
                            if parent == 0:
                                break
                            next_hwnd = parent

                        next_window = WindowInfo(next_hwnd)
                        if (
                            next_window.is_visible
                            and next_window.title.strip()
                            and "图片匹配器" not in next_window.title
                        ):
                            logger.debug(
                                f"位置 ({x}, {y}) 找到下层窗口: {next_window.title}"
                            )
                            return next_window
                except Exception as e:
                    logger.debug(f"获取下层窗口失败: {e}")

                return None

            logger.debug(f"位置 ({x}, {y}) 的窗口: {window.title}")
            return window

        except Exception as e:
            logger.error(f"获取位置窗口失败: {e}")
            return None

    def get_window_by_title(
        self, title: str, exact_match: bool = False
    ) -> Optional[WindowInfo]:
        """
        根据标题查找窗口

        Args:
            title: 窗口标题
            exact_match: 是否精确匹配

        Returns:
            窗口信息，未找到返回None
        """
        try:
            windows = self.get_all_windows()

            for window in windows:
                if exact_match:
                    if window.title == title:
                        return window
                else:
                    if title.lower() in window.title.lower():
                        return window

            return None

        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            return None

    def get_foreground_window(self) -> Optional[WindowInfo]:
        """
        获取前景窗口（当前活动窗口）

        Returns:
            前景窗口信息
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None

            return WindowInfo(hwnd)

        except Exception as e:
            logger.error(f"获取前景窗口失败: {e}")
            return None

    def bring_window_to_front(self, hwnd: int) -> bool:
        """
        将窗口置于前台

        Args:
            hwnd: 窗口句柄

        Returns:
            是否成功
        """
        try:
            # 如果窗口最小化，先恢复
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # 置于前台
            win32gui.SetForegroundWindow(hwnd)
            return True

        except Exception as e:
            logger.error(f"置于前台失败: {e}")
            return False

    def capture_window_image(self, hwnd: int) -> Optional[bytes]:
        """
        捕获窗口图像

        Args:
            hwnd: 窗口句柄

        Returns:
            图像数据，失败返回None
        """
        try:
            window = WindowInfo(hwnd)
            rect = window.rect

            # 尝试多种截图方法
            screenshot = None
            
            # 方法1：尝试使用PrintWindow API（最适合DPI环境）
            try:
                screenshot = self._capture_window_with_printwindow(hwnd, rect)
                if screenshot:
                    logger.debug(f"PrintWindow API截图成功: {screenshot.size}")
            except Exception as e:
                logger.debug(f"PrintWindow API失败: {e}")
            
            # 方法2：如果PrintWindow失败，使用PIL ImageGrab
            if screenshot is None:
                try:
                    from PIL import ImageGrab
                    x, y, width, height = rect["x"], rect["y"], rect["width"], rect["height"]
                    
                    # 直接使用逻辑坐标进行截图，让PIL自己处理DPI
                    screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
                    logger.debug(f"PIL截图: ({x}, {y}, {width}, {height}) -> {screenshot.size}")
                    
                except ImportError:
                    # 方法3：回退到pyautogui
                    screenshot = pyautogui.screenshot(
                        region=(rect["x"], rect["y"], rect["width"], rect["height"])
                    )
                    logger.debug(f"PyAutoGUI截图: {screenshot.size}")

            if screenshot is None:
                logger.error("所有截图方法都失败了")
                return None

            # 转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 编码为PNG
            success, encoded_img = cv2.imencode(".png", screenshot_cv)
            if success:
                return encoded_img.tobytes()
            else:
                return None

        except Exception as e:
            logger.error(f"捕获窗口图像失败: {e}")
            return None
    
    def _capture_window_with_printwindow(self, hwnd: int, rect: Dict[str, int]) -> Optional:
        """
        使用PrintWindow API捕获窗口
        这个方法不受DPI缩放影响，能准确捕获窗口内容
        """
        try:
            import ctypes
            from ctypes import wintypes
            from PIL import Image
            
            # 获取窗口尺寸
            width = rect["width"]
            height = rect["height"]
            
            if width <= 0 or height <= 0:
                return None
            
            # 创建设备上下文
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            
            # 获取窗口DC
            window_dc = user32.GetWindowDC(hwnd)
            if not window_dc:
                return None
            
            # 创建内存DC
            mem_dc = gdi32.CreateCompatibleDC(window_dc)
            if not mem_dc:
                user32.ReleaseDC(hwnd, window_dc)
                return None
            
            # 创建位图
            bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
            if not bitmap:
                gdi32.DeleteDC(mem_dc)
                user32.ReleaseDC(hwnd, window_dc)
                return None
            
            # 选择位图到内存DC
            old_bitmap = gdi32.SelectObject(mem_dc, bitmap)
            
            # 使用PrintWindow捕获窗口内容
            # PW_CLIENTONLY = 0x1, PW_RENDERFULLCONTENT = 0x2
            result = user32.PrintWindow(hwnd, mem_dc, 0x2)
            
            if result:
                # 获取位图数据
                bmp_info = wintypes.BITMAPINFO()
                bmp_info.bmiHeader.biSize = ctypes.sizeof(bmp_info.bmiHeader)
                bmp_info.bmiHeader.biWidth = width
                bmp_info.bmiHeader.biHeight = -height  # 负值表示从上到下
                bmp_info.bmiHeader.biPlanes = 1
                bmp_info.bmiHeader.biBitCount = 32
                bmp_info.bmiHeader.biCompression = 0  # BI_RGB
                
                # 创建缓冲区
                buffer_size = width * height * 4
                buffer = (ctypes.c_char * buffer_size)()
                
                # 获取位图数据
                lines = gdi32.GetDIBits(
                    mem_dc, bitmap, 0, height, buffer, 
                    ctypes.byref(bmp_info), 0  # DIB_RGB_COLORS
                )
                
                if lines == height:
                    # 转换为PIL图像
                    img_data = bytes(buffer)
                    # Windows bitmap是BGRA格式，转换为RGBA
                    import struct
                    rgba_data = bytearray()
                    for i in range(0, len(img_data), 4):
                        b, g, r, a = struct.unpack_from('BBBB', img_data, i)
                        rgba_data.extend([r, g, b, a])
                    
                    screenshot = Image.frombytes('RGBA', (width, height), bytes(rgba_data))
                    # 转换为RGB
                    screenshot = screenshot.convert('RGB')
                    
                    # 清理资源
                    gdi32.SelectObject(mem_dc, old_bitmap)
                    gdi32.DeleteObject(bitmap)
                    gdi32.DeleteDC(mem_dc)
                    user32.ReleaseDC(hwnd, window_dc)
                    
                    return screenshot
            
            # 清理资源
            gdi32.SelectObject(mem_dc, old_bitmap)
            gdi32.DeleteObject(bitmap)
            gdi32.DeleteDC(mem_dc)
            user32.ReleaseDC(hwnd, window_dc)
            
            return None
            
        except Exception as e:
            logger.debug(f"PrintWindow API执行失败: {e}")
            return None


# 创建全局实例
window_selector = WindowSelector()


def get_all_windows_list(include_invisible: bool = False) -> List[Dict[str, Any]]:
    """便捷函数：获取所有窗口列表"""
    windows = window_selector.get_all_windows(include_invisible)
    return [w.to_dict() for w in windows]


def get_window_at_pos(x: int, y: int) -> Optional[Dict[str, Any]]:
    """便捷函数：获取指定位置的窗口"""
    window = window_selector.get_window_at_position(x, y)
    return window.to_dict() if window else None


def find_window_by_title(
    title: str, exact_match: bool = False
) -> Optional[Dict[str, Any]]:
    """便捷函数：根据标题查找窗口"""
    window = window_selector.get_window_by_title(title, exact_match)
    return window.to_dict() if window else None


def get_active_window() -> Optional[Dict[str, Any]]:
    """便捷函数：获取当前活动窗口"""
    window = window_selector.get_foreground_window()
    return window.to_dict() if window else None


def bring_window_front(hwnd: int) -> bool:
    """便捷函数：将窗口置于前台"""
    return window_selector.bring_window_to_front(hwnd)
