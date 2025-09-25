from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QKeyEvent, QMouseEvent


class EventHandler:
    def __init__(self, main_window):
        self.main_window = main_window

    def handle_key_press(self, event: QKeyEvent | None):
        """Handle key press events"""
        key_mapping = [Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4]
        shape_mapping = ["", "󰔷", "x", ""]

        if event.key() in key_mapping:
            self._handle_channel_selection(event, key_mapping, shape_mapping)
        else:
            self._handle_other_keys(event)

    def _handle_channel_selection(self, event, key_mapping, shape_mapping):
        """Handle channel selection keys (1-4)"""
        index = key_mapping.index(event.key())
        if self.main_window.selected_channel is not None:
            row, col = self.main_window.selected_channel
            seizures = self.main_window.data[row, col]["SzTimes"]
            se = self.main_window.data[row, col]["SETimes"]
            if self.main_window.data is not None:
                if self.main_window.plotted_channels[index] is not None:
                    self.main_window.plotted_channels[index].plotted_state = False
                    self.main_window.plotted_channels[index].plotted_shape = None
                    self.main_window.plotted_channels[index].update()
                self.main_window.plotted_channels[index] = self.main_window.grid_widget.cells[row][col]
                self.main_window.plotted_channels[index].plotted_state = True
                self.main_window.plotted_channels[index].plotted_shape = shape_mapping[index]
                self.main_window.plotted_channels[index].update()

                if self.main_window.raster_plot is not None:
                    raster_plotted_channels = []
                    for i in range(4):
                        if self.main_window.plotted_channels[i] is not None:
                            r_row, r_col = (
                                self.main_window.plotted_channels[i].row + 1,
                                self.main_window.plotted_channels[i].col + 1,
                            )
                            raster_plotted_channels.append((r_row, r_col))
                    self.main_window.raster_plot.set_plotted_channels(
                        raster_plotted_channels)

            ignore = int(10 * self.main_window.sampling_rate)

            self.main_window.graph_widget.plot(
                self.main_window.time_vector[ignore:-ignore],
                self.main_window.data[row, col]["signal"][ignore:-ignore],
                f"{shape_mapping[index]} Channel ({row + 1}, {col + 1})",
                "sec",
                "mV",
                index,
                shape_mapping[index],
                seizures,
                se,
            )

            self.main_window.graph_widget.plot_peaks()
            self.main_window.grid_widget.cells[row][col].clicked_state = False
            self.main_window.grid_widget.cells[row][col].selected_tooltip.hide(
            )
            self.main_window.grid_widget.cells[row][col].update()
            self.main_window.grid_widget.selected_channel = None

            if self.main_window.toggleSpectrogramAction.isChecked():
                self.main_window.hide_spectrograms()
                self.main_window.show_spectrograms()

    def _handle_other_keys(self, event):
        """Handle other keyboard shortcuts"""
        if event.key() == Qt.Key_Shift:
            self.main_window.graph_widget.change_view_mode("pan")
        elif event.key() == Qt.Key_Right:
            if self.main_window.ui_manager.skip_backward_button.isEnabled():
                self.main_window.stepForward()
        elif event.key() == Qt.Key_Left:
            if self.main_window.ui_manager.skip_forward_button.isEnabled():
                self.main_window.stepBackward()
        elif event.key() == Qt.Key_Space:
            if self.main_window.ui_manager.play_pause_button.isEnabled():
                self.main_window.playPause()
        elif event.key() == Qt.Key_Up:
            if self.main_window.ui_manager.speed_combo.currentIndex() < self.main_window.ui_manager.speed_combo.count() - 1:
                self.main_window.ui_manager.speed_combo.setCurrentIndex(
                    self.main_window.ui_manager.speed_combo.currentIndex() + 1
                )
        elif event.key() == Qt.Key_Down:
            if self.main_window.ui_manager.speed_combo.currentIndex() > 0:
                self.main_window.ui_manager.speed_combo.setCurrentIndex(
                    self.main_window.ui_manager.speed_combo.currentIndex() - 1
                )
        elif event.key() == Qt.Key_L:
            self.main_window.lock_to_playhead = not self.main_window.lock_to_playhead
            if self.main_window.lock_to_playhead:
                self.main_window.lock_plots_to_playhead()
        elif event.key() == Qt.Key_S:
            self._handle_seek_to_cursor()
        elif event.key() == Qt.Key_F:
            self._handle_toggle_discharge_peaks()
        elif event.key() == Qt.Key_B:
            self.main_window.set_custom_region()
        elif event.key() == Qt.Key_A:
            self.main_window.find_discharges()
        elif event.key() == Qt.Key_R:
            self._handle_draw_seizures()
        elif event.key() == Qt.Key_H:
            self._handle_draw_beginning_points()
        elif event.key() == Qt.Key_J:
            self._handle_draw_heatmap()
        elif event.key() == Qt.Key_K:
            self._handle_create_continuous_heatmap()
        elif event.key() == Qt.Key_G:
            self.main_window.auto_analyze()
        elif event.key() == Qt.Key_T:
            if self.main_window.is_auto_analyzing:
                self.main_window.is_auto_analyzing = False
        elif event.key() == Qt.Key_M:
            self._handle_add_marker()
        elif event.key() == Qt.Key_Return:
            self._handle_confirmation(True)
        elif event.key() == Qt.Key_Escape:
            self._handle_confirmation(False)
        elif event.key() == Qt.Key_V:
            self.main_window.update_grid(red=False)

    def _handle_seek_to_cursor(self):
        """Handle seeking to cursor position"""
        cursor_pos = QCursor.pos()
        for i in range(4):
            plot_widget = self.main_window.graph_widget.plot_widgets[i]

            plot_item = plot_widget.getPlotItem()
            view_box = plot_item.getViewBox()

            local_pos = plot_widget.mapFromGlobal(cursor_pos)

            if plot_widget.rect().contains(local_pos):
                scene_pos = plot_item.mapToScene(local_pos)
                view_pos = view_box.mapSceneToView(scene_pos)
                seek_pos = view_pos.x()

                self.main_window.ui_manager.progress_bar.setValue(
                    int(seek_pos * self.main_window.sampling_rate))
                self.main_window.update_grid()
                if self.main_window.lock_to_playhead:
                    self.main_window.lock_plots_to_playhead()
                break

    def _handle_toggle_discharge_peaks(self):
        """Handle toggling discharge peaks display"""
        import pyqtgraph as pg

        self.main_window.show_discharge_peaks = not self.main_window.show_discharge_peaks
        if not self.main_window.show_discharge_peaks:
            for i in range(4):
                if self.main_window.plotted_channels[i] is not None:
                    for item in self.main_window.graph_widget.plot_widgets[i].items():
                        if isinstance(item, pg.ScatterPlotItem):
                            self.main_window.graph_widget.plot_widgets[i].removeItem(
                                item)
        else:
            self.main_window.graph_widget.plot_peaks()

    def _handle_draw_seizures(self):
        """Handle drawing seizures"""
        cell_width = self.main_window.grid_widget.cells[0][0].rect().width()
        cell_height = self.main_window.grid_widget.cells[0][0].rect().height()
        self.main_window.cluster_tracker.draw_seizures(
            self.main_window.grid_widget.scene, cell_width, cell_height
        )

    def _handle_draw_beginning_points(self):
        """Handle drawing beginning points"""
        cell_width = self.main_window.grid_widget.cells[0][0].rect().width()
        cell_height = self.main_window.grid_widget.cells[0][0].rect().height()
        self.main_window.cluster_tracker.draw_beginning_points(
            self.main_window.grid_widget.scene, cell_width, cell_height
        )

    def _handle_draw_heatmap(self):
        """Handle drawing heatmap"""
        rows, cols = 64, 64
        cell_width = self.main_window.grid_widget.cells[0][0].rect().width()
        cell_height = self.main_window.grid_widget.cells[0][0].rect().height()
        self.main_window.cluster_tracker.draw_heatmap(
            self.main_window.grid_widget.scene, cell_width, cell_height, rows, cols
        )

    def _handle_create_continuous_heatmap(self):
        """Handle creating continuous heatmap"""
        rows, cols = 64, 64
        cell_width = self.main_window.grid_widget.cells[0][0].rect().width()
        cell_height = self.main_window.grid_widget.cells[0][0].rect().height()
        self.main_window.cluster_tracker.create_continuous_heatmap(
            self.main_window.grid_widget.scene, cell_width, cell_height, rows, cols
        )

    def _handle_add_marker(self):
        """Handle adding marker"""
        current_time = self.main_window.ui_manager.progress_bar.value() / \
            self.main_window.sampling_rate
        self.main_window.markers.append(current_time)
        self.main_window.ui_manager.progress_bar.setMarkers(
            self.main_window.markers)
        print(f"Added marker at {current_time}")

    def _handle_confirmation(self, confirmed):
        """Handle confirmation dialog"""
        if self.main_window.need_confirmation:
            self.main_window.discharge_start_dialog.confirm(confirmed)
            self.main_window.need_confirmation = False
            if not confirmed:
                self.main_window.stepForward()

    def handle_key_release(self, event: QKeyEvent | None):
        """Handle key release events"""
        if event.key() == Qt.Key_Shift:
            self.main_window.graph_widget.change_view_mode("rect")
        elif event.key() in [Qt.Key_R, Qt.Key_H, Qt.Key_J, Qt.Key_K]:
            self.main_window.cluster_tracker.clear_plot(
                self.main_window.grid_widget.scene)
        elif event.key() == Qt.Key_V:
            self.main_window.update_grid(red=True)

    def handle_mouse_press(self, event: QMouseEvent | None):
        """Handle mouse press events"""
        if not self.main_window.grid_widget.underMouse() and not self.main_window.is_recording_video:
            self.main_window.deselect_cell()

    def handle_cell_click(self, row, col):
        """Handle cell click events"""
        if self.main_window.selected_channel:
            prev_row, prev_col = self.main_window.selected_channel
            prev_cell = self.main_window.grid_widget.cells[prev_row][prev_col]
            prev_cell.clicked_state = False
            prev_cell.update()
            prev_cell.selected_tooltip.hide()
            prev_cell.hover_tooltip.hide()
        self.main_window.selected_channel = (row, col)

    def handle_region_click(self, start, stop):
        """Handle region click events"""
        import math

        print(f"Region clicked: {start}, {stop}")
        for i in range(4):
            if self.main_window.plotted_channels[i] is not None:
                self.main_window.graph_widget.plot_widgets[i].setXRange(
                    start, stop)
                self.main_window.ui_manager.progress_bar.setValue(
                    math.floor(start * self.main_window.sampling_rate)
                )
                self.main_window.last_skip_time = start
        self.main_window.current_region = (start, stop)
