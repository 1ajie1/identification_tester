import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

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
    
    // 按钮组管理
    ButtonGroup {
        id: inputModeGroup
        buttons: [imageMode, windowMode]
    }
    
    // 日志数据模型
    ListModel {
        id: logListModel
        
        Component.onCompleted: {
            addLog("系统初始化完成", "info")
            addLog("等待用户操作...", "info")
        }
        
        // 监听模型变化，确保滚动到底部
        onRowsInserted: {
            Qt.callLater(function() {
                if (logListView) {
                    logListView.positionViewAtEnd()
                }
            })
        }
    }
    
    // 添加日志的函数
    function addLog(message, type) {
        type = type || "info"
        var now = new Date()
        var timestamp = Qt.formatTime(now, "hh:mm:ss")
        
        logListModel.append({
            "timestamp": timestamp,
            "message": message,
            "type": type
        })
        
        // 限制日志条目数量（最多100条）
        if (logListModel.count > 100) {
            logListModel.remove(0)
        }
        
        // 延迟自动滚动到底部，确保内容已渲染
        Qt.callLater(function() {
            logListView.positionViewAtEnd()
        })
    }
    
    // 监听控制器信号，记录操作日志
    Connections {
        target: controller
        
        function onModeChanged(mode) {
            var modeText = mode === 0 ? "双图片匹配" : "屏幕窗口匹配"
            addLog("切换到" + modeText + "模式", "info")
        }
        
        function onAlgorithmModeChanged(mode) {
            var algorithmNames = ["模板匹配", "ORB特征匹配", "YOLO+ORB混合"]
            addLog("选择算法: " + algorithmNames[mode], "info")
        }
        
        function onNeedleImage(path) {
            var filename = path.split('/').pop() || path.split('\\').pop()
        }
        
        function onHaystackImage(path) {
            var filename = path.split('/').pop() || path.split('\\').pop()
        }
        
        function onWindowSelected(windowTitle) {
            addLog("选择窗口: " + windowTitle, "success")
        }
        
        function onLogAdded(message, type) {
            addLog(message, type)
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15
        
        // 输入模式标题
        Text {
            text: "输入模式"
            font.pixelSize: 18
            font.bold: true
            color: textColor
        }
        
        // 输入模式按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Button {
                id: imageMode
                Layout.fillWidth: true
                height: 50
                text: "双图片匹配"
                font.pixelSize: 14
                checkable: true
                checked: controller.currentMode === 0
                ButtonGroup.group: inputModeGroup
                
                onClicked: controller.switchMode(0)
            }
            
            Button {
                id: windowMode
                Layout.fillWidth: true
                height: 50
                text: "屏幕窗口匹配"
                font.pixelSize: 14
                checkable: true
                checked: controller.currentMode === 1
                ButtonGroup.group: inputModeGroup
                
                onClicked: controller.switchMode(1)
            }
        }
        
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
                
                model: [
                    "🎯 模板匹配",
                    "🔍 ORB 特征匹配", 
                    "🚀 YOLO + ORB"
                ]
                
                currentIndex: controller.algorithmMode
                
                onCurrentIndexChanged: {
                    if (currentIndex !== controller.algorithmMode) {
                        controller.switchAlgorithmMode(currentIndex)
                    }
                }
                
                // 监听控制器变化来同步下拉框
                Connections {
                    target: controller
                    function onAlgorithmModeChanged(mode) {
                        if (algorithmComboBox.currentIndex !== mode) {
                            algorithmComboBox.currentIndex = mode
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
                    settingsDialog.open()
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
            
            enabled: (controller.currentMode === 0 && controller.image1Path && controller.image2Path) ||
                    (controller.currentMode === 1 && controller.selectedWindow)
            
            onClicked: {
                var algorithmNames = ["模板匹配", "ORB特征匹配", "YOLO+ORB混合"]
                addLog("开始执行匹配 - 算法: " + algorithmNames[controller.algorithmMode], "info")
                controller.startMatching()
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
            
            Rectangle{
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
                        Qt.callLater(function() {
                            positionViewAtEnd()
                        })
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
                            switch(type) {
                                case "error": return "#FFEBEE"
                                case "warning": return "#FFF8E1" 
                                case "success": return "#E8F5E8"
                                default: return "transparent"
                            }
                        }
                        radius: 6
                        border.color: {
                            switch(type) {
                                case "error": return "#FFCDD2"
                                case "warning": return "#FFE0B2"
                                case "success": return "#C8E6C9"
                                default: return "transparent"
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
                                    switch(type) {
                                        case "error": return "❌"
                                        case "warning": return "⚠️"
                                        case "success": return "✅"
                                        default: return "ℹ️"
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
                                        switch(type) {
                                            case "error": return "#D32F2F"
                                            case "warning": return "#F57C00"
                                            case "success": return "#388E3C"
                                            default: return "#424242"
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
            if (width < minimumWidth) width = minimumWidth
        }
        
        onHeightChanged: {
            if (height < minimumHeight) height = minimumHeight
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
                        applySettings()
                        settingsDialog.close()
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
        templateMethodCombo.currentIndex = 0
        templateThresholdSlider.value = 0.8
        
        // ORB默认值
        orbFeaturesSpinBox.value = 1000
        orbDistanceSlider.value = 0.75
        orbMinMatchesSpinBox.value = 10
        
        // YOLO+ORB默认值
        yoloConfidenceSlider.value = 0.5
        nmsThresholdSlider.value = 0.4
        yoloOrbFeaturesSpinBox.value = 500
        
        addLog("参数已重置为默认值", "info")
    }
    
    // 应用设置的函数
    function applySettings() {
        var settings = {}
        
        switch(algorithmComboBox.currentIndex) {
            case 0: // 模板匹配
                settings = {
                    method: templateMethodCombo.currentText,
                    threshold: templateThresholdSlider.value
                }
                break
            case 1: // ORB
                settings = {
                    nfeatures: orbFeaturesSpinBox.value,
                    distance_threshold: orbDistanceSlider.value,
                    min_matches: orbMinMatchesSpinBox.value
                }
                break
            case 2: // YOLO+ORB
                settings = {
                    yolo_confidence: yoloConfidenceSlider.value,
                    nms_threshold: nmsThresholdSlider.value,
                    orb_nfeatures: yoloOrbFeaturesSpinBox.value
                }
                break
        }
        
        // 调用控制器保存设置
        controller.updateAlgorithmSettings(algorithmComboBox.currentIndex, JSON.stringify(settings))
        
        var algorithmNames = ["模板匹配", "ORB特征匹配", "YOLO+ORB混合"]
        addLog("已更新 " + algorithmNames[algorithmComboBox.currentIndex] + " 参数设置", "success")
    }
}
