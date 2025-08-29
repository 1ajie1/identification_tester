#!/usr/bin/env python3
"""
测试pyautogui和PySide6 DPI兼容性
"""

import os
import sys
import ctypes

# 设置环境变量
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ.setdefault('PYAUTOGUI_NO_FAILSAFE', '1')

# 设置DPI感知
if os.name == "nt":
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
        print("✅ DPI感知设置成功 (SetProcessDpiAwarenessContext)")
    except:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            print("✅ DPI感知设置成功 (SetProcessDpiAwareness)")
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
                print("✅ DPI感知设置成功 (SetProcessDPIAware)")
            except:
                print("❌ DPI感知设置失败")

# 导入PySide6
try:
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtCore import Qt
    print("✅ PySide6导入成功")
    
    # 设置高DPI缩放策略
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    print("✅ Qt高DPI策略设置成功")
except Exception as e:
    print(f"❌ PySide6设置失败: {e}")

# 导入pyautogui
try:
    import pyautogui
    print(f"✅ pyautogui导入成功 (版本: {pyautogui.__version__})")
    
    # 测试截图功能
    screen_size = pyautogui.size()
    print(f"✅ 屏幕尺寸: {screen_size}")
except Exception as e:
    print(f"❌ pyautogui导入失败: {e}")

print("🎉 测试完成！")