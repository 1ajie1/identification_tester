import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    id: overlay
    width: Screen.width
    height: Screen.height
    x: 0
    y: 0
    flags: Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
    color: "transparent"
    
    // 信号定义
    signal windowSelected(string windowTitle)
    signal selectionCancelled()
    
    property bool isDragging: false
    property point startPos
    
    Rectangle {
        anchors.fill: parent
        color: "#40000000" // 半透明黑色遮罩
        
        // 十字准星光标
        Rectangle {
            id: crosshair
            width: 40
            height: 40
            color: "transparent"
            border.color: "#FF0000"
            border.width: 2
            radius: 20
            visible: mouseArea.containsMouse
            
            x: mouseArea.mouseX - width/2
            y: mouseArea.mouseY - height/2
            
            Rectangle {
                width: 2
                height: parent.height
                color: "#FF0000"
                anchors.centerIn: parent
            }
            
            Rectangle {
                width: parent.width
                height: 2
                color: "#FF0000"
                anchors.centerIn: parent
            }
        }
        
        // 信息显示
        Rectangle {
            id: infoPanel
            width: 300
            height: 80
            color: "#CC000000"
            radius: 8
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.margins: 20
            
            Column {
                anchors.centerIn: parent
                spacing: 8
                
                Text {
                    text: "窗口选择模式"
                    color: "white"
                    font.pixelSize: 16
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                
                Text {
                    text: "拖拽鼠标到目标窗口上松开 | ESC键取消"
                    color: "#CCCCCC"
                    font.pixelSize: 12
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }
        
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.CrossCursor
            
            onPressed: {
                isDragging = true
                startPos = Qt.point(mouse.x, mouse.y)
            }
            
            onReleased: {
                if (isDragging) {
                    // 模拟获取鼠标位置下的窗口
                    var windowTitle = getWindowAtPosition(mouse.x, mouse.y)
                    windowSelected(windowTitle)
                    overlay.close()
                }
            }
            
            onCanceled: {
                selectionCancelled()
                overlay.close()
            }
        }
    }
    
    // 键盘事件处理
    Keys.onEscapePressed: {
        selectionCancelled()
        close()
    }
    
    Component.onCompleted: {
        // 获取焦点以接收键盘事件
        forceActiveFocus()
        // 设置窗口为全屏
        showFullScreen()
    }
    
    // 模拟获取窗口标题的函数
    function getWindowAtPosition(x, y) {
        // 这里应该调用系统API获取鼠标位置的窗口
        // 目前使用模拟数据
        var windows = [
            "记事本", "Chrome浏览器", "文件资源管理器", 
            "Visual Studio Code", "QQ", "微信",
            "计算器", "画图", "设置"
        ]
        
        var index = Math.floor(Math.random() * windows.length)
        return windows[index]
    }
    
    // 添加动画效果
    PropertyAnimation {
        id: fadeIn
        target: overlay
        property: "opacity"
        from: 0
        to: 1
        duration: 200
        running: true
    }
}
