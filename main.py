import sys
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QmlElement, qmlRegisterType, QQmlApplicationEngine
from PySide6.QtQuick import QQuickView
from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl

QML_IMPORT_NAME = "ImageMatcher"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ImageMatcherController(QObject):
    # 信号定义
    modeChanged = Signal(int)  # 模式改变信号 (0: 双图片模式, 1: 屏幕窗口模式)
    algorithmModeChanged = Signal(
        int
    )  # 算法模式改变信号 (0: 模板匹配, 1: ORB, 2: YOLO+ORB)
    image1Selected = Signal(str)  # 第一张图片选择信号
    image2Selected = Signal(str)  # 第二张图片选择信号
    windowSelected = Signal(str)  # 屏幕窗口选择信号
    logAdded = Signal(str, str)  # 日志添加信号 (message, type)

    def __init__(self):
        super().__init__()
        self._current_mode = 0  # 0: 双图片模式, 1: 屏幕窗口模式
        self._algorithm_mode = 0  # 0: 模板匹配, 1: ORB, 2: YOLO+ORB
        self._image1_path = ""
        self._image2_path = ""
        self._selected_window = ""

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
    @Property(str, notify=image1Selected)
    def image1Path(self):
        return self._image1_path

    @Property(str, notify=image2Selected)
    def image2Path(self):
        return self._image2_path

    @Property(str, notify=windowSelected)
    def selectedWindow(self):
        return self._selected_window

    @Slot(int)
    def switchMode(self, mode):
        """切换输入模式"""
        self.currentMode = mode
        print(f"切换到输入模式: {'双图片匹配' if mode == 0 else '屏幕窗口匹配'}")

    @Slot(int)
    def switchAlgorithmMode(self, mode):
        """切换算法模式"""
        self.algorithmMode = mode
        algorithm_names = ["模板匹配", "OpenCV ORB特征匹配", "YOLO+ORB混合匹配"]
        print(f"切换到算法模式: {algorithm_names[mode]}")

    @Slot(str)
    def selectImage1(self, path):
        """选择第一张图片"""
        self._image1_path = path
        self.image1Selected.emit(path)
        print(f"选择第一张图片: {path}")

    @Slot(str)
    def selectImage2(self, path):
        """选择第二张图片"""
        self._image2_path = path
        self.image2Selected.emit(path)
        print(f"选择第二张图片: {path}")

    @Slot(str)
    def selectWindow(self, window_title):
        """选择屏幕窗口"""
        self._selected_window = window_title
        self.windowSelected.emit(window_title)
        print(f"选择窗口: {window_title}")

    @Slot()
    def startMatching(self):
        """开始匹配"""
        algorithm_names = ["模板匹配", "OpenCV ORB特征匹配", "YOLO+ORB混合匹配"]
        if self._current_mode == 0:
            print(f"开始匹配图片: {self._image1_path} vs {self._image2_path}")
            print(f"使用算法: {algorithm_names[self._algorithm_mode]}")
        else:
            print(f"开始匹配屏幕窗口: {self._selected_window}")
            print(f"使用算法: {algorithm_names[self._algorithm_mode]}")

    @Slot(str, str)
    def addLog(self, message, log_type):
        """添加日志"""
        self.logAdded.emit(message, log_type)


class ImageMatcherApp:
    def __init__(self):
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
    app = ImageMatcherApp()
    sys.exit(app.run())
