import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs

ApplicationWindow {
    id: displayWindow
    width: 800
    height: 600
    visible: true
    title: "图片匹配器 - 显示窗口"
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint

    // 现代化的颜色主题
    property color primaryColor: "#2196F3"
    property color secondaryColor: "#FFC107"
    property color backgroundColor: "#F5F5F5"
    property color cardColor: "#FFFFFF"
    property color textColor: "#333333"
    property color borderColor: "#E0E0E0"

    // 主显示区域 - 只保留核心显示功能

    StackLayout {
        id: displayStack
        anchors.fill: parent
        anchors.margins: 20
        currentIndex: controller.currentMode

        // 双图片模式显示
        Item {
            RowLayout {
                anchors.fill: parent
                spacing: 20

                // 第一张图片显示区域
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "white"
                        radius: 6
                        border.color: borderColor
                        border.width: 1

                        Image {
                            id: image1Display
                            anchors.fill: parent
                            anchors.margins: 10
                            source: controller.image1Path ? "file:///" + controller.image1Path : ""
                            fillMode: Image.PreserveAspectFit
                            visible: controller.image1Path !== ""

                            onStatusChanged: {
                                if (status === Image.Error) {
                                    console.log("加载图片1失败: " + controller.image1Path);
                                }
                            }
                        }

                        // 占位符和选择按钮
                        Column {
                            anchors.centerIn: parent
                            spacing: 15
                            visible: !image1Display.visible

                            Rectangle {
                                width: 80
                                height: 80
                                color: "#F0F0F0"
                                radius: 40
                                anchors.horizontalCenter: parent.horizontalCenter

                                Text {
                                    anchors.centerIn: parent
                                    text: "🖼️"
                                    font.pixelSize: 32
                                }
                            }

                            Text {
                                text: "请选择模板图片"
                                font.pixelSize: 14
                                color: "#666666"
                                anchors.horizontalCenter: parent.horizontalCenter
                            }

                            Button {
                                text: "选择图片"
                                anchors.horizontalCenter: parent.horizontalCenter
                                onClicked: fileDialog1.open()
                            }
                        }

                        // 图片上的选择按钮
                        Button {
                            anchors.top: parent.top
                            anchors.right: parent.right
                            anchors.margins: 10
                            text: "更换"
                            visible: image1Display.visible
                            onClicked: fileDialog1.open()
                        }
                    }

                    Text {
                        text: "模板图片: " + (controller.image1Path ? controller.image1Path.split('/').pop() || controller.image1Path.split('\\').pop() : "未选择文件")
                        font.pixelSize: 12
                        color: "#666666"
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                }

                // 分隔线和VS标识
                Rectangle {
                    Layout.preferredWidth: 60
                    Layout.fillHeight: true
                    color: "transparent"

                    Column {
                        anchors.centerIn: parent
                        spacing: 10

                        Rectangle {
                            width: 50
                            height: 50
                            color: primaryColor
                            radius: 25
                            anchors.horizontalCenter: parent.horizontalCenter

                            Text {
                                anchors.centerIn: parent
                                text: "VS"
                                font.pixelSize: 16
                                font.bold: true
                                color: "white"
                            }
                        }

                        Rectangle {
                            width: 2
                            height: 100
                            color: borderColor
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }
                }

                // 第二张图片显示区域
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "white"
                        radius: 6
                        border.color: borderColor
                        border.width: 1

                        Image {
                            id: image2Display
                            anchors.fill: parent
                            anchors.margins: 10
                            source: controller.image2Path ? "file:///" + controller.image2Path : ""
                            fillMode: Image.PreserveAspectFit
                            visible: controller.image2Path !== ""

                            onStatusChanged: {
                                if (status === Image.Error) {
                                    console.log("加载图片2失败: " + controller.image2Path);
                                }
                            }
                        }

                        // 占位符和选择按钮
                        Column {
                            anchors.centerIn: parent
                            spacing: 15
                            visible: !image2Display.visible

                            Rectangle {
                                width: 80
                                height: 80
                                color: "#F0F0F0"
                                radius: 40
                                anchors.horizontalCenter: parent.horizontalCenter

                                Text {
                                    anchors.centerIn: parent
                                    text: "🖼️"
                                    font.pixelSize: 32
                                }
                            }

                            Text {
                                text: "请选择待匹配的图片"
                                font.pixelSize: 14
                                color: "#666666"
                                anchors.horizontalCenter: parent.horizontalCenter
                            }

                            Button {
                                text: "选择图片"
                                anchors.horizontalCenter: parent.horizontalCenter
                                onClicked: fileDialog2.open()
                            }
                        }

                        // 图片上的选择按钮
                        Button {
                            anchors.top: parent.top
                            anchors.right: parent.right
                            anchors.margins: 10
                            text: "更换"
                            visible: image2Display.visible
                            onClicked: fileDialog2.open()
                        }
                    }

                    Text {
                        text: "待匹配的图片: " + (controller.image2Path ? controller.image2Path.split('/').pop() || controller.image2Path.split('\\').pop() : "未选择文件")
                        font.pixelSize: 12
                        color: "#666666"
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        }

        // 屏幕窗口模式显示 - 支持实时区域预览
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 20

                // 实时区域显示或选择界面
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "white"
                    radius: 6
                    border.color: borderColor
                    border.width: 1

                    // 实时区域图像显示
                    Image {
                        id: screenAreaImage
                        anchors.fill: parent
                        anchors.margins: 10
                        source: controller.screenAreaImagePath ? "file:///" + controller.screenAreaImagePath : ""
                        fillMode: Image.PreserveAspectFit
                        visible: controller.screenAreaImagePath !== ""
                        cache: false  // 禁用缓存以确保实时更新

                        onStatusChanged: {
                            if (status === Image.Error) {
                                console.log("加载屏幕区域图片失败: " + controller.screenAreaImagePath);
                            }
                        }
                    }

                    // 选择界面（当没有选择区域时显示）
                    Column {
                        anchors.centerIn: parent
                        spacing: 20
                        visible: !screenAreaImage.visible

                        Rectangle {
                            width: 120
                            height: 120
                            color: "#F0F0F0"
                            radius: 60
                            anchors.horizontalCenter: parent.horizontalCenter

                            Text {
                                anchors.centerIn: parent
                                text: "🎯"
                                font.pixelSize: 48
                            }
                        }

                        Text {
                            text: "请选择屏幕区域"
                            font.pixelSize: 16
                            color: "#666666"
                            anchors.horizontalCenter: parent.horizontalCenter
                        }

                        Button {
                            id: windowSelectorButton
                            text: windowSelector.isSelecting ? "选择区域中..." : "🎯 选择屏幕区域"
                            anchors.horizontalCenter: parent.horizontalCenter
                            enabled: !windowSelector.isSelecting

                            onPressed: {
                                windowSelector.startSelection();
                            }
                        }

                        Text {
                            text: "点击按钮后右键拖拽选择屏幕区域"
                            font.pixelSize: 12
                            color: "#999999"
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }

                    // 重新选择按钮（当有区域显示时）
                    Button {
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 10
                        text: "重新选择"
                        visible: screenAreaImage.visible
                        enabled: !windowSelector.isSelecting
                        onClicked: {
                            windowSelector.startSelection();
                        }
                    }
                }

                // 区域信息显示
                Text {
                    Layout.fillWidth: true
                    text: controller.selectedWindow ? "实时显示: " + controller.selectedWindow : "未选择区域"
                    font.pixelSize: 12
                    color: "#666666"
                    elide: Text.ElideMiddle
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    // 文件选择对话框
    FileDialog {
        id: fileDialog1
        title: "选择第一张图片"
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)", "所有文件 (*)"]
        onAccepted: {
            var filePath = selectedFile.toString().replace("file:///", "");
            addLog("用户选择模板图片: " + (filePath.split('/').pop() || filePath.split('\\').pop()), "info");
            controller.selectImage1(filePath);
        }
    }

    FileDialog {
        id: fileDialog2
        title: "选择第二张图片"
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)", "所有文件 (*)"]
        onAccepted: {
            var filePath = selectedFile.toString().replace("file:///", "");
            addLog("用户选择待匹配的图片: " + (filePath.split('/').pop() || filePath.split('\\').pop()), "info");
            controller.selectImage2(filePath);
        }
    }

    // 窗口选择器组件
    Item {
        id: windowSelector
        property bool isSelecting: false

        function startSelection() {
            isSelecting = true;
            addLog("启动窗口选择器", "info");
            // 创建全屏透明窗口用于拖拽选择
            var component = Qt.createComponent("WindowSelectorOverlay.qml");
            if (component.status === Component.Ready) {
                var overlay = component.createObject(displayWindow);

                overlay.areaSelected.connect(function (areaRect) {
                    let rectJson = JSON.stringify({
                        x: areaRect.x,
                        y: areaRect.y,
                        width: areaRect.width,
                        height: areaRect.height
                    });
                    controller.selectScreenArea(rectJson);
                    windowSelector.isSelecting = false;
                    addLog("屏幕区域选择完成", "success");
                    overlay.destroy();
                });

                overlay.selectionCancelled.connect(function () {
                    windowSelector.isSelecting = false;
                    addLog("区域选择已取消", "warning");
                    overlay.destroy();
                });
                overlay.show();
            } else {
                // 如果没有overlay组件，提示开发中
                addLog("窗口选择器组件开发中", "error");
                windowSelector.isSelecting = false;
            }
        }
    }

    // 添加日志输出功能
    property var logFunction: null

    // 屏幕匹配结果覆盖层
    property var screenMatchOverlay: null

    // 多个检测结果覆盖层数组
    property var multipleDetectionOverlays: []

    function addLog(message, type) {
        // 通过全局信号发送日志到控制窗口
        controller.addLog(message, type || "info");
    }

    function showScreenMatchOverlay(x, y, width, height, confidence, title) {
        // 创建屏幕匹配结果覆盖层
        if (screenMatchOverlay) {
            screenMatchOverlay.closeWithAnimation();
            screenMatchOverlay = null;
        }

        var component = Qt.createComponent("MatchResultOverlay.qml");
        if (component.status === Component.Ready) {
            screenMatchOverlay = component.createObject(null, {
                "autoClose": true,
                "autoCloseDelay": 10000  // 10秒后自动关闭
            });

            if (screenMatchOverlay) {
                // 连接信号
                screenMatchOverlay.overlayClicked.connect(function () {
                    addLog("用户点击了匹配结果覆盖层", "info");
                });

                screenMatchOverlay.overlayClosed.connect(function () {
                    screenMatchOverlay = null;
                    addLog("匹配结果覆盖层已关闭", "info");
                });

                screenMatchOverlay.showMatchResult(x, y, width, height, confidence, title);
                addLog(`显示屏幕匹配结果覆盖层: ${title}`, "success");
            }
        } else {
            addLog("无法创建匹配结果覆盖层", "error");
        }
    }

    function showMultipleDetections(detectionsJson) {
        // 清理之前的覆盖层
        closeMultipleDetectionOverlays();

        try {
            var detections = JSON.parse(detectionsJson);
            addLog(`显示 ${detections.length} 个检测结果`, "success");

            var component = Qt.createComponent("MatchResultOverlay.qml");
            if (component.status === Component.Ready) {
                for (var i = 0; i < detections.length; i++) {
                    var detection = detections[i];
                    var overlay = component.createObject(null, {
                        "autoClose": true,
                        "autoCloseDelay": 15000  // 15秒后自动关闭
                    });

                    if (overlay) {
                        // 连接信号
                        overlay.overlayClicked.connect(function () {
                            addLog("用户点击了检测结果覆盖层", "info");
                        });

                        overlay.overlayClosed.connect(function () {
                            // 从数组中移除已关闭的覆盖层
                            for (var j = 0; j < multipleDetectionOverlays.length; j++) {
                                if (multipleDetectionOverlays[j] === overlay) {
                                    multipleDetectionOverlays.splice(j, 1);
                                    break;
                                }
                            }
                            addLog("检测结果覆盖层已关闭", "info");
                        });

                        var title = `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`;
                        overlay.showMatchResult(detection.screen_x, detection.screen_y, detection.width, detection.height, detection.confidence, title);
                        multipleDetectionOverlays.push(overlay);
                    }
                }
            } else {
                addLog("无法创建检测结果覆盖层", "error");
            }
        } catch (e) {
            addLog(`解析检测结果失败: ${e}`, "error");
        }
    }

    function closeMultipleDetectionOverlays() {
        // 关闭所有多个检测结果覆盖层
        for (var i = 0; i < multipleDetectionOverlays.length; i++) {
            if (multipleDetectionOverlays[i]) {
                multipleDetectionOverlays[i].close();
            }
        }
        multipleDetectionOverlays = [];
    }

    // 监听控制器信号，更新显示
    Connections {
        target: controller

        function onModeChanged(mode) {
            displayStack.currentIndex = mode;
            var modeText = mode === 0 ? "双图片匹配" : "屏幕窗口匹配";
            addLog("显示窗口切换到" + modeText + "模式", "info");
        }

        function onNeedleImage(path) {
            var filename = path.split('/').pop() || path.split('\\').pop();
            addLog("模板图片加载完成: " + filename, "success");
        }

        function onHaystackImage(path) {
            var filename = path.split('/').pop() || path.split('\\').pop();
            addLog("待匹配的图片加载完成: " + filename, "success");
        }

        function onWindowSelected(windowTitle) {
            addLog("屏幕区域选择完成: " + windowTitle, "success");
        }

        function onShowScreenMatchOverlay(x, y, width, height, confidence, title) {
            showScreenMatchOverlay(x, y, width, height, confidence, title);
        }

        function onShowMultipleDetections(detectionsJson) {
            showMultipleDetections(detectionsJson);
        }

        function onScreenAreaImageChanged(imagePath) {
            // 强制刷新图像显示
            if (screenAreaImage) {
                screenAreaImage.source = "";
                screenAreaImage.source = imagePath ? "file:///" + imagePath : "";
            }
        }
    }
}
