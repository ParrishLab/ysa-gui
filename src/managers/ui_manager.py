from PyQt5.QtWidgets import (
    QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QSlider, QCheckBox, QComboBox, QPushButton, QScrollArea
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..main_refactored import MainWindow


class UIManager:
    def __init__(self, main_window: 'MainWindow'):
        self.main_window: 'MainWindow' = main_window

    def setup_main_window(self):
        self._setup_main_tabs()
        self._setup_left_pane()
        self._setup_right_pane()
        self._setup_bottom_pane()

    def _setup_main_tabs(self):
        self.main_window.main_tab_widget = QTabWidget()
        self.main_window.tab_widget = QTabWidget()
        self.main_window.main_tab_widget.currentChanged.connect(
            self.main_window.update_tab_layout)
        self.main_window.setCentralWidget(self.main_window.main_tab_widget)

        self.main_window.main_tab = QWidget()
        self.main_window.main_tab_layout = QHBoxLayout()
        self.main_window.main_tab.setLayout(self.main_window.main_tab_layout)

        self.main_window.stats_tab = QWidget()
        self.main_window.stats_tab_layout = QVBoxLayout()
        self.main_window.stats_tab.setLayout(self.main_window.stats_tab_layout)

        self.main_window.main_tab_widget.addTab(
            self.main_window.main_tab, "Main")
        self.main_window.main_tab_widget.addTab(
            self.main_window.stats_tab, "Stats")

    def _setup_left_pane(self):
        from widgets.GridWidget import GridWidget
        from widgets.SquareWidget import SquareWidget
        from widgets.ClusterTracker import ClusterTracker
        from widgets.LegendWidget import LegendWidget

        self.main_window.left_pane = QWidget()
        self.main_window.left_layout = QVBoxLayout()
        self.main_window.left_pane.setLayout(self.main_window.left_layout)
        self.main_window.main_tab_layout.addWidget(self.main_window.left_pane)

        self.main_window.left_layout.addWidget(self.main_window.tab_widget)

        self.main_window.grid_widget = GridWidget(64, 64, self.main_window)
        self.main_window.grid_widget.setMinimumHeight(
            self.main_window.grid_widget.height() + 100)
        self.main_window.grid_widget.cell_clicked.connect(
            self.main_window.on_cell_clicked)
        self.main_window.grid_widget.save_as_video_requested.connect(
            self.main_window.show_video_editor
        )
        self.main_window.grid_widget.save_as_image_requested.connect(
            lambda: self.main_window._save_grid_dialog()
        )

        square_widget = SquareWidget()
        square_layout = QVBoxLayout()
        square_widget.setLayout(square_layout)
        square_layout.addWidget(self.main_window.grid_widget)

        self.main_window.cluster_tracker = ClusterTracker()

        self.main_window.legend_widget = LegendWidget()
        self.main_window.legend_widget.setVisible(False)

        mea_grid_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.main_window.legend_widget)
        top_layout.addWidget(square_widget)

        mea_grid_layout.addLayout(top_layout)

        mea_grid_widget = QWidget()
        mea_grid_widget.setLayout(mea_grid_layout)

        self.main_window.tab_widget.addTab(mea_grid_widget, "MEA Grid")

        self._setup_raster_tab()

        self.main_window.tab_widget.currentChanged.connect(
            self.main_window.update_tab_layout)

    def _setup_raster_tab(self):
        self.main_window.second_tab_widget = QWidget()
        self.main_window.second_tab_layout = QVBoxLayout()
        self.main_window.second_tab_widget.setLayout(
            self.main_window.second_tab_layout)
        self.main_window.tab_widget.addTab(
            self.main_window.second_tab_widget, "Raster Plot")

        self.main_window.second_plot_widget = pg.PlotWidget()
        self.main_window.second_plot_widget.setAspectLocked(False)
        self.main_window.second_plot_widget.setBackground("w")
        self.main_window.second_tab_layout.addWidget(
            self.main_window.second_plot_widget)

        self.main_window.raster_settings_layout = QHBoxLayout()
        self.main_window.second_tab_layout.addLayout(
            self.main_window.raster_settings_layout)

        self.main_window.raster_settings_layout.addWidget(
            QLabel("Raster Settings:"))

        self.main_window.edit_raster_settings_button = QPushButton(
            "Edit Raster Settings")
        self.main_window.raster_settings_layout.addWidget(
            self.main_window.edit_raster_settings_button)
        self.main_window.edit_raster_settings_button.clicked.connect(
            self.main_window.edit_raster_settings
        )

        self.main_window.create_groups_button = QPushButton("Create Groups")
        self.main_window.raster_settings_layout.addWidget(
            self.main_window.create_groups_button)
        self.main_window.create_groups_button.clicked.connect(
            self.main_window.create_groups)

        self.main_window.toggle_color_mode_button = QPushButton(
            "Toggle Color Mode")
        self.main_window.raster_settings_layout.addWidget(
            self.main_window.toggle_color_mode_button)
        self.main_window.toggle_color_mode_button.clicked.connect(
            self.main_window.toggle_raster_color_mode
        )

    def _setup_right_pane(self):
        from widgets.GraphWidget import GraphWidget

        self.main_window.right_pane = QWidget()
        self.main_window.right_layout = QVBoxLayout()
        self.main_window.right_pane.setLayout(self.main_window.right_layout)
        self.main_window.main_tab_layout.addWidget(self.main_window.right_pane)

        self.main_window.right_splitter = QSplitter(Qt.Vertical)
        self.main_window.right_layout.addWidget(
            self.main_window.right_splitter)

        self.main_window.graph_pane = QWidget()
        self.main_window.graph_layout = QVBoxLayout()
        self.main_window.graph_pane.setLayout(self.main_window.graph_layout)
        self.main_window.right_splitter.addWidget(self.main_window.graph_pane)

        self.main_window.graph_widget = GraphWidget(self.main_window)
        self.main_window.graph_layout.addWidget(self.main_window.graph_widget)
        self.main_window.graph_widget.region_clicked.connect(
            self.main_window.handle_region_clicked)
        self.main_window.graph_widget.save_single_plot.connect(
            lambda: self.main_window.save_channel_plot(
                self.main_window.graph_widget.active_plot_index)
        )
        self.main_window.graph_widget.save_all_plots.connect(
            self.main_window.save_channel_plots)

        self._setup_settings_pane()

    def _setup_settings_pane(self):
        self.main_window.settings_pane = QWidget()
        self.main_window.settings_layout = QVBoxLayout()
        self.main_window.settings_pane.setLayout(
            self.main_window.settings_layout)
        self.main_window.right_splitter.addWidget(
            self.main_window.settings_pane)

        self.main_window.settings_top_layout = QHBoxLayout()
        self.main_window.settings_layout.addLayout(
            self.main_window.settings_top_layout)

        self.main_window.opacity_label = QLabel("Image Opacity:")
        self.main_window.settings_top_layout.addWidget(
            self.main_window.opacity_label)

        self.main_window.opacity_slider = QSlider(Qt.Horizontal)
        self.main_window.opacity_slider.setRange(0, 100)
        self.main_window.opacity_slider.setValue(100)
        self.main_window.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.main_window.opacity_slider.setTickInterval(25)
        self.main_window.opacity_slider.valueChanged.connect(
            self.main_window.set_grid_opacity)
        self.main_window.settings_top_layout.addWidget(
            self.main_window.opacity_slider)

        self.show_order_checkbox = QCheckBox("Show Order")
        self.show_order_checkbox.setEnabled(False)
        self.main_window.settings_top_layout.addWidget(
            self.show_order_checkbox)
        self.show_order_checkbox.stateChanged.connect(
            self.main_window.toggle_order)

        self.order_combo = QComboBox()
        self.order_combo.addItems(
            ["Default", "Order by Seizure", "Order by SE"]
        )
        self.main_window.settings_top_layout.addWidget(
            self.order_combo)
        self.order_combo.currentIndexChanged.connect(
            self.main_window.set_raster_order)

        self._setup_control_layout()

    def _setup_control_layout(self):
        self.main_window.control_layout = QHBoxLayout()
        self.main_window.settings_layout.addLayout(
            self.main_window.control_layout)

        self.main_window.open_button = QPushButton(" Open File")
        self.main_window.open_button.clicked.connect(
            self.main_window.open_file)
        self.main_window.control_layout.addWidget(self.main_window.open_button)

        self.main_window.low_ram_checkbox = QCheckBox("󰡵 Low RAM Mode")
        self.main_window.control_layout.addWidget(
            self.main_window.low_ram_checkbox)

        self.cpp_mode_checkbox = QCheckBox(" Use C++")
        self.cpp_mode_checkbox.stateChanged.connect(
            self.main_window.toggle_cpp_mode)
        self.main_window.control_layout.addWidget(
            self.cpp_mode_checkbox)

        self.view_button = QPushButton(" Quick View")
        self.view_button.clicked.connect(
            self.main_window.analysis_manager.run_analysis)
        self.main_window.control_layout.addWidget(self.view_button)

        self.run_button = QPushButton(" Run Analysis")
        self.run_button.clicked.connect(
            self.main_window.analysis_manager.run_analysis)
        self.main_window.control_layout.addWidget(self.run_button)

        self.clear_button = QPushButton("󰆴 Clear Plots")
        self.main_window.control_layout.addWidget(
            self.clear_button)
        self.clear_button.clicked.connect(
            self.main_window.clear_plots)

    def _setup_bottom_pane(self):
        from widgets.ProgressBar import EEGScrubberWidget

        self.main_window.bottom_pane = QWidget()
        self.main_window.bottom_layout = QHBoxLayout()
        self.main_window.bottom_pane.setLayout(self.main_window.bottom_layout)
        self.main_window.right_layout.addWidget(self.main_window.bottom_pane)

        self.main_window.playback_layout = QHBoxLayout()
        self.main_window.bottom_layout.addLayout(
            self.main_window.playback_layout)

        self.progress_bar = EEGScrubberWidget()
        self.progress_bar.valueChanged.connect(
            self.main_window.seekPosition)
        self.main_window.playback_layout.addWidget(
            self.progress_bar, 1)

        self._setup_playback_controls()

    def _setup_playback_controls(self):
        from PyQt5.QtCore import QTimer

        self.skip_backward_button = QPushButton("")
        self.skip_backward_button.clicked.connect(
            self.main_window.skipBackward)
        self.progress_bar.control_layout.addWidget(
            self.skip_backward_button)

        self.prev_frame_button = QPushButton("")
        self.prev_frame_button.clicked.connect(
            self.main_window.stepBackward)
        self.progress_bar.control_layout.addWidget(
            self.prev_frame_button)

        self.play_pause_button = QPushButton("")
        self.play_pause_button.clicked.connect(
            self.main_window.playPause)
        self.progress_bar.control_layout.addWidget(
            self.play_pause_button)

        self.main_window.playback_timer = QTimer()
        self.main_window.playback_timer.timeout.connect(
            self.main_window.updatePlayback)

        self.next_frame_button = QPushButton("")
        self.next_frame_button.clicked.connect(
            self.main_window.stepForward)
        self.progress_bar.control_layout.addWidget(
            self.next_frame_button)

        self.skip_forward_button = QPushButton("")
        self.skip_forward_button.clicked.connect(
            self.main_window.skipForward)
        self.progress_bar.control_layout.addWidget(
            self.skip_forward_button)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(
            ["0.01", "0.1", "0.25", "0.5", "1.0", "2.0", "4.0", "16.0"]
        )
        self.speed_combo.setCurrentIndex(2)
        self.speed_combo.currentIndexChanged.connect(
            self.main_window.setPlaybackSpeed)

        self.speed_combo.view().setMinimumWidth(50)
        self.progress_bar.control_layout.addWidget(
            self.speed_combo)

    def set_analysis_widgets_enabled(self, enabled: bool):
        """Enable/disable analysis-related widgets"""
        self.run_button.setEnabled(enabled)
        self.view_button.setEnabled(enabled)

    def set_playback_widgets_enabled(self, enabled: bool):
        """Enable/disable playback-related widgets"""
        widgets = [
            self.clear_button, self.skip_backward_button, self.prev_frame_button,
            self.play_pause_button, self.next_frame_button, self.skip_forward_button,
            self.progress_bar, self.speed_combo, self.order_combo
        ]
        for widget in widgets:
            widget.setEnabled(enabled)

        if not enabled:
            self.show_order_checkbox.setEnabled(False)
