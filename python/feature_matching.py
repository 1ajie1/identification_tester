import cv2
import numpy as np
import time
from typing import Optional, Tuple, List, Dict, Any, Union
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ORBFeatureMatchingEngine:
    """
    基于OpenCV ORB的特征匹配引擎
    支持多种匹配策略和参数配置
    """

    def __init__(self):
        # 默认ORB配置参数
        self.default_orb_config = {
            "nfeatures": 1000,  # 最多保留的特征点数量
            "scaleFactor": 1.2,  # 金字塔缩放因子
            "nlevels": 8,  # 金字塔层数
            "edgeThreshold": 15,  # 边缘阈值（降低以检测更多特征点）
            "firstLevel": 0,  # 第一层索引
            "WTA_K": 2,  # 2点对WTA模式
            "scoreType": cv2.ORB_HARRIS_SCORE,  # HARRIS评分
            "patchSize": 31,  # 描述子计算邻域大小
            "fastThreshold": 10,  # FAST角点阈值（降低以检测更多特征点）
        }

        # 默认匹配配置
        self.default_match_config = {
            "distance_threshold": 0.8,  # 距离阈值（提高以允许更多匹配）
            "min_matches": 4,  # 最小匹配点数（降低以便测试）
            "max_retries": 3,  # 最大重试次数
            "retry_delay": 1.0,  # 重试间隔
            "use_ratio_test": False,  # 对于相同图片，不使用比值测试
            "use_cross_check": False,  # 对于相同图片，不使用交叉检查
            "homography_threshold": 5.0,  # 单应性矩阵RANSAC阈值
        }

        # 匹配器类型
        self.matcher_types = {
            "BF": "BruteForce",  # 暴力匹配
            "FLANN": "FLANN",  # FLANN匹配
        }

    def create_orb_detector(self, config: Dict[str, Any] = None) -> cv2.ORB:
        """
        创建ORB检测器

        Args:
            config: ORB配置参数

        Returns:
            配置好的ORB检测器
        """
        if config is None:
            config = self.default_orb_config.copy()

        # 合并配置
        orb_config = self.default_orb_config.copy()
        orb_config.update(config)

        logger.info(f"创建ORB检测器，配置: {orb_config}")

        # 创建ORB检测器
        orb = cv2.ORB_create(
            nfeatures=orb_config["nfeatures"],
            scaleFactor=orb_config["scaleFactor"],
            nlevels=orb_config["nlevels"],
            edgeThreshold=orb_config["edgeThreshold"],
            firstLevel=orb_config["firstLevel"],
            WTA_K=orb_config["WTA_K"],
            scoreType=orb_config["scoreType"],
            patchSize=orb_config["patchSize"],
            fastThreshold=orb_config["fastThreshold"],
        )

        return orb

    def create_matcher(
        self, matcher_type: str = "BF", cross_check: bool = True
    ) -> Union[cv2.BFMatcher, cv2.FlannBasedMatcher]:
        """
        创建特征匹配器

        Args:
            matcher_type: 匹配器类型 ('BF' 或 'FLANN')
            cross_check: 是否启用交叉检查

        Returns:
            配置好的匹配器
        """
        if matcher_type == "BF":
            # 创建暴力匹配器，使用汉明距离
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=cross_check)
            logger.info(f"创建BruteForce匹配器，交叉检查: {cross_check}")
        elif matcher_type == "FLANN":
            # FLANN参数
            FLANN_INDEX_LSH = 6
            index_params = dict(
                algorithm=FLANN_INDEX_LSH,
                table_number=6,  # 12
                key_size=12,  # 20
                multi_probe_level=1,  # 2
            )
            search_params = dict(checks=50)
            matcher = cv2.FlannBasedMatcher(index_params, search_params)
            logger.info("创建FLANN匹配器")
        else:
            raise ValueError(f"不支持的匹配器类型: {matcher_type}")

        return matcher

    def detect_and_compute(
        self, image: np.ndarray, orb_config: Dict[str, Any] = None
    ) -> Tuple[List, np.ndarray]:
        """
        检测关键点并计算描述子

        Args:
            image: 输入图像
            orb_config: ORB配置参数

        Returns:
            关键点列表和描述子数组
        """
        orb = self.create_orb_detector(orb_config)

        # 转换为灰度图像
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        logger.info(f"图像尺寸: {image.shape}, 灰度图尺寸: {gray.shape}")
        logger.info(
            f"图像数据类型: {gray.dtype}, 像素值范围: {gray.min()}-{gray.max()}"
        )

        # 检查图像是否有效
        if gray.size == 0:
            logger.error("输入图像为空")
            return [], None

        # 如果图像对比度太低，尝试增强对比度
        if gray.std() < 10:
            logger.warning(f"图像对比度较低 (std={gray.std():.2f})，尝试增强对比度")
            # 使用CLAHE增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            logger.info(
                f"对比度增强后像素值范围: {gray.min()}-{gray.max()}, std={gray.std():.2f}"
            )

        # 检测关键点并计算描述子
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        logger.info(f"检测到 {len(keypoints)} 个关键点")

        # 如果没有检测到关键点，尝试调整参数
        if len(keypoints) == 0:
            logger.warning("未检测到关键点，尝试降低阈值")

            # 创建更宽松的ORB检测器
            loose_config = (
                orb_config.copy() if orb_config else self.default_orb_config.copy()
            )
            loose_config.update(
                {
                    "fastThreshold": 5,  # 降低FAST阈值
                    "edgeThreshold": 10,  # 降低边缘阈值
                    "nfeatures": 2000,  # 增加特征点数量
                }
            )

            loose_orb = self.create_orb_detector(loose_config)
            keypoints, descriptors = loose_orb.detectAndCompute(gray, None)
            logger.info(f"宽松参数检测到 {len(keypoints)} 个关键点")

        return keypoints, descriptors

    def match_features(
        self,
        template_image: np.ndarray,
        target_image: np.ndarray,
        config: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        执行ORB特征匹配

        Args:
            template_image: 模板图像
            target_image: 目标图像
            config: 匹配配置参数

        Returns:
            匹配结果字典，未找到匹配则返回None
        """
        if config is None:
            config = self.default_match_config.copy()

        # 合并配置
        match_config = self.default_match_config.copy()
        match_config.update(config)

        max_retries = match_config.get("max_retries", 3)
        retry_delay = match_config.get("retry_delay", 1.0)

        for attempt in range(max_retries):
            try:
                logger.info(f"ORB特征匹配尝试 {attempt + 1}/{max_retries}")

                result = self._attempt_orb_matching(
                    template_image, target_image, match_config
                )

                if result:
                    logger.info(
                        f"ORB匹配成功！匹配点数: {result['num_matches']}, "
                        f"置信度: {result['confidence']:.3f}"
                    )
                    return result

                if attempt < max_retries - 1:
                    logger.info(
                        f"第 {attempt + 1} 次尝试失败，{retry_delay}秒后重试..."
                    )
                    time.sleep(retry_delay)

            except Exception as e:
                logger.error(f"ORB匹配过程中发生错误: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue

        logger.warning("所有ORB匹配重试都失败")
        return None

    def _attempt_orb_matching(
        self,
        template_image: np.ndarray,
        target_image: np.ndarray,
        config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        执行单次ORB匹配尝试

        Args:
            template_image: 模板图像
            target_image: 目标图像
            config: 匹配配置

        Returns:
            匹配结果字典
        """
        try:
            # 获取ORB配置参数
            orb_config = {
                "nfeatures": config.get("nfeatures", 1000),
                "scaleFactor": config.get("scaleFactor", 1.2),
                "nlevels": config.get("nlevels", 8),
                "edgeThreshold": config.get("edgeThreshold", 31),
                "firstLevel": config.get("firstLevel", 0),
                "WTA_K": config.get("WTA_K", 2),
                "scoreType": config.get("scoreType", cv2.ORB_HARRIS_SCORE),
                "patchSize": config.get("patchSize", 31),
                "fastThreshold": config.get("fastThreshold", 20),
            }

            # 检测关键点和描述子
            kp1, des1 = self.detect_and_compute(template_image, orb_config)
            kp2, des2 = self.detect_and_compute(target_image, orb_config)

            logger.info(
                f"模板图像关键点: {len(kp1)}, 描述子形状: {des1.shape if des1 is not None else None}"
            )
            logger.info(
                f"目标图像关键点: {len(kp2)}, 描述子形状: {des2.shape if des2 is not None else None}"
            )

            if des1 is None or des2 is None:
                logger.warning("无法计算描述子")
                return None

            if len(des1) < 4 or len(des2) < 4:
                logger.warning(f"描述子数量不足: 模板{len(des1)}, 目标{len(des2)}")
                return None

            # 创建匹配器
            matcher_type = config.get("matcher_type", "BF")
            use_cross_check = config.get("use_cross_check", True)
            matcher = self.create_matcher(matcher_type, use_cross_check)

            # 执行匹配
            if (
                config.get("use_ratio_test", True)
                and matcher_type == "BF"
                and not use_cross_check
            ):
                # 使用比值测试（与交叉检查互斥）
                matches = self._ratio_test_matching(matcher, des1, des2, config)
            else:
                # 直接匹配
                matches = matcher.match(des1, des2)

            logger.info(f"初始匹配数量: {len(matches)}")

            if len(matches) < config.get("min_matches", 10):
                logger.warning(f"匹配点数量不足: {len(matches)}")
                return None

            # 计算匹配质量和位置
            result = self._analyze_matches(
                kp1, kp2, matches, template_image, target_image, config
            )

            return result

        except Exception as e:
            logger.error(f"ORB匹配尝试失败: {e}")
            return None

    def _ratio_test_matching(
        self,
        matcher: cv2.BFMatcher,
        des1: np.ndarray,
        des2: np.ndarray,
        config: Dict[str, Any],
    ) -> List[cv2.DMatch]:
        """
        使用比值测试进行匹配

        Args:
            matcher: 匹配器
            des1: 模板描述子
            des2: 目标描述子
            config: 配置参数

        Returns:
            过滤后的匹配点列表
        """
        # 获取每个描述子的两个最佳匹配
        raw_matches = matcher.knnMatch(des1, des2, k=2)

        # 应用比值测试
        ratio_threshold = config.get("distance_threshold", 0.75)
        good_matches = []

        for match_pair in raw_matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append(m)

        logger.info(f"比值测试过滤: {len(raw_matches)} -> {len(good_matches)}")

        return good_matches

    def _analyze_matches(
        self,
        kp1: List,
        kp2: List,
        matches: List[cv2.DMatch],
        template_image: np.ndarray,
        target_image: np.ndarray,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        分析匹配结果

        Args:
            kp1: 模板关键点
            kp2: 目标关键点
            matches: 匹配点
            template_image: 模板图像
            target_image: 目标图像
            config: 配置参数

        Returns:
            分析结果字典
        """
        # 提取匹配点坐标
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        # 计算单应性矩阵
        homography = None
        inliers_mask = None
        num_inliers = 0

        if len(matches) >= 4:
            try:
                homography, inliers_mask = cv2.findHomography(
                    src_pts,
                    dst_pts,
                    cv2.RANSAC,
                    config.get("homography_threshold", 5.0),
                )

                if inliers_mask is not None:
                    num_inliers = np.sum(inliers_mask)

            except cv2.error as e:
                logger.warning(f"单应性矩阵计算失败: {e}")

        # 计算匹配质量
        total_matches = len(matches)
        inlier_ratio = num_inliers / total_matches if total_matches > 0 else 0

        # 计算平均匹配距离
        avg_distance = (
            np.mean([m.distance for m in matches]) if matches else float("inf")
        )

        # 计算置信度（基于内点比例和匹配数量）
        confidence = inlier_ratio * 0.7 + min(total_matches / 100, 1.0) * 0.3

        # 计算匹配区域的边界框
        bounding_box = None
        center_point = None

        if homography is not None and num_inliers >= 4:
            h, w = template_image.shape[:2]
            corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)

            try:
                transformed_corners = cv2.perspectiveTransform(corners, homography)

                # 计算边界框
                x_coords = transformed_corners[:, 0, 0]
                y_coords = transformed_corners[:, 0, 1]

                min_x, max_x = int(np.min(x_coords)), int(np.max(x_coords))
                min_y, max_y = int(np.min(y_coords)), int(np.max(y_coords))

                bounding_box = {
                    "left": min_x,
                    "top": min_y,
                    "right": max_x,
                    "bottom": max_y,
                    "width": max_x - min_x,
                    "height": max_y - min_y,
                }

                # 计算中心点
                center_point = {
                    "x": int((min_x + max_x) / 2),
                    "y": int((min_y + max_y) / 2),
                }

            except cv2.error as e:
                logger.warning(f"透视变换计算失败: {e}")

        result = {
            "method": "ORB_features",
            "num_matches": total_matches,
            "num_inliers": int(num_inliers),
            "inlier_ratio": float(inlier_ratio),
            "avg_distance": float(avg_distance),
            "confidence": float(confidence),
            "homography": homography.tolist() if homography is not None else None,
            "bounding_box": bounding_box,
            "center_point": center_point,
            "keypoints1": [(int(kp.pt[0]), int(kp.pt[1])) for kp in kp1],
            "keypoints2": [(int(kp.pt[0]), int(kp.pt[1])) for kp in kp2],
            "matches": [(m.queryIdx, m.trainIdx, float(m.distance)) for m in matches],
            "template_size": template_image.shape[:2],
            "target_size": target_image.shape[:2],
        }

        logger.info(
            f"匹配分析完成: 总匹配{total_matches}, 内点{num_inliers}, "
            f"内点比例{inlier_ratio:.3f}, 置信度{confidence:.3f}"
        )

        return result

    def draw_matches(
        self,
        template_image: np.ndarray,
        target_image: np.ndarray,
        match_result: Dict[str, Any],
        max_matches: int = 50,
        show_info_text: bool = False,
    ) -> np.ndarray:
        """
        绘制匹配结果

        Args:
            template_image: 模板图像
            target_image: 目标图像
            match_result: 匹配结果
            max_matches: 最大绘制匹配数量
            show_info_text: 是否在图像上显示文字信息

        Returns:
            绘制了匹配结果的图像
        """
        try:
            # 重新创建关键点对象
            kp1 = [cv2.KeyPoint(x, y, 1) for x, y in match_result["keypoints1"]]
            kp2 = [cv2.KeyPoint(x, y, 1) for x, y in match_result["keypoints2"]]

            # 重新创建匹配对象
            matches = [
                cv2.DMatch(qi, ti, d)
                for qi, ti, d in match_result["matches"][:max_matches]
            ]

            # 绘制匹配
            img_matches = cv2.drawMatches(
                template_image,
                kp1,
                target_image,
                kp2,
                matches,
                None,
                flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
            )

            # 如果有边界框，绘制它
            if match_result["bounding_box"] is not None:
                bbox = match_result["bounding_box"]
                offset_x = template_image.shape[1]  # 目标图像的x偏移

                # 在目标图像区域绘制边界框
                cv2.rectangle(
                    img_matches,
                    (bbox["left"] + offset_x, bbox["top"]),
                    (bbox["right"] + offset_x, bbox["bottom"]),
                    (0, 255, 0),
                    3,
                )

                # 绘制中心点
                if match_result["center_point"] is not None:
                    center = match_result["center_point"]
                    cv2.circle(
                        img_matches,
                        (center["x"] + offset_x, center["y"]),
                        5,
                        (0, 0, 255),
                        -1,
                    )

            # 只有在明确要求时才添加信息文本
            if show_info_text:
                info_text = [
                    f"Matches: {match_result['num_matches']}",
                    f"Inliers: {match_result['num_inliers']}",
                    f"Confidence: {match_result['confidence']:.3f}",
                ]

                y_offset = 30
                for i, text in enumerate(info_text):
                    cv2.putText(
                        img_matches,
                        text,
                        (10, y_offset + i * 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                    )

            return img_matches

        except Exception as e:
            logger.error(f"绘制匹配结果失败: {e}")
            return np.hstack([template_image, target_image])

    def find_template_in_image(
        self, template_path: str, target_path: str, config: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        在图像中查找模板

        Args:
            template_path: 模板图像路径
            target_path: 目标图像路径
            config: 匹配配置

        Returns:
            匹配结果字典
        """
        try:
            # 读取图像
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            target = cv2.imread(target_path, cv2.IMREAD_COLOR)

            if template is None or target is None:
                logger.error("无法读取图像文件")
                return None

            # 执行匹配
            result = self.match_features(template, target, config)

            return result

        except Exception as e:
            logger.error(f"图像模板匹配失败: {e}")
            return None


# 创建全局实例
orb_matcher = ORBFeatureMatchingEngine()


def match_orb_features(
    template_path: str, target_path: str, **kwargs
) -> Optional[Dict[str, Any]]:
    """便捷函数：ORB特征匹配"""
    return orb_matcher.find_template_in_image(template_path, target_path, kwargs)


def create_orb_detector(**kwargs) -> cv2.ORB:
    """便捷函数：创建ORB检测器"""
    return orb_matcher.create_orb_detector(kwargs)
