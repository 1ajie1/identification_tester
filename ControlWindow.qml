import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: controlWindow
    width: 450
    height: 650
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
        
        // 自动滚动到底部
        logListView.positionViewAtEnd()
        
        // 限制日志条目数量（最多100条）
        if (logListModel.count > 100) {
            logListModel.remove(0)
        }
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
    
    Rectangle {
        anchors.fill: parent
        color: backgroundColor
        
        ScrollView {
            anchors.fill: parent
            anchors.margins: 20
            contentWidth: availableWidth
            contentHeight: Math.max(implicitContentHeight, availableHeight)
            
            ColumnLayout {
                width: parent.width
                height: Math.max(implicitHeight, parent.parent.availableHeight)
                spacing: 20
                
                // 输入模式选择区域
                Rectangle {
                    Layout.fillWidth: true
                    height: 120
                    color: cardColor
                    radius: 12
                    border.color: borderColor
                    border.width: 1
                    
                    Column {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15
                        
                        Text {
                            text: "输入模式"
                            font.pixelSize: 18
                            font.bold: true
                            color: textColor
                        }
                        
                        RowLayout {
                            width: parent.width
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
                    }
                }
                
                // 算法模式选择区域
                Rectangle {
                    Layout.fillWidth: true
                    height: 100
                    color: cardColor
                    radius: 12
                    border.color: borderColor
                    border.width: 1
                    
                    Column {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15
                        
                        Text {
                            text: "算法模式"
                            font.pixelSize: 18
                            font.bold: true
                            color: textColor
                        }
                        
                        ComboBox {
                            id: algorithmComboBox
                            width: parent.width
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
                    }
                }
                

                
                // 开始匹配按钮
                Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    text: "开始匹配"
                    font.pixelSize: 16
                    font.bold: true
                    
                    enabled: (controller.currentMode === 0 && controller.image1Path && controller.image2Path) ||
                            (controller.currentMode === 1 && controller.selectedWindow)
                    
                    onClicked: {
                        var algorithmNames = ["模板匹配", "ORB特征匹配", "YOLO+ORB混合"]
                        addLog("开始执行匹配 - 算法: " + algorithmNames[controller.algorithmMode], "info")
                        controller.startMatching()
                    }
                }
                
                // 操作日志区域
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 200
                    color: cardColor
                    radius: 12
                    border.color: borderColor
                    border.width: 1
                    
                    // 添加阴影效果
                    Rectangle {
                        anchors.fill: parent
                        anchors.topMargin: 2
                        anchors.leftMargin: 2
                        color: "#00000010"
                        radius: 12
                        z: -1
                    }
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12
                        
                        // 标题栏
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            
                            // 状态指示器
                            Rectangle {
                                width: 8
                                height: 8
                                color: "#4CAF50"
                                radius: 4
                                
                                // 呼吸灯效果
                                SequentialAnimation on opacity {
                                    running: true
                                    loops: Animation.Infinite
                                    NumberAnimation { to: 0.3; duration: 1000 }
                                    NumberAnimation { to: 1.0; duration: 1000 }
                                }
                            }
                            
                            Text {
                                text: "📋 操作日志"
                                font.pixelSize: 16
                                font.bold: true
                                color: textColor
                            }
                            
                            // 日志数量标签
                            Rectangle {
                                width: countText.width + 16
                                height: 24
                                color: primaryColor
                                radius: 12
                                opacity: 0.1
                                
                                Text {
                                    id: countText
                                    anchors.centerIn: parent
                                    text: logListModel.count + " 条"
                                    font.pixelSize: 11
                                    color: primaryColor
                                    font.bold: true
                                }
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            // 清空按钮
                            Button {
                                text: "🗑️ 清空"
                                height: 32
                                font.pixelSize: 12
                                flat: true
                                
                                background: Rectangle {
                                    color: parent.hovered ? "#FFE0E0" : "transparent"
                                    radius: 6
                                    border.color: parent.hovered ? "#F44336" : borderColor
                                    border.width: 1
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font: parent.font
                                    color: parent.hovered ? "#F44336" : "#666666"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                onClicked: {
                                    logListModel.clear()
                                    addLog("日志已清空", "info")
                                }
                            }
                        }
                        
                        // 日志内容区域
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#FAFBFC"
                            radius: 8
                            border.color: "#E8EAED"
                            border.width: 1
                            
                            ScrollView {
                                anchors.fill: parent
                                anchors.margins: 8
                                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                                clip: true
                                
                                ListView {
                                    id: logListView
                                    model: logListModel
                                    spacing: 4
                                    
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
                                        height: logContent.height + 16
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
            }
        }
    }
    
}
