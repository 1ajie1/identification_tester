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

    // 信号定义
    signal overlayClicked
    signal overlayClosed

    // 主容器
    Rectangle {
        anchors.fill: parent
        color: "transparent"

        // 匹配边界框
        Rectangle {
            id: boundingBox
            x: matchX
            y: matchY
            width: matchWidth
            height: matchHeight
            color: "transparent"
            border.color: "#FF0000"
            border.width: 3
            radius: 4
            visible: showBoundingBox

            // 动画效果
            SequentialAnimation on border.color {
                running: visible
                loops: Animation.Infinite
                ColorAnimation {
                    to: "#FF0000"
                    duration: 1000
                }
                ColorAnimation {
                    to: "#FF6666"
                    duration: 1000
                }
            }

            // 中心点标记
            Rectangle {
                width: 10
                height: 10
                color: "#FF0000"
                radius: 5
                anchors.centerIn: parent

                SequentialAnimation on opacity {
                    running: boundingBox.visible
                    loops: Animation.Infinite
                    NumberAnimation {
                        to: 0.3
                        duration: 800
                    }
                    NumberAnimation {
                        to: 1.0
                        duration: 800
                    }
                }
            }
        }

        // 信息面板
        Rectangle {
            id: infoPanel
            width: Math.max(200, infoText.implicitWidth + 40)
            height: infoColumn.height + 20
            color: "#CC000000"
            radius: 8
            border.color: "#555555"
            border.width: 1

            // 定位在匹配框旁边
            x: {
                let targetX = matchX + matchWidth + 10;
                if (targetX + width > resultOverlay.width) {
                    targetX = matchX - width - 10;
                }
                return Math.max(10, Math.min(targetX, resultOverlay.width - width - 10));
            }

            y: {
                let targetY = matchY;
                return Math.max(10, Math.min(targetY, resultOverlay.height - height - 10));
            }

            Column {
                id: infoColumn
                anchors.centerIn: parent
                spacing: 8

                Text {
                    id: titleText
                    text: matchTitle || "匹配结果"
                    color: "#FFFFFF"
                    font.pixelSize: 14
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Text {
                    id: infoText
                    text: `置信度: ${(matchConfidence * 100).toFixed(1)}%\n位置: (${matchX}, ${matchY})\n尺寸: ${matchWidth}×${matchHeight}`
                    color: "#CCCCCC"
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignLeft
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10

                    Button {
                        text: "详情"
                        font.pixelSize: 10
                        implicitHeight: 25
                        implicitWidth: 50
                        onClicked: {
                            overlayClicked();
                        }
                    }

                    Button {
                        text: "关闭"
                        font.pixelSize: 10
                        implicitHeight: 25
                        implicitWidth: 50
                        onClicked: {
                            resultOverlay.close();
                        }
                    }
                }
            }
        }

        // 点击区域
        MouseArea {
            anchors.fill: parent
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
    function showMatchResult(x, y, width, height, confidence, title) {
        matchX = x;
        matchY = y;
        matchWidth = width;
        matchHeight = height;
        matchConfidence = confidence;
        matchTitle = title || "匹配结果";

        // 调整窗口位置和大小以包含匹配区域
        let minX = Math.min(x - 50, 0);
        let minY = Math.min(y - 50, 0);
        let maxX = Math.max(x + width + 300, Screen.width);
        let maxY = Math.max(y + height + 100, Screen.height);

        resultOverlay.x = minX;
        resultOverlay.y = minY;
        resultOverlay.width = maxX - minX;
        resultOverlay.height = maxY - minY;

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
