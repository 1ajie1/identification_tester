"""
基于OpenCV的模板匹配引擎
完全移除pyautogui依赖，避免DPI冲突问题
"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple, List, Dict, Any
import logging
import os
from PIL import Image, ImageGrab

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateMatchingEngine:
    """
    基于OpenCV的模板匹配引擎
    使用PIL进行屏幕截图，OpenCV进行模板匹配
    """

    def __init__(self):
        # OpenCV模板匹配方法映射
        self.matching_methods = {
            "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
            "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
            "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
            "TM_CCOEFF": cv2.TM_CCOEFF,
            "TM_CCORR": cv2.TM_CCORR,
            "TM_SQDIFF": cv2.TM_SQDIFF,
        }

        # 默认配置
        self.default_config = {
            "method": "TM_CCOEFF_NORMED",
            "threshold": 0.8,
            "max_retries": 3,
            "retry_delay": 1.0,  # 重试间隔（秒）
            "confidence_threshold": 0.9,  # 高置信度阈值
            "scale_range": [0.8, 1.2],  # 缩放范围
            "scale_steps": 5,  # 缩放步数
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

                # 使用OpenCV进行模板匹配
                result = self._attempt_opencv_match(template_path, config, region)

                if result:
                    logger.info(
                        f"匹配成功！位置: ({result['center_x']}, {result['center_y']}), "
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

    def _capture_screen(
        self, region: Tuple[int, int, int, int] = None
    ) -> Optional[np.ndarray]:
        """
        使用PIL捕获屏幕截图

        Args:
            region: 截图区域 (x, y, width, height)

        Returns:
            截图的numpy数组，BGR格式
        """
        try:
            if region:
                x, y, width, height = region
                screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            else:
                screenshot = ImageGrab.grab()

            # 转换为OpenCV格式 (BGR)
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot_cv

        except Exception as e:
            logger.error(f"屏幕截图失败: {e}")
            return None

    def _attempt_opencv_match(
        self,
        template_path: str,
        config: Dict[str, Any],
        region: Tuple[int, int, int, int] = None,
    ) -> Optional[Dict[str, Any]]:
        """使用OpenCV进行模板匹配"""
        try:
            # 读取模板图片
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"无法读取模板图片: {template_path}")
                return None

            # 截取屏幕
            screenshot = self._capture_screen(region)
            if screenshot is None:
                logger.error("屏幕截图失败")
                return None

            logger.info(f"模板尺寸: {template.shape}, 截图尺寸: {screenshot.shape}")

            # 执行模板匹配
            result = self._match_template(template, screenshot, config)

            if result and region:
                # 如果使用了区域截图，需要调整坐标
                result["left"] += region[0]
                result["top"] += region[1]
                result["center_x"] += region[0]
                result["center_y"] += region[1]
                result["region"] = region

            return result

        except Exception as e:
            logger.error(f"OpenCV匹配出错: {e}")
            return None

    def _match_template(
        self, template: np.ndarray, screenshot: np.ndarray, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        执行模板匹配

        Args:
            template: 模板图像
            screenshot: 屏幕截图
            config: 配置参数

        Returns:
            匹配结果或None
        """
        method_name = config.get("method", "TM_CCOEFF_NORMED")
        method = self.matching_methods.get(method_name, cv2.TM_CCOEFF_NORMED)
        threshold = config.get("threshold", 0.8)

        # 尝试多尺度匹配
        if config.get("scale_range") and config.get("scale_steps", 0) > 1:
            return self._multi_scale_match(
                template, screenshot, method, threshold, config
            )
        else:
            return self._single_scale_match(template, screenshot, method, threshold)

    def _single_scale_match(
        self,
        template: np.ndarray,
        screenshot: np.ndarray,
        method: int,
        threshold: float,
    ) -> Optional[Dict[str, Any]]:
        """单尺度模板匹配"""
        try:
            # 检查模板是否比截图大
            if (
                template.shape[0] > screenshot.shape[0]
                or template.shape[1] > screenshot.shape[1]
            ):
                logger.warning("模板图片比截图大，无法匹配")
                return None

            # 执行模板匹配
            result = cv2.matchTemplate(screenshot, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 根据方法选择合适的值和位置
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                match_val = min_val
                match_loc = min_loc
                confidence = (
                    1 - match_val
                    if method == cv2.TM_SQDIFF_NORMED
                    else 1 - (match_val / np.max(result))
                )
            else:
                match_val = max_val
                match_loc = max_loc
                confidence = match_val

            logger.debug(
                f"匹配值: {match_val}, 置信度: {confidence}, 阈值: {threshold}"
            )

            if confidence >= threshold:
                template_h, template_w = template.shape[:2]
                center_x = match_loc[0] + template_w // 2
                center_y = match_loc[1] + template_h // 2

                return {
                    "method": "opencv",
                    "left": int(match_loc[0]),
                    "top": int(match_loc[1]),
                    "width": int(template_w),
                    "height": int(template_h),
                    "center_x": int(center_x),
                    "center_y": int(center_y),
                    "confidence": float(confidence),
                    "match_value": float(match_val),
                    "scale": 1.0,
                }

            return None

        except Exception as e:
            logger.error(f"单尺度匹配失败: {e}")
            return None

    def _multi_scale_match(
        self,
        template: np.ndarray,
        screenshot: np.ndarray,
        method: int,
        threshold: float,
        config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """多尺度模板匹配"""
        try:
            scale_range = config.get("scale_range", [0.8, 1.2])
            scale_steps = config.get("scale_steps", 5)

            best_result = None
            best_confidence = 0

            # 生成缩放比例
            scales = np.linspace(scale_range[0], scale_range[1], scale_steps)

            for scale in scales:
                # 缩放模板
                scaled_template = cv2.resize(
                    template,
                    None,
                    fx=scale,
                    fy=scale,
                    interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC,
                )

                # 检查缩放后的模板是否合适
                if (
                    scaled_template.shape[0] > screenshot.shape[0]
                    or scaled_template.shape[1] > screenshot.shape[1]
                ):
                    continue

                # 执行匹配
                result = self._single_scale_match(
                    scaled_template, screenshot, method, threshold
                )

                if result and result["confidence"] > best_confidence:
                    best_confidence = result["confidence"]
                    result["scale"] = float(scale)
                    best_result = result

                    logger.debug(
                        f"尺度 {scale:.2f} 匹配置信度: {result['confidence']:.3f}"
                    )

            if best_result:
                logger.info(
                    f"最佳匹配尺度: {best_result['scale']:.2f}, 置信度: {best_result['confidence']:.3f}"
                )

            return best_result

        except Exception as e:
            logger.error(f"多尺度匹配失败: {e}")
            return None

    def find_template_in_image(
        self,
        template_path: str,
        target_image_path: str,
        config: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        在指定图片中查找模板

        Args:
            template_path: 模板图片路径
            target_image_path: 目标图片路径
            config: 匹配配置参数

        Returns:
            匹配结果字典，未找到则返回None
        """
        try:
            if config is None:
                config = self.default_config.copy()

            # 读取模板和目标图片
            template = cv2.imread(template_path)
            target = cv2.imread(target_image_path)

            if template is None:
                logger.error(f"无法读取模板图片: {template_path}")
                return None

            if target is None:
                logger.error(f"无法读取目标图片: {target_image_path}")
                return None

            logger.info(f"在图片中查找模板: {template_path} -> {target_image_path}")
            logger.info(f"模板尺寸: {template.shape}, 目标尺寸: {target.shape}")

            # 执行模板匹配
            result = self._match_template(template, target, config)

            if result:
                logger.info(
                    f"在图片中找到匹配！位置: ({result['center_x']}, {result['center_y']}), "
                    f"置信度: {result['confidence']:.3f}"
                )
            else:
                logger.info("在图片中未找到匹配")

            return result

        except Exception as e:
            logger.error(f"图片匹配过程中发生错误: {e}")
            return None

    def find_all_matches(
        self,
        template_path: str,
        config: Dict[str, Any] = None,
        region: Tuple[int, int, int, int] = None,
        max_matches: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        查找所有匹配项

        Args:
            template_path: 模板图片路径
            config: 匹配配置参数
            region: 搜索区域
            max_matches: 最大匹配数量

        Returns:
            匹配结果列表
        """
        try:
            if config is None:
                config = self.default_config.copy()

            # 读取模板图片
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"无法读取模板图片: {template_path}")
                return []

            # 截取屏幕
            screenshot = self._capture_screen(region)
            if screenshot is None:
                logger.error("屏幕截图失败")
                return []

            method_name = config.get("method", "TM_CCOEFF_NORMED")
            method = self.matching_methods.get(method_name, cv2.TM_CCOEFF_NORMED)
            threshold = config.get("threshold", 0.8)

            # 执行模板匹配
            result = cv2.matchTemplate(screenshot, template, method)

            # 查找所有匹配点
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                locations = np.where(result <= (1 - threshold))
            else:
                locations = np.where(result >= threshold)

            matches = []
            template_h, template_w = template.shape[:2]

            # 获取匹配点的置信度并排序
            match_points = []
            for pt in zip(*locations[::-1]):  # 交换x,y坐标
                if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                    confidence = 1 - result[pt[1], pt[0]]
                else:
                    confidence = result[pt[1], pt[0]]
                match_points.append((pt, confidence))

            # 按置信度排序
            match_points.sort(key=lambda x: x[1], reverse=True)

            # 非最大值抑制，避免重叠的匹配
            for pt, confidence in match_points[: max_matches * 3]:  # 取更多候选
                x, y = pt

                # 检查是否与已有匹配重叠
                overlap = False
                for existing_match in matches:
                    if (
                        abs(x - existing_match["left"]) < template_w * 0.5
                        and abs(y - existing_match["top"]) < template_h * 0.5
                    ):
                        overlap = True
                        break

                if not overlap:
                    center_x = x + template_w // 2
                    center_y = y + template_h // 2

                    match_result = {
                        "method": "opencv_all",
                        "left": int(x),
                        "top": int(y),
                        "width": int(template_w),
                        "height": int(template_h),
                        "center_x": int(center_x),
                        "center_y": int(center_y),
                        "confidence": float(confidence),
                    }

                    # 调整区域偏移
                    if region:
                        match_result["left"] += region[0]
                        match_result["top"] += region[1]
                        match_result["center_x"] += region[0]
                        match_result["center_y"] += region[1]
                        match_result["region"] = region

                    matches.append(match_result)

                    if len(matches) >= max_matches:
                        break

            logger.info(f"找到 {len(matches)} 个匹配项")
            return matches

        except Exception as e:
            logger.error(f"查找所有匹配项失败: {e}")
            return []

    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        try:
            screenshot = ImageGrab.grab()
            return screenshot.size
        except Exception as e:
            logger.error(f"获取屏幕尺寸失败: {e}")
            return (1920, 1080)  # 默认尺寸

    def save_match_result(
        self,
        result: Dict[str, Any],
        screenshot_path: str = None,
        template_path: str = None,
    ) -> Optional[str]:
        """
        保存匹配结果图片

        Args:
            result: 匹配结果
            screenshot_path: 截图保存路径
            template_path: 模板图片路径

        Returns:
            保存的图片路径
        """
        try:
            if not result:
                return None

            # 截取屏幕
            screenshot = self._capture_screen()
            if screenshot is None:
                return None

            # 在截图上绘制匹配框
            x, y = result["left"], result["top"]
            w, h = result["width"], result["height"]

            # 绘制绿色矩形框
            cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 添加置信度文本
            confidence_text = f"Confidence: {result['confidence']:.3f}"
            cv2.putText(
                screenshot,
                confidence_text,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # 保存图片
            if screenshot_path is None:
                screenshot_path = f"match_result_{int(time.time())}.png"

            cv2.imwrite(screenshot_path, screenshot)
            logger.info(f"匹配结果已保存: {screenshot_path}")
            return screenshot_path

        except Exception as e:
            logger.error(f"保存匹配结果失败: {e}")
            return None


# 创建全局实例
template_matcher = TemplateMatchingEngine()


# 便捷函数
def find_on_screen(template_path: str, **kwargs) -> Optional[Dict[str, Any]]:
    """便捷函数：在屏幕上查找模板"""
    return template_matcher.find_template_on_screen(template_path, **kwargs)


def find_in_image(
    template_path: str, target_path: str, **kwargs
) -> Optional[Dict[str, Any]]:
    """便捷函数：在图片中查找模板"""
    return template_matcher.find_template_in_image(template_path, target_path, **kwargs)


def find_all_on_screen(template_path: str, **kwargs) -> List[Dict[str, Any]]:
    """便捷函数：查找屏幕上所有匹配项"""
    return template_matcher.find_all_matches(template_path, **kwargs)
