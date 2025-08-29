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
    signal areaSelected(rect areaRect)
    signal selectionCancelled()
    
    // 属性定义
    property bool isSelecting: false
    
    // 区域选择相关属性
    property bool isDrawingArea: false
    property point areaStartPoint: Qt.point(0, 0)
    property point areaEndPoint: Qt.point(0, 0)
    property rect currentAreaRect: Qt.rect(0, 0, 0, 0)
    
    // 半透明遮罩
    Rectangle {
        anchors.fill: parent
        color: "#30000000"
        
        // 十字准线
        Rectangle {
            id: crosshairV
            width: 1
            height: parent.height
            color: "#FF0000"
            x: mouseArea.mouseX
            visible: mouseArea.containsMouse
        }
        
        Rectangle {
            id: crosshairH
            width: parent.width
            height: 1
            color: "#FF0000"
            y: mouseArea.mouseY
            visible: mouseArea.containsMouse
        }
        

        
        // 区域选择框
        Rectangle {
            id: areaHighlight
            x: currentAreaRect.x
            y: currentAreaRect.y
            width: currentAreaRect.width
            height: currentAreaRect.height
            color: "#40FF0000"
            border.color: "#FF0000"
            border.width: 2
            radius: 0
            visible: isDrawingArea && currentAreaRect.width > 0 && currentAreaRect.height > 0
            
            // 闪烁动画
            SequentialAnimation on border.color {
                running: areaHighlight.visible
                loops: Animation.Infinite
                ColorAnimation { 
                    to: "#FF0000"
                    duration: 400
                }
                ColorAnimation { 
                    to: "#FF6666"
                    duration: 400
                }
            }
        }
            
            // 区域信息面板
        Rectangle {
            id: infoPanel
            width: Math.max(200, infoText.implicitWidth + 20)
            height: infoText.implicitHeight + 20
            color: "#E0000000"
            border.color: "#FF0000"
            border.width: 1
            radius: 5
            visible: isDrawingArea
            
            // 跟随鼠标位置显示
            x: Math.min(mouseArea.mouseX + 20, parent.width - width - 10)
            y: Math.min(mouseArea.mouseY + 20, parent.height - height - 10)
            
            Text {
                id: infoText
                anchors.fill: parent
                anchors.margins: 10
                color: "#FFFFFF"
                font.pixelSize: 12
                font.family: "Microsoft YaHei"
                wrapMode: Text.WordWrap
                
                text: {
                    if (isDrawingArea) {
                        var info = "🎯 正在选择区域\n"
                        info += "📐 " + currentAreaRect.width.toFixed(1) + " × " + currentAreaRect.height.toFixed(1) + "\n"
                        info += "📍 (" + currentAreaRect.x.toFixed(1) + ", " + currentAreaRect.y.toFixed(1) + ")"
                        return info
                    } else {
                        return ""
                    }
                }
            }
        }
        
        // 鼠标区域
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.CrossCursor
            acceptedButtons: Qt.RightButton
            
            property int mouseX: 0
            property int mouseY: 0
            
            onPositionChanged: function(mouse) {
                mouseX = mouse.x
                mouseY = mouse.y
                
                if (isDrawingArea) {
                    // 更新区域选择框
                    areaEndPoint = Qt.point(mouse.x, mouse.y)
                    updateAreaRect()
                }
            }
            
            onPressed: function(mouse) {
                if (mouse.button === Qt.RightButton) {
                    // 右键开始画区域
                    isDrawingArea = true
                    areaStartPoint = Qt.point(mouse.x, mouse.y)
                    areaEndPoint = Qt.point(mouse.x, mouse.y)
                    updateAreaRect()
                }
            }
            
            onReleased: function(mouse) {
                if (mouse.button === Qt.RightButton && isDrawingArea) {
                    // 右键完成区域选择
                    console.log("右键释放，当前区域:", currentAreaRect)
                    if (currentAreaRect.width > 10 && currentAreaRect.height > 10) {
                        areaSelected(currentAreaRect)
                        overlay.close()
                    } else {
                        // 区域太小，取消选择
                        console.log("区域太小，取消选择")
                        isDrawingArea = false
                        currentAreaRect = Qt.rect(0, 0, 0, 0)
                    }
                }
            }
            
            onCanceled: {
                selectionCancelled()
                overlay.close()
            }
        }
    }
    
    // 键盘事件处理器
    Item {
        id: keyHandler
        focus: true
        anchors.fill: parent
        
        Keys.onEscapePressed: {
            selectionCancelled()
            overlay.close()
        }
        

    }
    
    // 帮助提示
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 50
        width: helpText.implicitWidth + 30
        height: helpText.implicitHeight + 20
        color: "#D0000000"
        border.color: "#FFFFFF"
        border.width: 1
        radius: 10
        
        Text {
            id: helpText
            anchors.centerIn: parent
            color: "#FFFFFF"
            font.pixelSize: 14
            font.family: "Microsoft YaHei"
            text: isDrawingArea ? 
                  "🖱️ 拖动右键画选择区域，松开完成选择" : 
                  "💡 右键拖动画选择区域，ESC取消"
        }
    }
    
    Component.onCompleted: {
        // 设置窗口为全屏并获取焦点
        showFullScreen()
        keyHandler.forceActiveFocus()
    }
    

    
    // 更新区域选择框的函数
    function updateAreaRect() {
        var x = Math.min(areaStartPoint.x, areaEndPoint.x)
        var y = Math.min(areaStartPoint.y, areaEndPoint.y)
        var width = Math.abs(areaEndPoint.x - areaStartPoint.x)
        var height = Math.abs(areaEndPoint.y - areaStartPoint.y)
        
        // QML返回逻辑坐标，物理坐标转换由Python端处理
        // 保留一位小数
        x = Math.round(x * 10) / 10
        y = Math.round(y * 10) / 10
        width = Math.round(width * 10) / 10
        height = Math.round(height * 10) / 10
        
        currentAreaRect = Qt.rect(x, y, width, height)
    }
}