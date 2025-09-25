from PyQt5.QtCore import QTimer

from helpers.Constants import PAUSE_ICON, PLAY_ICON


class PlaybackManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def skip_backward(self):
        """Skip to previous seizure/SE event"""
        if self.main_window.data is None or self.main_window.plotted_channels == [None] * 4:
            return

        current_time = self.main_window.ui_manager.progress_bar.value() / \
            self.main_window.sampling_rate
        start_time = 0

        for i in range(4):
            if self.main_window.plotted_channels[i] is not None:
                row, col = self.main_window.plotted_channels[i].row, self.main_window.plotted_channels[i].col
                seizures = self.main_window.data[row, col]["SzTimes"]
                se = self.main_window.data[row, col]["SETimes"]
                for seizure in seizures:
                    if seizure[0] < current_time:
                        start_time = max(start_time, seizure[0])
                for se_event in se:
                    if se_event[0] < current_time:
                        start_time = max(start_time, se_event[0])

        self.main_window.last_skip_time = start_time
        next_index = int(start_time * self.main_window.sampling_rate)

        if next_index > 0:
            self.main_window.ui_manager.progress_bar.setValue(next_index)
            self._update_plot_ranges(start_time)
            self.main_window.update_grid()
        else:
            self.main_window.ui_manager.progress_bar.setValue(0)

    def step_backward(self):
        """Step backward by speed interval"""
        speed = float(self.main_window.ui_manager.speed_combo.currentText())
        current_value = self.main_window.ui_manager.progress_bar.value()
        next_value = current_value - \
            int(speed * self.main_window.sampling_rate)

        if next_value >= 0:
            self.main_window.ui_manager.progress_bar.setValue(next_value)
            self.main_window.update_grid()
        else:
            self.main_window.ui_manager.progress_bar.setValue(0)

    def pause_playback(self):
        """Pause playback"""
        self.main_window.ui_manager.play_pause_button.setText(PLAY_ICON)
        self.main_window.playback_timer.stop()

    def play_pause(self):
        """Toggle play/pause state"""
        if self.main_window.ui_manager.play_pause_button.text() == PLAY_ICON:
            self.main_window.ui_manager.play_pause_button.setText(PAUSE_ICON)
            self.main_window.playback_timer.start(50)
        else:
            self.main_window.ui_manager.play_pause_button.setText(PLAY_ICON)
            self.main_window.playback_timer.stop()

    def update_playback(self):
        """Update playback position during play"""
        speed = float(self.main_window.ui_manager.speed_combo.currentText())
        skip_frames = int(speed * self.main_window.sampling_rate)

        current_value = self.main_window.ui_manager.progress_bar.value()
        next_value = current_value + skip_frames

        if next_value <= self.main_window.ui_manager.progress_bar.maximum():
            self.main_window.ui_manager.progress_bar.setValue(next_value)
            if self.main_window.lock_to_playhead:
                self.lock_plots_to_playhead()
        else:
            self.main_window.ui_manager.progress_bar.setValue(
                self.main_window.ui_manager.progress_bar.maximum())
            self.main_window.playback_timer.stop()
            self.main_window.ui_manager.play_pause_button.setText(PLAY_ICON)

    def lock_plots_to_playhead(self):
        """Lock plot view to follow playhead"""
        current_time = self.main_window.ui_manager.progress_bar.value() / \
            self.main_window.sampling_rate
        for plot_widget in self.main_window.graph_widget.plot_widgets:
            view_box = plot_widget.getPlotItem().getViewBox()
            x_range = view_box.viewRange()[0]
            x_width = x_range[1] - x_range[0]
            x_min = current_time - x_width / 2
            x_max = current_time + x_width / 2
            view_box.setRange(xRange=(x_min, x_max), padding=0)

    def step_forward(self):
        """Step forward by speed interval"""
        speed = float(self.main_window.ui_manager.speed_combo.currentText())
        current_value = self.main_window.ui_manager.progress_bar.value()
        next_value = current_value + \
            int(speed * self.main_window.sampling_rate)

        if next_value <= self.main_window.ui_manager.progress_bar.maximum():
            self.main_window.ui_manager.progress_bar.setValue(next_value)
            self.main_window.update_grid()
        else:
            self.main_window.ui_manager.progress_bar.setValue(
                self.main_window.ui_manager.progress_bar.maximum())

    def skip_forward(self):
        """Skip to next seizure/SE event"""
        if self.main_window.data is None or self.main_window.plotted_channels == [None] * 4:
            return

        current_time = self.main_window.ui_manager.progress_bar.value() / \
            self.main_window.sampling_rate
        start_time = self.main_window.recording_length

        for i in range(4):
            if self.main_window.plotted_channels[i] is not None:
                row, col = self.main_window.plotted_channels[i].row, self.main_window.plotted_channels[i].col
                seizures = self.main_window.data[row, col]["SzTimes"]
                se = self.main_window.data[row, col]["SETimes"]
                for seizure in seizures:
                    if seizure[0] > current_time and self.main_window.last_skip_time != seizure[0]:
                        start_time = min(start_time, seizure[0])
                for se_event in se:
                    if (
                        se_event[0] > current_time
                        and self.main_window.last_skip_time != se_event[0]
                    ):
                        start_time = min(start_time, se_event[0])

        self.main_window.last_skip_time = start_time
        next_index = int(start_time * self.main_window.sampling_rate)

        if next_index < self.main_window.ui_manager.progress_bar.maximum():
            self.main_window.ui_manager.progress_bar.setValue(next_index)
            self._update_plot_ranges(start_time)
            self.main_window.update_grid()
        else:
            self.main_window.ui_manager.progress_bar.setValue(
                self.main_window.ui_manager.progress_bar.maximum())

    def _update_plot_ranges(self, start_time):
        """Update plot widget ranges"""
        for plot_widget in self.main_window.graph_widget.plot_widgets:
            view_box = plot_widget.getPlotItem().getViewBox()
            x_range = view_box.viewRange()[0]
            x_width = x_range[1] - x_range[0]
            x_min = start_time - x_width / 2
            x_max = start_time + x_width / 2
            view_box.setRange(xRange=(x_min, x_max), padding=0)

    def set_playback_speed(self, index):
        """Set playback speed"""
        interval = 50
        self.main_window.playback_timer.setInterval(interval)

    def seek_position(self, value):
        """Seek to specific position"""
        self.main_window.graph_widget.update_red_lines(
            value, self.main_window.sampling_rate)
        if self.main_window.raster_plot is not None:
            if self.main_window.raster_plot.raster_red_line is not None:
                percentage = value / self.main_window.ui_manager.progress_bar.maximum()
                scaled_percentage = percentage * \
                    len(self.main_window.active_channels)
                self.main_window.raster_plot.raster_red_line.setPos(
                    scaled_percentage)

        if self.main_window.lock_to_playhead:
            self.lock_plots_to_playhead()

        self.main_window.update_grid()

