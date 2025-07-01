from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QBrush, QFont, QLinearGradient, QPainter
from PyQt5.QtWidgets import QWidget

from helpers.Constants import ACTIVE, BACKGROUND, SE, SEIZURE


class LegendWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(120)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont("Arial", 10)
        font.setBold(True)
        painter.setFont(font)

        gradient1 = QLinearGradient(0, 0, 0, self.height() // 2)
        gradient1.setColorAt(0.0, Qt.white)
        gradient1.setColorAt(1.0, SEIZURE)

        gradient2 = QLinearGradient(0, 0, 0, self.height() // 2)
        gradient2.setColorAt(0.0, Qt.white)
        gradient2.setColorAt(1.0, SE)

        seizure_bar = QRect(10, 40, 20, self.height() // 2)
        se_bar = QRect(50, 40, 20, self.height() // 2)

        painter.setBrush(QBrush(gradient1))
        painter.setPen(Qt.NoPen)
        painter.drawRect(seizure_bar)

        painter.setBrush(QBrush(gradient2))
        painter.drawRect(se_bar)

        painter.setPen(Qt.white)
        painter.save()
        seizure_text = "Seizure (Sz)"
        metrics = painter.fontMetrics()
        seizure_text_width = metrics.width(seizure_text)
        painter.translate(seizure_bar.right() + 15, seizure_bar.center().y())
        painter.rotate(-90)
        painter.drawText(-seizure_text_width // 2, 0, seizure_text)
        painter.restore()

        painter.save()
        metrics = painter.fontMetrics()
        se_text = "Status Epilepticus (SE)"
        se_text_width = metrics.width(se_text)
        painter.translate(se_bar.right() + 15, se_bar.center().y())
        painter.rotate(-90)
        painter.drawText(-se_text_width // 2, 0, se_text)
        painter.restore()

        label_spacing = 10
        labels = ["Minimum", "Maximum"]
        painter.setPen(Qt.white)
        painter.drawText(seizure_bar.left(), seizure_bar.top() - label_spacing, labels[0])
        painter.drawText(seizure_bar.left(), seizure_bar.bottom() + 15 + label_spacing, labels[1])

        # Show active channel and inactive channel colors
        painter.setPen(Qt.white)
        label_y = seizure_bar.bottom() + 98
        square_y = seizure_bar.bottom() + 60

        # Active
        painter.setPen(Qt.white)
        painter.drawText(10, label_y, "Active")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(ACTIVE))
        painter.drawRect(10, square_y, 20, 20)

        # Inactive (below Active)
        painter.setPen(Qt.white)
        painter.setPen(Qt.white)
        painter.drawText(10, label_y + 60, "Inactive")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(BACKGROUND))
        painter.drawRect(10, square_y + 60, 20, 20)
