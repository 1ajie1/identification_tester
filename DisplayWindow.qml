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
                                            console.log("加载图片1失败: " + controller.image1Path)
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
                                        text: "请选择第一张图片"
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
                            text: controller.image1Path ? 
                                  controller.image1Path.split('/').pop() || controller.image1Path.split('\\').pop() : 
                                  "未选择文件"
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
                                            console.log("加载图片2失败: " + controller.image2Path)
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
                                        text: "请选择第二张图片"
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
                            text: controller.image2Path ? 
                                  controller.image2Path.split('/').pop() || controller.image2Path.split('\\').pop() : 
                                  "未选择文件"
                            font.pixelSize: 12
                            color: "#666666"
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }
            }
            
            // 屏幕窗口模式显示 - 只保留核心功能
            Item {
                Column {
                    anchors.centerIn: parent
                    spacing: 20
                    
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
                        text: controller.selectedWindow ? 
                              "已选择窗口: " + controller.selectedWindow : 
                              "请选择窗口"
                        font.pixelSize: 16
                        color: "#666666"
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    
                    Button {
                        id: windowSelectorButton
                        text: windowSelector.isSelecting ? "拖拽选择窗口中..." : "🎯 拖拽选择窗口"
                        anchors.horizontalCenter: parent.horizontalCenter
                        enabled: !windowSelector.isSelecting
                        
                        onPressed: {
                            windowSelector.startSelection()
                        }
                    }
                    
                    Text {
                        text: "按住按钮并拖拽到目标窗口上松开鼠标"
                        font.pixelSize: 12
                        color: "#999999"
                        anchors.horizontalCenter: parent.horizontalCenter
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
            var filePath = selectedFile.toString().replace("file:///", "")
            addLog("用户选择图片1: " + (filePath.split('/').pop() || filePath.split('\\').pop()), "info")
            controller.selectImage1(filePath)
        }
        onRejected: {
            addLog("图片1选择已取消", "warning")
        }
    }
    
    FileDialog {
        id: fileDialog2
        title: "选择第二张图片"
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)", "所有文件 (*)"]
        onAccepted: {
            var filePath = selectedFile.toString().replace("file:///", "")
            addLog("用户选择图片2: " + (filePath.split('/').pop() || filePath.split('\\').pop()), "info")
            controller.selectImage2(filePath)
        }
        onRejected: {
            addLog("图片2选择已取消", "warning")
        }
    }
    
    // 窗口选择器组件
    Item {
        id: windowSelector
        property bool isSelecting: false
        
        function startSelection() {
            isSelecting = true
            addLog("启动窗口选择器", "info")
            // 创建全屏透明窗口用于拖拽选择
            var component = Qt.createComponent("WindowSelectorOverlay.qml")
            if (component.status === Component.Ready) {
                var overlay = component.createObject(displayWindow, {
                    "onWindowSelected": function(windowTitle) {
                        controller.selectWindow(windowTitle)
                        windowSelector.isSelecting = false
                        addLog("窗口选择器关闭", "info")
                    },
                    "onSelectionCancelled": function() {
                        windowSelector.isSelecting = false
                        addLog("窗口选择已取消", "warning")
                    }
                })
                overlay.show()
            } else {
                // 如果没有overlay组件，使用简单的模拟选择
                addLog("使用模拟窗口选择", "warning")
                windowSelector.simulateWindowSelection()
            }
        }
        
        function simulateWindowSelection() {
            // 模拟窗口选择过程
            var timer = Qt.createQmlObject("
                import QtQuick 2.15;
                Timer {
                    interval: 2000;
                    running: true;
                    repeat: false;
                    onTriggered: {
                        controller.selectWindow('模拟选择的窗口');
                        windowSelector.isSelecting = false;
                        destroy();
                    }
                }", windowSelector, "SimulationTimer")
        }
    }
    
    // 添加日志输出功能
    property var logFunction: null
    
    function addLog(message, type) {
        // 通过全局信号发送日志到控制窗口
        controller.addLog(message, type || "info")
    }
    
    // 监听控制器信号，更新显示
    Connections {
        target: controller
        
        function onModeChanged(mode) {
            displayStack.currentIndex = mode
            var modeText = mode === 0 ? "双图片匹配" : "屏幕窗口匹配"
            addLog("显示窗口切换到" + modeText + "模式", "info")
        }
        
        function onImage1Selected(path) {
            var filename = path.split('/').pop() || path.split('\\').pop()
            addLog("图片1加载完成: " + filename, "success")
        }
        
        function onImage2Selected(path) {
            var filename = path.split('/').pop() || path.split('\\').pop()
            addLog("图片2加载完成: " + filename, "success")
        }
        
        function onWindowSelected(windowTitle) {
            addLog("屏幕窗口选择完成: " + windowTitle, "success")
        }
    }
}