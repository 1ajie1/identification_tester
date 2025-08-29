import pyautogui
import cv2
import numpy as np
import time
from typing import Optional, Tuple, List, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateMatchingEngine:
    """
    基于pyautogui和OpenCV的模板匹配引擎
    支持多种匹配方法和重试机制
    """

    def __init__(self):
        # 设置pyautogui的基本配置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        # OpenCV模板匹配方法映射
        self.matching_methods = {
            "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
            "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
            "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
        }

        # 默认配置
        self.default_config = {
            "method": "TM_CCOEFF_NORMED",
            "threshold": 0.8,
            "max_retries": 3,
            "retry_delay": 1.0,  # 重试间隔（秒）
            "confidence_threshold": 0.9,  # 高置信度阈值
        }

    def find_template_on_screen(
        self,
        template_path: str,
        config: Dict[str, Any] = None,
        region: Tuple[int, int, int, int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        在屏幕上查找模板图片

        Args:
            template_path: 模板图片路径
            config: 匹配配置参数
            region: 搜索区域 (left, top, width, height)

        Returns:
            匹配结果字典，包含位置、置信度等信息，未找到则返回None
        """
        if config is None:
            config = self.default_config.copy()

        max_retries = config.get("max_retries", 3)
        retry_delay = config.get("retry_delay", 1.0)

        for attempt in range(max_retries):
            try:
                logger.info(f"模板匹配尝试 {attempt + 1}/{max_retries}")

                # 使用pyautogui进行基础匹配
                result = self._attempt_pyautogui_match(template_path, config, region)

                if result:
                    logger.info(
                        f"匹配成功！位置: ({result['center_x']}, {result['center_y']}), "
                        f"置信度: {result['confidence']:.3f}"
                    )
                    return result

                # 如果pyautogui失败，尝试使用OpenCV进行更精确的匹配
                result = self._attempt_opencv_match(template_path, config, region)

                if result:
                    logger.info(
                        f"OpenCV匹配成功！位置: ({result['center_x']}, {result['center_y']}), "
                        f"置信度: {result['confidence']:.3f}"
                    )
                    return result

                if attempt < max_retries - 1:
                    logger.info(
                        f"第 {attempt + 1} 次尝试失败，{retry_delay}秒后重试..."
                    )
                    time.sleep(retry_delay)

            except Exception as e:
                logger.error(f"匹配过程中发生错误: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue

        logger.warning("所有重试都失败，未找到匹配的模板")
        return None

    def _attempt_pyautogui_match(
        self,
        template_path: str,
        config: Dict[str, Any],
        region: Tuple[int, int, int, int] = None,
    ) -> Optional[Dict[str, Any]]:
        """使用pyautogui进行模板匹配"""
        try:
            confidence = config.get("threshold", 0.8)

            # 使用pyautogui的locateOnScreen功能
            if region:
                location = pyautogui.locateOnScreen(
                    template_path, confidence=confidence, region=region
                )
            else:
                location = pyautogui.locateOnScreen(
                    template_path, confidence=confidence
                )

            if location:
                center = pyautogui.center(location)
                return {
                    "method": "pyautogui",
                    "left": location.left,
                    "top": location.top,
                    "width": location.width,
                    "height": location.height,
                    "center_x": center.x,
                    "center_y": center.y,
                    "confidence": confidence,  # pyautogui不返回实际置信度
                    "region": region,
                }

        except pyautogui.ImageNotFoundException:
            logger.debug("pyautogui未找到匹配项")
        except Exception as e:
            logger.debug(f"pyautogui匹配出错: {e}")

        return None

    def _attempt_opencv_match(
        self,
        template_path: str,
        config: Dict[str, Any],
        region: Tuple[int, int, int, int] = None,
    ) -> Optional[Dict[str, Any]]:
        """使用OpenCV进行更精确的模板匹配"""
        try:
            # 读取模板图片
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                logger.error(f"无法读取模板图片: {template_path}")
                return None

            # 截取屏幕
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            # 转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 获取匹配方法和阈值
            method_name = config.get("method", "TM_CCOEFF_NORMED")
            method = self.matching_methods.get(method_name, cv2.TM_CCOEFF_NORMED)
            threshold = config.get("threshold", 0.8)

            # 执行模板匹配
            result = cv2.matchTemplate(screenshot_cv, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 根据方法选择合适的值和位置
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                match_val = min_val
                match_loc = min_loc
                confidence = 1 - match_val  # 对于SQDIFF，值越小越好
            else:
                match_val = max_val
                match_loc = max_loc
                confidence = match_val

            # 检查是否超过阈值
            if confidence >= threshold:
                template_h, template_w = template.shape[:2]

                # 计算中心点
                center_x = match_loc[0] + template_w // 2
                center_y = match_loc[1] + template_h // 2

                # 如果指定了区域，需要调整坐标
                if region:
                    center_x += region[0]
                    center_y += region[1]
                    match_loc = (match_loc[0] + region[0], match_loc[1] + region[1])

                return {
                    "method": f"opencv_{method_name}",
                    "left": match_loc[0],
                    "top": match_loc[1],
                    "width": template_w,
                    "height": template_h,
                    "center_x": center_x,
                    "center_y": center_y,
                    "confidence": float(confidence),
                    "region": region,
                }

        except Exception as e:
            logger.debug(f"OpenCV匹配出错: {e}")

        return None

    def find_multiple_templates(
        self,
        template_path: str,
        config: Dict[str, Any] = None,
        region: Tuple[int, int, int, int] = None,
        max_matches: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        查找屏幕上的多个模板匹配

        Args:
            template_path: 模板图片路径
            config: 匹配配置参数
            region: 搜索区域
            max_matches: 最大匹配数量

        Returns:
            匹配结果列表
        """
        if config is None:
            config = self.default_config.copy()

        try:
            # 读取模板图片
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                logger.error(f"无法读取模板图片: {template_path}")
                return []

            # 截取屏幕
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            # 转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 获取匹配方法和阈值
            method_name = config.get("method", "TM_CCOEFF_NORMED")
            method = self.matching_methods.get(method_name, cv2.TM_CCOEFF_NORMED)
            threshold = config.get("threshold", 0.8)

            # 执行模板匹配
            result = cv2.matchTemplate(screenshot_cv, template, method)

            # 找到所有匹配位置
            locations = np.where(result >= threshold)
            matches = []

            template_h, template_w = template.shape[:2]

            for pt in zip(*locations[::-1]):  # 切换x,y坐标
                confidence = result[pt[1], pt[0]]

                # 计算中心点
                center_x = pt[0] + template_w // 2
                center_y = pt[1] + template_h // 2

                # 如果指定了区域，需要调整坐标
                if region:
                    center_x += region[0]
                    center_y += region[1]
                    pt = (pt[0] + region[0], pt[1] + region[1])

                matches.append(
                    {
                        "method": f"opencv_{method_name}_multi",
                        "left": pt[0],
                        "top": pt[1],
                        "width": template_w,
                        "height": template_h,
                        "center_x": center_x,
                        "center_y": center_y,
                        "confidence": float(confidence),
                        "region": region,
                    }
                )

                if len(matches) >= max_matches:
                    break

            # 按置信度排序
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            logger.info(f"找到 {len(matches)} 个匹配项")

            return matches

        except Exception as e:
            logger.error(f"多重匹配过程中发生错误: {e}")
            return []

    def click_template(
        self,
        template_path: str,
        config: Dict[str, Any] = None,
        region: Tuple[int, int, int, int] = None,
        button: str = "left",
        clicks: int = 1,
    ) -> bool:
        """
        查找并点击模板

        Args:
            template_path: 模板图片路径
            config: 匹配配置参数
            region: 搜索区域
            button: 鼠标按钮 ('left', 'right', 'middle')
            clicks: 点击次数

        Returns:
            是否成功点击
        """
        match_result = self.find_template_on_screen(template_path, config, region)

        if match_result:
            try:
                pyautogui.click(
                    match_result["center_x"],
                    match_result["center_y"],
                    clicks=clicks,
                    button=button,
                )
                logger.info(
                    f"成功点击位置: ({match_result['center_x']}, {match_result['center_y']})"
                )
                return True
            except Exception as e:
                logger.error(f"点击失败: {e}")
                return False
        else:
            logger.warning("未找到模板，无法点击")
            return False

    def get_template_info(self, template_path: str) -> Optional[Dict[str, Any]]:
        """
        获取模板图片信息

        Args:
            template_path: 模板图片路径

        Returns:
            模板信息字典
        """
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                return None

            height, width = template.shape[:2]
            return {
                "path": template_path,
                "width": width,
                "height": height,
                "channels": template.shape[2] if len(template.shape) > 2 else 1,
            }
        except Exception as e:
            logger.error(f"获取模板信息失败: {e}")
            return None


# 创建全局实例
template_matcher = TemplateMatchingEngine()


def find_template(template_path: str, **kwargs) -> Optional[Dict[str, Any]]:
    """便捷函数：查找模板"""
    return template_matcher.find_template_on_screen(template_path, kwargs)


def click_template(template_path: str, **kwargs) -> bool:
    """便捷函数：点击模板"""
    return template_matcher.click_template(template_path, kwargs)
