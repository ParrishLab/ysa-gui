import numpy as np
import pyqtgraph as pg
from scipy.signal import spectrogram
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout
)
from PyQt5.QtCore import QRect, QSize, Qt

FS = 100  # Sampling frequency of the EEG data
CHUNKSZ = 1024  # Chunk size for FFT
OVERLAP = 64  # Overlap between chunks
FREQ_RANGE = (0.5, 50)  # Frequency range of interest for seizure activity


class SpectrogramWidget(pg.PlotWidget):
    def __init__(
        self,
        eeg_data,
        fs=100,
        chunk_size=1024,
        overlap=64,
        fs_range=(0.5, 50),
        linked_widget=None,
    ):
        super(SpectrogramWidget, self).__init__()

        self.img = pg.ImageItem()
        self.addItem(self.img)

        # Calculate spectrogram
        Sxx_db = self.calculate_spectrogram(eeg_data, fs, chunk_size, overlap, fs_range)

        # Set colormap
        cmap = pg.colormap.get("inferno")
        self.img.setLookupTable(cmap.getLookupTable())
        self.img.setLevels([np.min(Sxx_db), np.max(Sxx_db)])

        # Setup the correct scaling for y-axis
        freq = np.arange((chunk_size / 2) + 1) / (float(chunk_size) / fs)
        freq_mask = (freq >= fs_range[0]) & (freq <= fs_range[1])
        freq = freq[freq_mask]
        self.setLabel("left", "Frequency", units="Hz")
        self.setLabel("bottom", "Time", units="s")
        self.setXRange(0, eeg_data.shape[0] / fs)
        self.setYRange(fs_range[0], fs_range[1])

        if linked_widget is not None:
            self.setXLink(linked_widget)
            self.setYLink(linked_widget)

        self.show()
        self.getPlotItem().getViewBox().autoRange()

    def calculate_spectrogram(self, eeg_data, fs, chunk_size, overlap, fs_range):
        print(f"EEG data shape: {eeg_data.shape}")

        # Calculate spectrogram for the entire dataset at once
        f, t, Sxx = spectrogram(
            eeg_data,
            fs=fs,
            window="hann",
            nperseg=chunk_size,
            noverlap=overlap,
            nfft=chunk_size,
            scaling="density",
            mode="psd",
        )

        # Convert power spectral density to dB scale
        Sxx_db = 10 * np.log10(Sxx)

        # Extract the frequency range of interest
        freq_mask = (f >= fs_range[0]) & (f <= fs_range[1])
        Sxx_db = Sxx_db[freq_mask, :]

        # Set the image array
        self.img_array = Sxx_db
        self.img.setImage(
            self.img_array.T, autoLevels=False
        )  # Transpose the spectrogram array for correct orientation
        return Sxx_db
    
    class ExportSpectrograms(QDialog):
        def __init__(self, parent=None, plot_index=None):
            super().__init__(parent)
            self.parent = parent
            self.plot_index = plot_index
            self.setWindowTitle("Export Spectrograms")
            self.setMinimumWidth(300)
            self.initUI()

        def initUI(self):
            layout = QVBoxLayout(self)

            # Channel selection
            self.channel_checkboxes = []
            if (
                self.plot_index is not None
                and self.parent.plotted_channels[self.plot_index] is not None
            ):
                row, col = (
                    self.parent.plotted_channels[self.plot_index].row,
                    self.parent.plotted_channels[self.plot_index].col,
                )
                checkbox = QCheckBox(f"Channel ({row + 1}, {col + 1})")
                checkbox.setChecked(True)
                layout.addWidget(checkbox)
                self.channel_checkboxes.append(checkbox)
            else:
                for i in range(4):
                    if self.parent.plotted_channels[i] is not None:
                        row, col = (
                            self.parent.plotted_channels[i].row,
                            self.parent.plotted_channels[i].col,
                        )
                        checkbox = QCheckBox(f"Channel ({row + 1}, {col + 1})")
                        checkbox.setChecked(True)
                        layout.addWidget(checkbox)
                        self.channel_checkboxes.append(checkbox)

                # Select All checkbox
                self.select_all_checkbox = QCheckBox("Select All")
                self.select_all_checkbox.setChecked(True)
                self.select_all_checkbox.stateChanged.connect(self.toggle_all_channels)
                layout.addWidget(self.select_all_checkbox)

            # Buttons
            button_layout = QHBoxLayout()
            save_button = QPushButton("Save")
            save_button.clicked.connect(self.save_plots)
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)

        def toggle_all_channels(self, state):
            for checkbox in self.channel_checkboxes:
                checkbox.setChecked(state == Qt.Checked)

