import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs

ApplicationWindow {
    id: controlWindow
    width: 450
    height: 700
    visible: true
    title: "图片匹配器 - 控制面板"
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint

    // 现代化的颜色主题
    property color primaryColor: "#2196F3"
    property color secondaryColor: "#FFC107"
    property color backgroundColor: "#F5F5F5"
    property color cardColor: "#FFFFFF"
    property color textColor: "#333333"
    property color borderColor: "#E0E0E0"

    // 日志数据模型
    ListModel {
        id: logListModel

        Component.onCompleted: {
            addLog("系统初始化完成", "info");
            addLog("等待用户操作...", "info");
        }

        // 监听模型变化，确保滚动到底部
        onRowsInserted: {
            Qt.callLater(function () {
                if (logListView) {
                    logListView.positionViewAtEnd();
                }
            });
        }
    }

    // 添加日志的函数
    function addLog(message, type) {
        type = type || "info";
        var now = new Date();
        var timestamp = Qt.formatTime(now, "hh:mm:ss");

        logListModel.append({
            "timestamp": timestamp,
            "message": message,
            "type": type
        });

        // 限制日志条目数量（最多100条）
        if (logListModel.count > 100) {
            logListModel.remove(0);
        }

        // 延迟自动滚动到底部，确保内容已渲染
        Qt.callLater(function () {
            logListView.positionViewAtEnd();
        });
    }

    // 监听控制器信号，记录操作日志
    Connections {
        target: controller

        function onModeChanged(mode) {
            var modeText = mode === 0 ? "双图片匹配" : "屏幕窗口匹配";
            addLog("自动切换到" + modeText + "模式", "info");
        }

        function onAlgorithmModeChanged(mode) {
            var algorithmNames = ["模板匹配", "ORB特征匹配", "YOLO+ORB混合", "纯YOLO"];
            addLog("选择算法: " + algorithmNames[mode], "info");
        }

        function onNeedleImage(path) {
            var filename = path.split('/').pop() || path.split('\\').pop();
        }

        function onHaystackImage(path) {
            var filename = path.split('/').pop() || path.split('\\').pop();
        }

        function onWindowSelected(windowTitle) {
            addLog("选择窗口: " + windowTitle, "success");
        }

        function onLogAdded(message, type) {
            addLog(message, type);
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // 算法模式标题
        Text {
            text: "算法模式"
            font.pixelSize: 18
            font.bold: true
            color: textColor
            Layout.topMargin: 10
        }

        // 算法选择下拉框和设置按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            ComboBox {
                id: algorithmComboBox
                Layout.fillWidth: true
                height: 40

                model: ["🎯 模板匹配", "🔍 ORB 特征匹配", "🚀 YOLO + ORB", "🎯 纯 YOLO"]

                currentIndex: controller.algorithmMode

                onCurrentIndexChanged: {
                    if (currentIndex !== controller.algorithmMode) {
                        controller.switchAlgorithmMode(currentIndex);
                        // 根据算法模式自动设置输入模式
                        // 0: 模板匹配 -> 双图片匹配 (mode 0)
                        // 1: ORB特征匹配 -> 双图片匹配 (mode 0)
                        // 2: YOLO+ORB -> 屏幕窗口匹配 (mode 1)
                        // 3: 纯YOLO -> 屏幕窗口匹配 (mode 1)
                        if (currentIndex === 0 || currentIndex === 1) {
                            controller.switchMode(0); // 双图片匹配
                        } else if (currentIndex === 2 || currentIndex === 3) {
                            controller.switchMode(1); // 屏幕窗口匹配
                        }
                    }
                }

                // 监听控制器变化来同步下拉框
                Connections {
                    target: controller
                    function onAlgorithmModeChanged(mode) {
                        if (algorithmComboBox.currentIndex !== mode) {
                            algorithmComboBox.currentIndex = mode;
                        }
                    }
                }
            }

            // 算法设置按钮
            Button {
                id: settingsButton
                width: 40
                height: 40
                text: "⚙️"
                font.pixelSize: 16
                flat: true

                ToolTip.visible: hovered
                ToolTip.text: "算法参数设置"

                onClicked: {
                    settingsDialog.open();
                }
            }
        }

        // 开始匹配按钮
        Button {
            Layout.fillWidth: true
            height: 60
            text: "开始匹配"
            font.pixelSize: 16
            font.bold: true
            Layout.topMargin: 10

            enabled: (controller.currentMode === 0 && controller.image1Path && controller.image2Path) || (controller.currentMode === 1 && controller.selectedWindow)

            onClicked: {
                var algorithmNames = ["模板匹配", "ORB特征匹配", "YOLO+ORB混合", "纯YOLO"];
                addLog("开始执行匹配 - 算法: " + algorithmNames[controller.algorithmMode], "info");
                controller.startMatching();
            }
        }

        // 操作日志标题栏
        // RowLayout {
        //     Layout.fillWidth: true
        //     // spacing: 5
        //     // Layout.topMargin: 5

        //     Text {
        //         text: "📋 操作日志"
        //         font.pixelSize: 16
        //         font.bold: true
        //         color: textColor
        //     }

        //     // 日志数量标签
        //     Text {
        //         id: countText
        //         text: "(" + logListModel.count + " 条)"
        //         font.pixelSize: 12
        //         color: primaryColor
        //         font.bold: true
        //     }

        //     Item { Layout.fillWidth: true }

        //     // 清空按钮
        //     Button {
        //         text: "清空"
        //         height: 28
        //         font.pixelSize: 12
        //         flat: true

        //         onClicked: {
        //             logListModel.clear()
        //             addLog("日志已清空", "info")
        //         }
        //     }
        // }

        // 日志列表
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 200
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true

            Rectangle {
                width: parent.width
                height: parent.height
                border.width: 1
                border.color: borderColor
                radius: 6
                color: cardColor

                ListView {
                    id: logListView
                    anchors.fill: parent
                    model: logListModel
                    spacing: 4

                    // 确保ListView会自动调整大小
                    onCountChanged: {
                        Qt.callLater(function () {
                            positionViewAtEnd();
                        });
                    }

                    // 空状态提示
                    Text {
                        anchors.centerIn: parent
                        visible: logListModel.count === 0
                        text: "📝 暂无日志记录"
                        font.pixelSize: 14
                        color: "#999999"
                        opacity: 0.6
                    }

                    delegate: Rectangle {
                        width: logListView.width
                        height: Math.max(logContent.implicitHeight + 16, 40)
                        color: {
                            switch (type) {
                            case "error":
                                return "#FFEBEE";
                            case "warning":
                                return "#FFF8E1";
                            case "success":
                                return "#E8F5E8";
                            default:
                                return "transparent";
                            }
                        }
                        radius: 6
                        border.color: {
                            switch (type) {
                            case "error":
                                return "#FFCDD2";
                            case "warning":
                                return "#FFE0B2";
                            case "success":
                                return "#C8E6C9";
                            default:
                                return "transparent";
                            }
                        }
                        border.width: type !== "info" ? 1 : 0

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8

                            // 类型图标
                            Text {
                                text: {
                                    switch (type) {
                                    case "error":
                                        return "❌";
                                    case "warning":
                                        return "⚠️";
                                    case "success":
                                        return "✅";
                                    default:
                                        return "ℹ️";
                                    }
                                }
                                font.pixelSize: 14
                                Layout.alignment: Qt.AlignTop
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                // 时间戳
                                Text {
                                    text: timestamp
                                    font.pixelSize: 10
                                    color: "#888888"
                                    font.family: "Consolas, Monaco, monospace"
                                }

                                // 日志内容
                                Text {
                                    id: logContent
                                    Layout.fillWidth: true
                                    text: message
                                    font.pixelSize: 12
                                    color: {
                                        switch (type) {
                                        case "error":
                                            return "#D32F2F";
                                        case "warning":
                                            return "#F57C00";
                                        case "success":
                                            return "#388E3C";
                                        default:
                                            return "#424242";
                                        }
                                    }
                                    wrapMode: Text.Wrap
                                    lineHeight: 1.3
                                }
                            }
                        }

                        // 鼠标悬停效果
                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            onEntered: parent.opacity = 0.8
                            onExited: parent.opacity = 1.0
                        }
                    }
                }
            }
        }
    }

    // 算法参数设置对话框
    Dialog {
        id: settingsDialog
        title: "算法参数设置"
        width: Math.max(420, Math.min(460, controlWindow.width - 30))
        height: Math.max(450, Math.min(560, controlWindow.height - 80))
        modal: true

        // 居中显示
        x: (controlWindow.width - width) / 2
        y: (controlWindow.height - height) / 2

        // 设置最小尺寸
        property int minimumWidth: 420
        property int minimumHeight: 450

        onWidthChanged: {
            if (width < minimumWidth)
                width = minimumWidth;
        }

        onHeightChanged: {
            if (height < minimumHeight)
                height = minimumHeight;
        }

        // 对话框内容
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            // 当前算法显示
            Text {
                id: currentAlgorithmText
                text: "当前算法：" + algorithmComboBox.model[algorithmComboBox.currentIndex]
                font.pixelSize: 14
                font.bold: true
                color: primaryColor
            }

            // 参数设置区域
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 200
                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true
                contentWidth: -1  // 自动调整内容宽度

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    // 模板匹配参数
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        visible: algorithmComboBox.currentIndex === 0

                        // 匹配方法
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "匹配方法："
                                Layout.minimumWidth: 70
                            }
                            ComboBox {
                                id: templateMethodCombo
                                Layout.fillWidth: true
                                model: ["TM_CCOEFF_NORMED", "TM_CCORR_NORMED", "TM_SQDIFF_NORMED"]
                                currentIndex: 0
                            }
                        }

                        // 匹配阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "匹配阈值："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: templateThresholdSlider
                                Layout.fillWidth: true
                                from: 0.1
                                to: 1.0
                                value: 0.8
                                stepSize: 0.01
                            }
                            Text {
                                text: templateThresholdSlider.value.toFixed(2)
                                Layout.minimumWidth: 40
                            }
                        }

                        // 最大重试次数
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "重试次数："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: templateRetriesSpinBox
                                Layout.fillWidth: true
                                from: 1
                                to: 10
                                value: 3
                                stepSize: 1
                            }
                        }

                        // 重试间隔
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "重试间隔："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: templateRetryDelaySlider
                                Layout.fillWidth: true
                                from: 0.5
                                to: 5.0
                                value: 1.0
                                stepSize: 0.1
                            }
                            Text {
                                text: templateRetryDelaySlider.value.toFixed(1) + "s"
                                Layout.minimumWidth: 40
                            }
                        }
                    }

                    // ORB特征匹配参数
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        visible: algorithmComboBox.currentIndex === 1

                        // 特征点数量
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "特征点数量："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: orbFeaturesSpinBox
                                Layout.fillWidth: true
                                from: 100
                                to: 5000
                                value: 1000
                                stepSize: 100
                            }
                        }

                        // 金字塔缩放因子
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "缩放因子："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: orbScaleFactorSlider
                                Layout.fillWidth: true
                                from: 1.1
                                to: 2.0
                                value: 1.2
                                stepSize: 0.1
                            }
                            Text {
                                text: orbScaleFactorSlider.value.toFixed(1)
                                Layout.minimumWidth: 40
                            }
                        }

                        // 金字塔层数
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "金字塔层数："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: orbNlevelsSpinBox
                                Layout.fillWidth: true
                                from: 3
                                to: 12
                                value: 8
                                stepSize: 1
                            }
                        }

                        // 边缘阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "边缘阈值："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: orbEdgeThresholdSpinBox
                                Layout.fillWidth: true
                                from: 10
                                to: 50
                                value: 31
                                stepSize: 1
                            }
                        }

                        // FAST角点阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "FAST阈值："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: orbFastThresholdSpinBox
                                Layout.fillWidth: true
                                from: 5
                                to: 50
                                value: 20
                                stepSize: 1
                            }
                        }

                        // 匹配距离阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "距离阈值："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: orbDistanceSlider
                                Layout.fillWidth: true
                                from: 0.1
                                to: 1.0
                                value: 0.75
                                stepSize: 0.01
                            }
                            Text {
                                text: orbDistanceSlider.value.toFixed(2)
                                Layout.minimumWidth: 40
                            }
                        }

                        // 最小匹配点数
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "最小匹配点："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: orbMinMatchesSpinBox
                                Layout.fillWidth: true
                                from: 4
                                to: 100
                                value: 10
                                stepSize: 1
                            }
                        }

                        // 最大重试次数
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "重试次数："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: orbRetriesSpinBox
                                Layout.fillWidth: true
                                from: 1
                                to: 10
                                value: 3
                                stepSize: 1
                            }
                        }
                    }

                    // YOLO+ORB混合参数
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        visible: algorithmComboBox.currentIndex === 2

                        // YOLO置信度阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "YOLO置信度："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: yoloConfidenceSlider
                                Layout.fillWidth: true
                                from: 0.1
                                to: 1.0
                                value: 0.5
                                stepSize: 0.01
                            }
                            Text {
                                text: yoloConfidenceSlider.value.toFixed(2)
                                Layout.minimumWidth: 40
                            }
                        }

                        // NMS阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "NMS阈值："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: nmsThresholdSlider
                                Layout.fillWidth: true
                                from: 0.1
                                to: 1.0
                                value: 0.4
                                stepSize: 0.01
                            }
                            Text {
                                text: nmsThresholdSlider.value.toFixed(2)
                                Layout.minimumWidth: 40
                            }
                        }

                        // ORB特征点数量
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "ORB特征点："
                                Layout.minimumWidth: 70
                            }
                            SpinBox {
                                id: yoloOrbFeaturesSpinBox
                                Layout.fillWidth: true
                                from: 100
                                to: 3000
                                value: 500
                                stepSize: 50
                            }
                        }

                        // YOLO模型文件选择
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            Text {
                                text: "YOLO模型文件："
                                font.pixelSize: 12
                                color: "#666666"
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    color: "#F5F5F5"
                                    border.color: "#E0E0E0"
                                    border.width: 1
                                    radius: 4

                                    Text {
                                        id: yoloOrbModelPathText
                                        property string fullPath: ""
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.margins: 8
                                        text: "未选择模型文件"
                                        color: "#666666"
                                        elide: Text.ElideMiddle
                                        font.pixelSize: 11
                                    }
                                }

                                Button {
                                    text: "选择"
                                    Layout.preferredWidth: 60
                                    Layout.preferredHeight: 30
                                    onClicked: yoloOrbModelFileDialog.open()
                                }

                                Button {
                                    text: "清除"
                                    Layout.preferredWidth: 60
                                    Layout.preferredHeight: 30
                                    enabled: yoloOrbModelPathText.text !== "未选择模型文件"
                                    onClicked: {
                                        yoloOrbModelPathText.text = "未选择模型文件";
                                    }
                                }
                            }
                        }
                    }

                    // 纯YOLO参数
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        visible: algorithmComboBox.currentIndex === 3

                        // YOLO置信度阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "YOLO置信度："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: pureYoloConfidenceSlider
                                Layout.fillWidth: true
                                from: 0.1
                                to: 1.0
                                value: 0.5
                                stepSize: 0.01
                            }
                            Text {
                                text: pureYoloConfidenceSlider.value.toFixed(2)
                                Layout.minimumWidth: 40
                            }
                        }

                        // NMS阈值
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "NMS阈值："
                                Layout.minimumWidth: 70
                            }
                            Slider {
                                id: pureYoloNmsSlider
                                Layout.fillWidth: true
                                from: 0.1
                                to: 1.0
                                value: 0.4
                                stepSize: 0.01
                            }
                            Text {
                                text: pureYoloNmsSlider.value.toFixed(2)
                                Layout.minimumWidth: 40
                            }
                        }

                        // YOLO模型文件选择
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            Text {
                                text: "YOLO模型文件："
                                font.pixelSize: 12
                                color: "#666666"
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    color: "#F5F5F5"
                                    border.color: "#E0E0E0"
                                    border.width: 1
                                    radius: 4

                                    Text {
                                        id: pureYoloModelPathText
                                        property string fullPath: ""
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.margins: 8
                                        text: "未选择模型文件"
                                        color: "#666666"
                                        elide: Text.ElideMiddle
                                        font.pixelSize: 11
                                    }
                                }

                                Button {
                                    text: "选择"
                                    Layout.preferredWidth: 60
                                    Layout.preferredHeight: 30
                                    onClicked: pureYoloModelFileDialog.open()
                                }

                                Button {
                                    text: "清除"
                                    Layout.preferredWidth: 60
                                    Layout.preferredHeight: 30
                                    enabled: pureYoloModelPathText.text !== "未选择模型文件"
                                    onClicked: {
                                        pureYoloModelPathText.text = "未选择模型文件";
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // 按钮区域
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 5
                Layout.preferredHeight: 35
                spacing: 10

                Button {
                    text: "重置默认"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 35
                    onClicked: resetToDefaults()
                }

                Button {
                    text: "应用设置"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 35
                    highlighted: true
                    onClicked: {
                        applySettings();
                        settingsDialog.close();
                    }
                }

                Button {
                    text: "取消"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 35
                    onClicked: settingsDialog.close()
                }
            }
        }
    }

    // 重置为默认值的函数
    function resetToDefaults() {
        // 模板匹配默认值
        templateMethodCombo.currentIndex = 0;
        templateThresholdSlider.value = 0.8;
        templateRetriesSpinBox.value = 3;
        templateRetryDelaySlider.value = 1.0;

        // ORB默认值
        orbFeaturesSpinBox.value = 1000;
        orbScaleFactorSlider.value = 1.2;
        orbNlevelsSpinBox.value = 8;
        orbEdgeThresholdSpinBox.value = 15;
        orbFastThresholdSpinBox.value = 10;
        orbDistanceSlider.value = 0.8;
        orbMinMatchesSpinBox.value = 4;
        orbRetriesSpinBox.value = 3;

        // YOLO+ORB默认值
        yoloConfidenceSlider.value = 0.5;
        nmsThresholdSlider.value = 0.4;
        yoloOrbFeaturesSpinBox.value = 500;
        yoloOrbModelPathText.text = "未选择模型文件";
        yoloOrbModelPathText.fullPath = "";

        // 纯YOLO默认值
        pureYoloConfidenceSlider.value = 0.5;
        pureYoloNmsSlider.value = 0.4;
        pureYoloModelPathText.text = "未选择模型文件";
        pureYoloModelPathText.fullPath = "";

        addLog("参数已重置为默认值", "info");
    }

    // 应用设置的函数
    function applySettings() {
        var settings = {};

        switch (algorithmComboBox.currentIndex) {
        case 0: // 模板匹配
            settings = {
                method: templateMethodCombo.currentText,
                threshold: templateThresholdSlider.value,
                max_retries: templateRetriesSpinBox.value,
                retry_delay: templateRetryDelaySlider.value
            };
            break;
        case 1: // ORB
            settings = {
                nfeatures: orbFeaturesSpinBox.value,
                scaleFactor: orbScaleFactorSlider.value,
                nlevels: orbNlevelsSpinBox.value,
                edgeThreshold: orbEdgeThresholdSpinBox.value,
                fastThreshold: orbFastThresholdSpinBox.value,
                distance_threshold: orbDistanceSlider.value,
                min_matches: orbMinMatchesSpinBox.value,
                max_retries: orbRetriesSpinBox.value
            };
            break;
        case 2: // YOLO+ORB
            settings = {
                yolo_confidence: yoloConfidenceSlider.value,
                nms_threshold: nmsThresholdSlider.value,
                orb_nfeatures: yoloOrbFeaturesSpinBox.value,
                model_path: yoloOrbModelPathText.fullPath || ""
            };
            break;
        case 3: // 纯YOLO
            settings = {
                confidence_threshold: pureYoloConfidenceSlider.value,
                nms_threshold: pureYoloNmsSlider.value,
                model_path: pureYoloModelPathText.fullPath || ""
            };
            break;
        }

        // 调用控制器保存设置
        controller.updateAlgorithmSettings(algorithmComboBox.currentIndex, JSON.stringify(settings));

        var algorithmNames = ["模板匹配", "ORB特征匹配", "YOLO+ORB混合", "纯YOLO"];
        addLog("已更新 " + algorithmNames[algorithmComboBox.currentIndex] + " 参数设置", "success");
    }

    // 匹配结果显示对话框
    Dialog {
        id: resultDialog
        title: "匹配结果"
        width: Math.min(800, controlWindow.width * 0.9)
        height: Math.min(600, controlWindow.height * 0.9)
        modal: true

        property string resultImagePath: ""
        property string resultTitle: ""

        // 居中显示
        x: (controlWindow.width - width) / 2
        y: (controlWindow.height - height) / 2

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            // 结果标题
            Text {
                id: resultTitleText
                text: resultDialog.resultTitle
                font.pixelSize: 16
                font.bold: true
                color: primaryColor
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }

            // 图片显示区域
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                Image {
                    id: resultImage
                    source: resultDialog.resultImagePath ? "file:///" + resultDialog.resultImagePath : ""
                    fillMode: Image.PreserveAspectFit

                    onStatusChanged: {
                        if (status === Image.Error) {
                            console.log("图片加载失败:", resultDialog.resultImagePath);
                        }
                    }
                }
            }

            // 按钮区域
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 35

                Item {
                    Layout.fillWidth: true
                }

                Button {
                    text: "保存图片"
                    Layout.preferredHeight: 35
                    onClicked: {
                        // TODO: 实现保存功能
                        addLog("保存功能开发中...", "info");
                    }
                }

                Button {
                    text: "关闭"
                    Layout.preferredHeight: 35
                    highlighted: true
                    onClicked: resultDialog.close()
                }
            }
        }
    }

    // 监听控制器的结果显示信号
    Connections {
        target: controller
        function onShowMatchResult(imagePath, title) {
            resultDialog.resultImagePath = imagePath;
            resultDialog.resultTitle = title;
            resultDialog.open();
            addLog("显示匹配结果: " + title, "info");
        }
    }

    // YOLO+ORB模型文件选择对话框
    FileDialog {
        id: yoloOrbModelFileDialog
        title: "选择YOLO+ORB模型文件"
        nameFilters: ["YOLO模型文件 (*.weights *.pt *.onnx)", "所有文件 (*)"]
        onAccepted: {
            var filePath = selectedFile.toString().replace("file:///", "");
            var filename = filePath.split('/').pop() || filePath.split('\\').pop();
            yoloOrbModelPathText.text = filename;
            yoloOrbModelPathText.fullPath = filePath;
            addLog("选择YOLO+ORB模型文件: " + filename, "info");
        }
        onRejected: {
            addLog("取消选择YOLO+ORB模型文件", "info");
        }
    }

    // 纯YOLO模型文件选择对话框
    FileDialog {
        id: pureYoloModelFileDialog
        title: "选择纯YOLO模型文件"
        nameFilters: ["YOLO模型文件 (*.weights *.pt *.onnx)", "所有文件 (*)"]
        onAccepted: {
            var filePath = selectedFile.toString().replace("file:///", "");
            var filename = filePath.split('/').pop() || filePath.split('\\').pop();
            pureYoloModelPathText.text = filename;
            pureYoloModelPathText.fullPath = filePath;
            addLog("选择纯YOLO模型文件: " + filename, "info");
        }
        onRejected: {
            addLog("取消选择纯YOLO模型文件", "info");
        }
    }
}
