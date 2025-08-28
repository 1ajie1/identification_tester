import QtQuick 2.15
import QtQuick.Controls 2.15

QtObject {
    id: root
    
    property var controlWindow
    property var displayWindow
    
    Component.onCompleted: {
        // 创建控制窗口
        var controlComponent = Qt.createComponent("ControlWindow.qml")
        if (controlComponent.status === Component.Ready) {
            controlWindow = controlComponent.createObject(null, {
                x: 100,
                y: 100
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
        var displayComponent = Qt.createComponent("DisplayWindow.qml")
        if (displayComponent.status === Component.Ready) {
            displayWindow = displayComponent.createObject(null, {
                x: 600,
                y: 100
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
}
