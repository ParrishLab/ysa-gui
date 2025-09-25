from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt

from widgets.ChannelExtract import ChannelExtract
from widgets.Media import open_save_grid_dialog, save_mea_with_plots


class MenuManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_menu_bar(self):
        self.main_window.menuBar = self.main_window.menuBar()
        self.main_window.menuBar.setNativeMenuBar(False)

        self._setup_file_menu()
        self._setup_edit_menu()
        self._setup_view_menu()
        self._setup_help_menu()

    def _setup_file_menu(self):
        self.main_window.fileMenu = QMenu("File", self.main_window)
        self.main_window.menuBar.addMenu(self.main_window.fileMenu)

        self.main_window.openAction = QAction("Open File", self.main_window)
        self.main_window.openAction.triggered.connect(self.main_window.open_file)
        self.main_window.fileMenu.addAction(self.main_window.openAction)

        self.main_window.uploadImageAction = QAction("Upload MEA Grid Image", self.main_window)
        self.main_window.uploadImageAction.triggered.connect(self.main_window.upload_image)
        self.main_window.fileMenu.addAction(self.main_window.uploadImageAction)

        self.main_window.viewHDF5Action = QAction("View HDF5 File", self.main_window)
        self.main_window.viewHDF5Action.triggered.connect(self.main_window.viewHDF5)
        self.main_window.fileMenu.addAction(self.main_window.viewHDF5Action)

        self.main_window.downsampleExportAction = QAction("Downsample and Export", self.main_window)
        self.main_window.downsampleExportAction.triggered.connect(
            lambda: ChannelExtract(self.main_window).exec_()
        )
        self.main_window.fileMenu.addAction(self.main_window.downsampleExportAction)

        self.main_window.fileMenu.addSeparator()

        self.createVideoAction = QAction("Save MEA as Video", self.main_window)
        self.createVideoAction.triggered.connect(self.main_window.show_video_editor)
        self.main_window.fileMenu.addAction(self.createVideoAction)

        self.saveGridAction = QAction("Save MEA as PNG", self.main_window)
        self.saveGridAction.triggered.connect(
            lambda: open_save_grid_dialog(self.main_window)
        )
        self.main_window.fileMenu.addAction(self.saveGridAction)

        self.saveChannelPlotsAction = QAction("Save Channel Plots", self.main_window)
        self.saveChannelPlotsAction.triggered.connect(self.main_window.save_channel_plots)
        self.main_window.fileMenu.addAction(self.saveChannelPlotsAction)

        self.saveMeaWithPlotsAction = QAction("Save MEA with Channel Plots", self.main_window)
        self.saveMeaWithPlotsAction.triggered.connect(
            lambda: save_mea_with_plots(self.main_window)
        )
        self.main_window.fileMenu.addAction(self.saveMeaWithPlotsAction)

    def _setup_edit_menu(self):
        from widgets.Settings import SettingsWidgetManager, DBSCANSettingsWidget, PeakSettingsWidget, SpectrogramSettingsWidget

        self.main_window.editMenu = QMenu("Edit", self.main_window)
        self.main_window.menuBar.addMenu(self.main_window.editMenu)

        self.main_window.settings_manager = SettingsWidgetManager(self.main_window.editMenu)

        self.main_window.db_scan_settings_widget = DBSCANSettingsWidget(self.main_window)
        self.main_window.settings_manager.add_widget(
            "Set DBSCAN settings", self.main_window.db_scan_settings_widget
        )

        self.main_window.peak_settings_widget = PeakSettingsWidget(self.main_window)
        self.main_window.settings_manager.add_widget(
            "Set Peak Settings", self.main_window.peak_settings_widget
        )

        self.main_window.spectrogram_settings_widget = SpectrogramSettingsWidget(self.main_window)
        self.main_window.settings_manager.add_widget(
            "Set spectrogram settings", self.main_window.spectrogram_settings_widget
        )

    def _setup_view_menu(self):
        from PyQt5.QtCore import QTimer

        self.main_window.viewMenu = QMenu("View", self.main_window)
        self.main_window.menuBar.addMenu(self.main_window.viewMenu)

        self.main_window.viewDischargeStartDialogAction = QAction(
            "Open Discharge Start Dialog", self.main_window
        )
        self.main_window.viewDischargeStartDialogAction.triggered.connect(
            self.main_window.open_discharge_start_dialog
        )
        self.main_window.viewMenu.addAction(self.main_window.viewDischargeStartDialogAction)

        self.main_window.toggleEventsOverlayAction = QAction(
            "Detected Events Overlay", self.main_window, checkable=True
        )
        self.main_window.toggleEventsOverlayAction.setChecked(False)
        self.main_window.toggleEventsOverlayAction.triggered.connect(
            self.main_window.toggle_events_overlay
        )
        self.main_window.viewMenu.addAction(self.main_window.toggleEventsOverlayAction)

        self.main_window.toggleLegendAction = QAction("Legend", self.main_window, checkable=True)
        self.main_window.toggleLegendAction.setChecked(False)
        self.main_window.toggleLegendAction.triggered.connect(self.main_window.toggle_legend)
        self.main_window.viewMenu.addAction(self.main_window.toggleLegendAction)

        self.toggleLinesAction = QAction("Spread Lines", self.main_window, checkable=True)
        self.toggleLinesAction.setChecked(False)
        self.toggleLinesAction.triggered.connect(self.main_window.toggle_lines)
        self.main_window.viewMenu.addAction(self.toggleLinesAction)

        self.main_window.togglePropLinesAction = QAction("Discharge Paths", self.main_window, checkable=True)
        self.main_window.togglePropLinesAction.setChecked(False)
        self.main_window.togglePropLinesAction.triggered.connect(self.main_window.toggle_prop_lines)
        self.main_window.viewMenu.addAction(self.main_window.togglePropLinesAction)

        self.main_window.toggleEventsAction = QAction("Detected Events", self.main_window, checkable=True)
        self.main_window.toggleEventsAction.setChecked(True)
        self.main_window.toggleEventsAction.triggered.connect(self.main_window.toggle_events)
        self.main_window.viewMenu.addAction(self.main_window.toggleEventsAction)

        self.main_window.toggleColorMappingAction = QAction("False Color Map", self.main_window, checkable=True)
        self.main_window.toggleColorMappingAction.setChecked(True)
        self.main_window.toggleColorMappingAction.triggered.connect(
            self.main_window.toggle_false_color_map
        )
        self.main_window.viewMenu.addAction(self.main_window.toggleColorMappingAction)

        self.main_window.viewMenu.addSeparator()

        self.main_window.toggleMiniMapAction = QAction("Mini-map", self.main_window, checkable=True)
        self.main_window.toggleMiniMapAction.setChecked(True)
        self.main_window.toggleMiniMapAction.triggered.connect(self.main_window.toggle_mini_map)
        self.main_window.viewMenu.addAction(self.main_window.toggleMiniMapAction)

        self.main_window.togglePlayheadsActions = QAction("Playheads", self.main_window, checkable=True)
        self.main_window.togglePlayheadsActions.setChecked(True)
        self.main_window.togglePlayheadsActions.triggered.connect(self.main_window.toggle_playheads)
        self.main_window.viewMenu.addAction(self.main_window.togglePlayheadsActions)

        self.main_window.antiAliasAction = QAction("Anti-aliasing", self.main_window, checkable=True)
        self.main_window.antiAliasAction.setChecked(False)
        self.main_window.antiAliasAction.triggered.connect(self.main_window.toggle_antialiasing)
        self.main_window.viewMenu.addAction(self.main_window.antiAliasAction)

        self.toggleRegionsAction = QAction("Seizure Regions", self.main_window, checkable=True)
        self.toggleRegionsAction.setChecked(True)
        self.toggleRegionsAction.triggered.connect(self.main_window.toggle_regions)
        self.main_window.viewMenu.addAction(self.toggleRegionsAction)

        self.main_window.toggleSpectrogramAction = QAction("Spectrograms", self.main_window, checkable=True)
        self.main_window.toggleSpectrogramAction.setChecked(False)
        self.main_window.toggleSpectrogramAction.triggered.connect(self.main_window.toggle_spectrogram)
        self.main_window.viewMenu.addAction(self.main_window.toggleSpectrogramAction)

        self.main_window.viewMenu.addSeparator()

        self.main_window.setBinSizeAction = QAction("Set Bin Size", self.main_window)
        self.main_window.setBinSizeAction.triggered.connect(self.main_window.set_bin_size)
        self.main_window.viewMenu.addAction(self.main_window.setBinSizeAction)

        self.main_window.setOrderAmountAction = QAction("Set Order Amount", self.main_window)
        self.main_window.setOrderAmountAction.triggered.connect(self.main_window.set_order_amount)
        self.main_window.viewMenu.addAction(self.main_window.setOrderAmountAction)

        for action in self.main_window.viewMenu.actions():
            if action.isCheckable():
                action.triggered.connect(
                    lambda: QTimer.singleShot(0, self.main_window.viewMenu.show)
                )

    def _setup_help_menu(self):
        self.main_window.helpMenu = QMenu("Help", self.main_window)
        self.main_window.menuBar.addMenu(self.main_window.helpMenu)

        self.main_window.docsAction = QAction("Documentation", self.main_window)
        self.main_window.helpMenu.addAction(self.main_window.docsAction)
        self.main_window.docsAction.triggered.connect(self.main_window.open_docs)

    def set_data_dependent_actions_enabled(self, enabled: bool):
        """Enable/disable actions that require data to be loaded"""
        actions = [
            self.saveGridAction, self.createVideoAction, self.saveChannelPlotsAction,
            self.saveMeaWithPlotsAction, self.toggleLinesAction, self.toggleRegionsAction
        ]
        for action in actions:
            action.setEnabled(enabled)