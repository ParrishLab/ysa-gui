from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor, QFont

from helpers.Constants import green, yellow, red

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
            # Bottom left if you want
            # x = screen_geometry.x() + 10
            # y = screen_geometry.height() - NOTIFICATION_HEIGHT + 50
            # Top right:
            x = screen_geometry.right() - WIDTH - 3
            y = screen_geometry.top() + (NOTIFICATION_HEIGHT // 2)
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

    def __init__(self, parent=None, title="", message="", bg=None, timeout=TIMEOUT):
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

        self.initUI(title, message)
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.finished.connect(self.on_animation_finished)

    def initUI(self, title, message):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(8)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(8)

        # Status icon
        status_icon = self.get_status_icon()
        header_layout.addWidget(status_icon)

        # Title
        title_label = QtWidgets.QLabel(title or self.get_default_title())
        title_label.setFont(QFont(FONT_FAMILY, 14, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Close button
        close_button = QtWidgets.QPushButton("×")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.close)
        close_button.setCursor(QtCore.Qt.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.8);
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
            }
        """)
        header_layout.addWidget(close_button)

        content_layout.addLayout(header_layout)

        # Message
        self.label = QtWidgets.QLabel(message)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(WIDTH - 48)
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.label.setStyleSheet("""
            font-size: 14px;
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.4;
        """)
        content_layout.addWidget(self.label)

        content_widget.setLayout(content_layout)

        # Enhanced shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 40))
        content_widget.setGraphicsEffect(shadow)

        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.get_bg_color()};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                font-family: {FONT_FAMILY};
            }}
        """)

        layout.addWidget(content_widget)
        self.setLayout(layout)

    def get_status_icon(self):
        icon = QtWidgets.QLabel()
        size = 20
        icon.setFixedSize(size, size)

        if self.bg == 0:  # Success
            icon_char = "✓"
        elif self.bg == 1:  # Warning
            icon_char = "!"
        elif self.bg == 2:  # Error
            icon_char = "×"
        else:
            icon_char = "i"

        icon.setText(icon_char)
        icon.setAlignment(QtCore.Qt.AlignCenter)
        icon.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: {size // 2}px;
            color: white;
            font-size: 14px;
            font-weight: bold;
        """)
        return icon

    def get_default_title(self):
        if self.bg == 0:
            return "Success"
        elif self.bg == 1:
            return "Warning"
        elif self.bg == 2:
            return "Error"
        return "Information"

    def get_bg_color(self):
        if self.bg == 0:
            return f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {green}, stop:1 {self.adjust_color(green, 0.6)})"
        elif self.bg == 1:
            return f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {yellow}, stop:1 {self.adjust_color(yellow, 0.6)})"
        elif self.bg == 2:
            return f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {red}, stop:1 {self.adjust_color(red, 0.6)})"
        return "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2D3748, stop:1 #1A202C)"

    def adjust_color(self, color, factor):
        # Helper function to slightly adjust color brightness for gradient
        color = color.lstrip("#")
        r = min(255, int(int(color[:2], 16) * factor))
        g = min(255, int(int(color[2:4], 16) * factor))
        b = min(255, int(int(color[4:], 16) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

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
    def show_message(cls, parent, message, title="", bg=None, timeout=TIMEOUT):
        notification = cls(parent, title, message, bg, timeout)
        NotificationManager.instance().add_notification(notification)
        return notification
