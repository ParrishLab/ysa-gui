from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor

from src.helpers.Constants import green, yellow, red

FONT_FAMILY = "Arial"
TIMEOUT = 5000
WIDTH = 600
NOTIFICATION_HEIGHT = 100


class NotificationManager(QtCore.QObject):
    _instance = None

    def __init__(self):
        super().__init__()
        self.notification_queue = []
        self.current_notification = None
        self.position = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_notification(self, notification):
        if not self.position:
            screen = QtWidgets.QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = screen_geometry.x() + 10
            y = screen_geometry.height() - NOTIFICATION_HEIGHT + 30
            self.position = QtCore.QPoint(x, y)

        if not self.current_notification:
            self.show_notification(notification)
        else:
            self.notification_queue.append(notification)

    def show_notification(self, notification):
        self.current_notification = notification
        notification.move(self.position)
        notification.closed.connect(self.handle_notification_closed)
        notification.show()

    def handle_notification_closed(self):
        self.current_notification = None
        if self.notification_queue:
            next_notification = self.notification_queue.pop(0)
            self.show_notification(next_notification)


class NotificationWidget(QtWidgets.QWidget):
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None, message="", bg=None, timeout=TIMEOUT):
        super().__init__(parent)
        self.setFixedHeight(NOTIFICATION_HEIGHT)
        self.setFixedWidth(WIDTH)
        self.setWindowFlags(
            QtCore.Qt.Tool
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        self.setAttribute(QtCore.Qt.WA_Hover)

        self.bg = bg
        self.timeout = timeout
        self.remaining_time = timeout
        self.elapsed_timer = QtCore.QElapsedTimer()
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)

        self.is_hovered = False
        self.is_animating = False

        self.initUI(message)
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.finished.connect(self.on_animation_finished)

    def initUI(self, message):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(12, 12, 12, 12)

        self.label = QtWidgets.QLabel(message)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(WIDTH - 60)
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        close_button = QtWidgets.QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.close)
        close_button.setCursor(QtCore.Qt.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
        """)

        content_layout.addWidget(self.label)
        content_layout.addWidget(close_button)
        content_widget.setLayout(content_layout)

        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 50))
        content_widget.setGraphicsEffect(shadow)

        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.get_bg_color()};
                border-radius: 6px;
            }}
            QLabel {{
                color: white;
                font-family: {FONT_FAMILY};
                font-size: 16px;
                background: transparent;
            }}
        """)

        layout.addWidget(content_widget)
        self.setLayout(layout)

    def get_bg_color(self):
        if self.bg == 0:
            return green
        elif self.bg == 1:
            return yellow
        elif self.bg == 2:
            return red
        return "#333"

    def enterEvent(self, event):
        self.is_hovered = True
        if self.timer.isActive():
            elapsed = self.elapsed_timer.elapsed()
            self.remaining_time = max(0, self.remaining_time - elapsed)
            self.timer.stop()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.check_and_start_timer()

    def check_and_start_timer(self):
        if not self.is_hovered and not self.is_animating and self.remaining_time > 0:
            self.elapsed_timer.restart()
            self.timer.start(self.remaining_time)

    def start_animation(self):
        self.is_animating = True
        self.setWindowOpacity(0)
        self.animation.setDuration(250)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

        self.remaining_time = self.timeout
        self.elapsed_timer.start()

    def close(self):
        self.fade_out()

    def fade_out(self):
        self.remaining_time = 0
        self.is_animating = True
        self.animation.setDuration(250)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.start()

    def on_animation_finished(self):
        self.is_animating = False
        if self.windowOpacity() == 0:
            self.closed.emit()
            super().close()
        else:
            self.check_and_start_timer()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_animation()

    @classmethod
    def show_message(cls, parent, message, bg=None, timeout=TIMEOUT):
        notification = cls(parent, message, bg, timeout)
        NotificationManager.instance().add_notification(notification)
        return notification
