import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    
    property var controlWindow
    property var displayWindow
    
    Component.onCompleted: {
        // 创建控制窗口
        var controlComponent = Qt.createComponent("qml/ControlWindow.qml")
        if (controlComponent.status === Component.Ready) {
            controlWindow = controlComponent.createObject(null, {
                x: 100,
                y: 100,
                objectName: "controlWindow"
            })
            if (controlWindow) {
                controlWindow.show()
                console.log("控制窗口创建成功")
            } else {
                console.log("控制窗口创建失败")
            }
        } else if (controlComponent.status === Component.Error) {
            console.log("控制窗口加载错误:", controlComponent.errorString())
        } else {
            console.log("控制窗口状态:", controlComponent.status)
        }
        
        // 创建显示窗口
        var displayComponent = Qt.createComponent("qml/DisplayWindow.qml")
        if (displayComponent.status === Component.Ready) {
            displayWindow = displayComponent.createObject(null, {
                x: 600,
                y: 100,
                objectName: "displayWindow"
            })
            if (displayWindow) {
                displayWindow.show()
                console.log("显示窗口创建成功")
            } else {
                console.log("显示窗口创建失败")
            }
        } else if (displayComponent.status === Component.Error) {
            console.log("显示窗口加载错误:", displayComponent.errorString())
        } else {
            console.log("显示窗口状态:", displayComponent.status)
        }
    }
    
    // 连接来自Python的托盘控制信号
    Connections {
        id: trayConnections
        target: controller
        function onShowControlWindowSignal() {
            if (root.controlWindow) {
                root.controlWindow.show()
                root.controlWindow.raise()
                root.controlWindow.requestActivate()
                console.log("显示控制窗口")
            }
        }
        
        function onHideControlWindowSignal() {
            if (root.controlWindow) {
                root.controlWindow.hide()
                console.log("隐藏控制窗口")
            }
        }
        
        function onShowDisplayWindowSignal() {
            if (root.displayWindow) {
                root.displayWindow.show()
                root.displayWindow.raise()
                root.displayWindow.requestActivate()
                console.log("显示显示窗口")
            }
        }
        
        function onHideDisplayWindowSignal() {
            if (root.displayWindow) {
                root.displayWindow.hide()
                console.log("隐藏显示窗口")
            }
        }
    }
}
