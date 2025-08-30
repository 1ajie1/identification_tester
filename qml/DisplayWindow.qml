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
    
    // 阻止默认的关闭行为，只隐藏窗口
    onClosing: function(close) {
        close.accepted = false  // 阻止默认关闭
        displayWindow.hide()    // 只隐藏窗口
        addLog("显示窗口已隐藏 - 可通过托盘菜单重新显示", "info")
    }

    // 现代化的颜色主题
    property color primaryColor: "#2196F3"
    property color secondaryColor: "#FFC107"
    property color backgroundColor: "#F5F5F5"
    property color cardColor: "#FFFFFF"
    property color textColor: "#333333"
    property color borderColor: "#E0E0E0"

    // 颜色映射函数（保留作为备用）
    function getClassColor(classId) {
        // 这个函数现在主要作为备用，实际颜色由后端动态生成
        const colors = [
            "#FF0000",  // 红色 - class_0
            "#00FF00",  // 绿色 - class_1
            "#0000FF",  // 蓝色 - class_2
            "#FFFF00",  // 黄色 - class_3
            "#FF00FF",  // 洋红 - class_4
            "#00FFFF",  // 青色 - class_5
            "#FFA500",  // 橙色 - class_6
            "#800080",  // 紫色 - class_7
            "#FFC0CB",  // 粉色 - class_8
            "#A52A2A"   // 棕色 - class_9
        ];
        return colors[classId % colors.length];
    }

    // 主显示区域 - 只保留核心显示功能
    
    // 状态栏数据
    property real currentFPS: 0.0
    property real currentLatency: 0.0
    property string deviceInfo: "CPU"

    StackLayout {
        id: displayStack
        anchors.fill: parent
        anchors.margins: 20
        anchors.bottomMargin: 60  // 为状态栏留出空间
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
                    Item {
                        anchors.fill: parent
                        anchors.margins: 10
                        
                        Item {
                            anchors.fill: parent
                            
                            Image {
                                id: screenAreaImage
                                anchors.fill: parent
                                source: controller.screenAreaImagePath ? "file:///" + controller.screenAreaImagePath : ""
                                fillMode: Image.PreserveAspectFit  // 保持宽高比并适应容器
                                visible: controller.screenAreaImagePath !== ""
                                cache: false  // 禁用缓存以确保实时更新
                                smooth: true  // 启用平滑缩放
                                
                                // 添加背景以便看清图片边界
                                Rectangle {
                                    anchors.fill: parent
                                    color: "transparent"
                                    border.color: "#E0E0E0"
                                    border.width: 1
                                    z: -1
                                }

                                // 添加鼠标区域以支持缩放查看
                                MouseArea {
                                    anchors.fill: parent
                                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                                    
                                    onDoubleClicked: {
                                        // 双击切换原始尺寸和适应尺寸
                                        if (screenAreaImage.fillMode === Image.PreserveAspectFit) {
                                            screenAreaImage.fillMode = Image.PreserveAspectCrop;
                                            console.log("切换到裁剪模式");
                                        } else {
                                            screenAreaImage.fillMode = Image.PreserveAspectFit;
                                            console.log("切换到适应模式");
                                        }
                                    }
                                    
                                    onClicked: function(mouse) {
                                        if (mouse.button === Qt.RightButton) {
                                            if (controller.screenAreaImagePath) {
                                                Qt.openUrlExternally("file:///" + controller.screenAreaImagePath);
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // 检测结果绘制层
                            Repeater {
                                id: detectionResultsRepeater
                                model: ListModel {
                                    id: detectionResultsModel
                                }
                                
                                delegate: Item {
                                    id: detectionDelegate
                                    
                                    // 计算在图像上的实际位置和大小
                                    property real imageDisplayWidth: screenAreaImage.paintedWidth
                                    property real imageDisplayHeight: screenAreaImage.paintedHeight
                                    property real imageDisplayX: screenAreaImage.x + (screenAreaImage.width - imageDisplayWidth) / 2
                                    property real imageDisplayY: screenAreaImage.y + (screenAreaImage.height - imageDisplayHeight) / 2
                                    
                                    // 计算检测框的缩放比例和位置
                                    property real scaleX: imageDisplayWidth / model.originalImageWidth
                                    property real scaleY: imageDisplayHeight / model.originalImageHeight
                                    
                                    x: imageDisplayX + (model.relativeX * imageDisplayWidth)
                                    y: imageDisplayY + (model.relativeY * imageDisplayHeight)
                                    width: model.relativeWidth * imageDisplayWidth
                                    height: model.relativeHeight * imageDisplayHeight
                                    
                                    visible: screenAreaImage.visible && imageDisplayWidth > 0 && imageDisplayHeight > 0
                                    
                                    // 检测框
                                    Rectangle {
                                        anchors.fill: parent
                                        color: "transparent"
                                        border.color: model.borderColor || "#FF0000"
                                        border.width: 2
                                        radius: 0
                                        
                                        // 闪烁动画
                                        SequentialAnimation on border.color {
                                            running: parent.visible
                                            loops: Animation.Infinite
                                            ColorAnimation { 
                                                to: model.borderColor || "#FF0000"
                                                duration: 800
                                            }
                                            ColorAnimation { 
                                                to: Qt.lighter(model.borderColor || "#FF0000", 1.5)
                                                duration: 800
                                            }
                                        }
                                    }
                                    
                                    // 类别和置信度标签
                                    Rectangle {
                                        id: labelBackground
                                        width: labelText.implicitWidth + 12
                                        height: labelText.implicitHeight + 8
                                        color: model.borderColor || "#FF0000"
                                        radius: 3
                                        
                                        // 智能定位标签
                                        x: 0
                                        y: {
                                            let labelHeight = height + 2;
                                            if (parent.y >= labelHeight) {
                                                return -labelHeight;  // 显示在框上方
                                            } else {
                                                return 2;  // 显示在框内上方
                                            }
                                        }

                                        Text {
                                            id: labelText
                                            text: `${model.className || "object"}: ${(model.confidence * 100).toFixed(1)}%`
                                            color: "white"
                                            font.pixelSize: 12
                                            font.bold: true
                                            anchors.centerIn: parent
                                        }
                                    }
                                    
                                    // 中心点标记
                                    Rectangle {
                                        width: 6
                                        height: 6
                                        color: model.borderColor || "#FF0000"
                                        radius: 3
                                        anchors.centerIn: parent
                                        opacity: 0.8
                                    }
                                }
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

    function addLog(message, type) {
        // 通过全局信号发送日志到控制窗口
        controller.addLog(message, type || "info");
    }

    function showScreenMatchOverlay(x, y, width, height, confidence, title) {
        // 先清除所有现有的检测结果
        clearDetectionResults();
        
        // 在显示窗口内显示单个匹配结果
        if (controller.screenAreaImagePath && detectionResultsModel) {
            // 获取原始图像尺寸（从控制器）
            let originalWidth = controller.selectedWindowRect ? controller.selectedWindowRect.width : 1920;
            let originalHeight = controller.selectedWindowRect ? controller.selectedWindowRect.height : 1080;
            
            detectionResultsModel.append({
                "relativeX": x / originalWidth,
                "relativeY": y / originalHeight,
                "relativeWidth": width / originalWidth,
                "relativeHeight": height / originalHeight,
                "confidence": confidence,
                "className": title || "匹配结果",
                "borderColor": getClassColor(0),  // 单个匹配结果使用默认颜色
                "originalImageWidth": originalWidth,
                "originalImageHeight": originalHeight
            });
            
            addLog(`显示匹配结果: ${title}`, "success");
        }
    }

    function showMultipleDetections(detectionsJson) {
        // 先清除所有现有的检测结果
        clearDetectionResults();

        try {
            var detections = JSON.parse(detectionsJson);
            
            // 实时检测时不显示日志消息，避免日志刷屏
            if (!controller.realtimeDetectionActive) {
                addLog(`显示 ${detections.length} 个检测结果`, "success");
            }

            if (controller.screenAreaImagePath && detectionResultsModel) {
                // 获取原始图像尺寸
                let originalWidth = controller.selectedWindowRect ? controller.selectedWindowRect.width : 1920;
                let originalHeight = controller.selectedWindowRect ? controller.selectedWindowRect.height : 1080;
                
                // 显示所有检测结果
                for (var i = 0; i < detections.length; i++) {
                    var detection = detections[i];
                    var className = detection.class_name || "object";
                    if (className.startsWith("class_")) {
                        className = className.substring(6);
                    }
                    
                    detectionResultsModel.append({
                        "relativeX": detection.relative_x || 0,
                        "relativeY": detection.relative_y || 0,
                        "relativeWidth": detection.relative_width || 0.1,
                        "relativeHeight": detection.relative_height || 0.1,
                        "confidence": detection.confidence || 0,
                        "className": className,
                        "borderColor": detection.border_color || getClassColor(detection.class_id || 0),  // 优先使用后端动态颜色
                        "originalImageWidth": originalWidth,
                        "originalImageHeight": originalHeight
                    });
                    
                    if (!controller.realtimeDetectionActive) {
                        addLog(`显示检测结果 ${i+1}: ${className} (${(detection.confidence * 100).toFixed(1)}%)`, "success");
                    }
                }
            }
        } catch (e) {
            addLog(`解析检测结果失败: ${e}`, "error");
        }
    }

    function clearDetectionResults() {
        // 清除显示窗口内的检测结果
        if (detectionResultsModel) {
            detectionResultsModel.clear();
        }
    }
    
    function closeMultipleDetectionOverlays() {
        // 兼容性函数 - 现在使用显示窗口内绘制，所以直接清除结果
        clearDetectionResults();
    }
    
    function clearAllDetections() {
        // 清理所有检测结果
        clearDetectionResults();
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
        
        function onClearAllDetections() {
            clearAllDetections();
        }

        function onScreenAreaImageChanged(imagePath) {
            // 强制刷新图像显示
            if (screenAreaImage) {
                screenAreaImage.source = "";
                screenAreaImage.source = imagePath ? "file:///" + imagePath : "";
            }
        }

        function onPerformanceInfoUpdated(fps, latency, device) {
            console.log("QML接收到性能信息:", fps, latency, device);
            updatePerformanceInfo(fps, latency, device);
        }
    }

    // 状态栏
    Rectangle {
        id: statusBar
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 40
        color: "#2E2E2E"
        border.color: "#404040"
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 20

            // 左侧：区域和图像信息
            Text {
                text: {
                    if (!controller.selectedWindow) return "未选择区域"
                    if (!controller.screenAreaImagePath) return `已选择: ${controller.selectedWindow}`
                    
                    // 直接使用selectedWindow，避免重复显示尺寸信息
                    return `实时显示: ${controller.selectedWindow}`
                }
                color: "#CCCCCC"
                font.pixelSize: 11
                elide: Text.ElideMiddle
                Layout.maximumWidth: 400  // 限制最大宽度避免过长
            }

            // 中间弹簧
            Item {
                Layout.fillWidth: true
            }

            // 右侧：性能信息
            RowLayout {
                spacing: 15
                
                // 设备信息
                Text {
                    text: `设备: ${deviceInfo}`
                    color: deviceInfo.includes("CUDA") || deviceInfo.includes("GPU") ? "#4CAF50" : "#FFC107"
                    font.pixelSize: 11
                    font.bold: true
                }

                // FPS
                Text {
                    text: `FPS: ${currentFPS.toFixed(1)}`
                    color: currentFPS > 20 ? "#4CAF50" : currentFPS > 10 ? "#FFC107" : "#F44336"
                    font.pixelSize: 11
                    font.bold: true
                }

                // 延迟
                Text {
                    text: `延迟: ${currentLatency.toFixed(1)}ms`
                    color: currentLatency < 50 ? "#4CAF50" : currentLatency < 100 ? "#FFC107" : "#F44336"
                    font.pixelSize: 11
                    font.bold: true
                }
            }
        }
    }

    // 更新状态栏信息的函数
    function updatePerformanceInfo(fps, latency, device) {
        console.log("更新性能信息:", fps, latency, device);
        currentFPS = fps || 0.0;
        currentLatency = latency || 0.0;
        deviceInfo = device || "CPU";
        console.log("更新后的值:", currentFPS, currentLatency, deviceInfo);
    }
}
