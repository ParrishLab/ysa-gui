# RealTimeAnalysisWidget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSpinBox,
    QDoubleSpinBox, QFileDialog, QGroupBox, QGridLayout, QSizePolicy
)
from ChannelSelection import ChannelSelection  # Assuming you also copy this class to a separate file


class RealTimeAnalysis(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)

        channelGroupBox = QGroupBox("Real-Time Channel Selection and Settings")
        gridLayout = QGridLayout()

        # Channel Selection Widget
        self.inputGridWidget = ChannelSelection(self)
        self.inputGridWidget.setMinimumSize(400, 400)
        gridLayout.addWidget(self.inputGridWidget, 0, 0)

        # Settings Widget
        settingsWidget = QWidget()
        settingsLayout = QVBoxLayout(settingsWidget)

        uploadButton = QPushButton("Upload Folder")
        settingsLayout.addWidget(uploadButton)

        self.channelCountLabel = QLabel("Channel Count: 0")
        settingsLayout.addWidget(self.channelCountLabel)

        self.rowSkipSpinBox = QSpinBox()
        self.rowSkipSpinBox.setRange(0, 3)
        settingsLayout.addWidget(QLabel("# Rows to Skip:"))
        settingsLayout.addWidget(self.rowSkipSpinBox)

        self.colSkipSpinBox = QSpinBox()
        self.colSkipSpinBox.setRange(0, 3)
        settingsLayout.addWidget(QLabel("# Columns to Skip:"))
        settingsLayout.addWidget(self.colSkipSpinBox)

        self.downsampleSpinBox = QDoubleSpinBox()
        self.downsampleSpinBox.setRange(0, 100000)
        self.downsampleSpinBox.setValue(300)
        settingsLayout.addWidget(QLabel("Downsampling (Hz):"))
        settingsLayout.addWidget(self.downsampleSpinBox)

        self.startTimeSpinBox = QDoubleSpinBox()
        self.startTimeSpinBox.setRange(0, 100000)
        settingsLayout.addWidget(QLabel("Start Time (s):"))
        settingsLayout.addWidget(self.startTimeSpinBox)

        self.endTimeSpinBox = QDoubleSpinBox()
        self.endTimeSpinBox.setRange(0, 100000)
        settingsLayout.addWidget(QLabel("End Time (s):"))
        settingsLayout.addWidget(self.endTimeSpinBox)

        exportButton = QPushButton("Export Channels")
        settingsLayout.addWidget(exportButton)

        restoreButton = QPushButton("Restore Selection")
        settingsLayout.addWidget(restoreButton)

        downsampleExportButton = QPushButton("Downsample Export")
        settingsLayout.addWidget(downsampleExportButton)

        settingsLayout.addStretch()
        gridLayout.addWidget(settingsWidget, 0, 1)

        channelGroupBox.setLayout(gridLayout)
        layout.addWidget(channelGroupBox)
