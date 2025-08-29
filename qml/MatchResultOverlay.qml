import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: resultOverlay
    width: 400
    height: 300
    flags: Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
    color: "transparent"

    // 属性定义
    property string matchResultImagePath: ""
    property string matchTitle: ""
    property real matchConfidence: 0.0
    property int matchX: 0
    property int matchY: 0
    property int matchWidth: 100
    property int matchHeight: 100
    property bool showBoundingBox: true
    property bool autoClose: false
    property int autoCloseDelay: 5000
    property int classId: 0  // 类别ID，用于颜色选择

    // 颜色映射函数
    function getClassColor(classId) {
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

    function getClassColorDark(classId) {
        const darkColors = [
            "#CC0000",  // 暗红色
            "#00CC00",  // 暗绿色
            "#0000CC",  // 暗蓝色
            "#CCCC00",  // 暗黄色
            "#CC00CC",  // 暗洋红
            "#00CCCC",  // 暗青色
            "#CC8400",  // 暗橙色
            "#660066",  // 暗紫色
            "#CC9AB8",  // 暗粉色
            "#842222"   // 暗棕色
        ];
        return darkColors[classId % darkColors.length];
    }

    // 信号定义
    signal overlayClicked
    signal overlayClosed

    // 主容器
    Rectangle {
        anchors.fill: parent
        color: "transparent"

        // YOLO风格的检测框和标签
        Item {
            id: detectionItem
            x: matchX
            y: matchY
            width: matchWidth
            height: matchHeight
            visible: showBoundingBox

            // 检测框
            Rectangle {
                id: boundingBox
                anchors.fill: parent
                color: "transparent"
                border.color: getClassColor(classId)
                border.width: 2
                visible: showBoundingBox
            }

            // 类别和置信度标签（显示在框的上方）
            Rectangle {
                id: labelBackground
                width: labelText.implicitWidth + 12
                height: labelText.implicitHeight + 8
                color: getClassColor(classId)
                radius: 3
                
                // 智能定位：优先显示在框的上方，空间不足时显示在框内上方
                x: 0
                y: {
                    let labelHeight = height + 2;
                    // 检查上方是否有足够空间
                    if (detectionItem.y >= labelHeight) {
                        return -labelHeight;  // 显示在框上方
                    } else {
                        return 2;  // 显示在框内上方
                    }
                }

                Text {
                    id: labelText
                    text: {
                        // 解析类别名称，去掉可能的"class_"前缀
                        let className = matchTitle || "object";
                        if (className.startsWith("class_")) {
                            className = className.substring(6);
                        }
                        return `${className}: ${(matchConfidence * 100).toFixed(1)}%`;
                    }
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    anchors.centerIn: parent
                }
            }

            // 中心点标记（可选）
            Rectangle {
                width: 6
                height: 6
                color: getClassColor(classId)
                radius: 3
                anchors.centerIn: parent
                opacity: 0.8
            }
        }

        // 简化的控制按钮（右上角）
        Row {
            id: controlButtons
            spacing: 5
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 10

            Button {
                text: "详情"
                font.pixelSize: 10
                implicitHeight: 25
                implicitWidth: 40
                background: Rectangle {
                    color: "#AA000000"
                    radius: 3
                    border.color: "#666666"
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: {
                    overlayClicked();
                }
            }

            Button {
                text: "×"
                font.pixelSize: 14
                font.bold: true
                implicitHeight: 25
                implicitWidth: 25
                background: Rectangle {
                    color: "#AAFF0000"
                    radius: 3
                    border.color: "#FF6666"
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: {
                    resultOverlay.close();
                }
            }
        }

        // 点击区域 - 只在检测框区域内响应
        MouseArea {
            x: detectionItem.x
            y: detectionItem.y
            width: detectionItem.width
            height: detectionItem.height
            onClicked: {
                overlayClicked();
            }
        }
    }

    // 自动关闭定时器
    Timer {
        id: autoCloseTimer
        interval: autoCloseDelay
        running: autoClose && resultOverlay.visible
        onTriggered: {
            resultOverlay.close();
        }
    }

    // 淡入动画
    PropertyAnimation {
        id: fadeInAnimation
        target: resultOverlay
        property: "opacity"
        from: 0
        to: 1
        duration: 300
        running: false
    }

    // 淡出动画
    PropertyAnimation {
        id: fadeOutAnimation
        target: resultOverlay
        property: "opacity"
        from: 1
        to: 0
        duration: 300
        onFinished: {
            resultOverlay.hide();
        }
    }

    // 组件加载完成时的初始化
    Component.onCompleted: {
        // 设置初始透明度
        opacity = 0;
        show();
        fadeInAnimation.start();
    }

    // 关闭事件处理
    onClosing: {
        overlayClosed();
    }

    // 公共方法
    function showMatchResult(x, y, width, height, confidence, title, classIdValue) {
        matchX = 0;  // 相对于窗口的坐标
        matchY = 0;
        matchWidth = width;
        matchHeight = height;
        matchConfidence = confidence;
        matchTitle = title || "匹配结果";
        classId = classIdValue || 0;

        // 计算窗口大小 - 只包含检测区域和控制按钮
        let padding = 60;  // 给控制按钮留出空间
        let windowWidth = width + padding;
        let windowHeight = height + padding;

        // 确保窗口不会太小
        windowWidth = Math.max(windowWidth, 150);
        windowHeight = Math.max(windowHeight, 80);

        // 设置窗口位置和大小
        resultOverlay.x = x - padding / 2;
        resultOverlay.y = y - padding / 2;
        resultOverlay.width = windowWidth;
        resultOverlay.height = windowHeight;

        // 确保窗口不超出屏幕边界
        if (resultOverlay.x < 0) {
            matchX = -resultOverlay.x;
            resultOverlay.x = 0;
        }
        if (resultOverlay.y < 0) {
            matchY = -resultOverlay.y;
            resultOverlay.y = 0;
        }
        if (resultOverlay.x + resultOverlay.width > Screen.width) {
            resultOverlay.x = Screen.width - resultOverlay.width;
            matchX = x - resultOverlay.x;
        }
        if (resultOverlay.y + resultOverlay.height > Screen.height) {
            resultOverlay.y = Screen.height - resultOverlay.height;
            matchY = y - resultOverlay.y;
        }

        if (!visible) {
            opacity = 0;
            show();
            fadeInAnimation.start();
        }
    }

    function closeWithAnimation() {
        fadeOutAnimation.start();
    }
}
