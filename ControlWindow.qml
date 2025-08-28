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
        
        function onImage1Selected(path) {
            var filename = path.split('/').pop() || path.split('\\').pop()
            addLog("选择第一张图片: " + filename, "success")
        }
        
        function onImage2Selected(path) {
            var filename = path.split('/').pop() || path.split('\\').pop()
            addLog("选择第二张图片: " + filename, "success")
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
        
        // 算法选择下拉框
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
}
