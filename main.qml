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
            controlWindow.show()
        }
        
        // 创建显示窗口
        var displayComponent = Qt.createComponent("DisplayWindow.qml")
        if (displayComponent.status === Component.Ready) {
            displayWindow = displayComponent.createObject(null, {
                x: 600,
                y: 100
            })
            displayWindow.show()
        }
    }
}
