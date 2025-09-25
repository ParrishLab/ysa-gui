import math
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QRectF, QPointF, QLineF, QTimer
from PyQt5.QtGui import QColor, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsEllipseItem,
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from scipy.signal import spectrogram
from sklearn.cluster import DBSCAN

from src.helpers.Constants import ACTIVE, SE, SEIZURE, BACKGROUND
from src.widgets.RasterPlot import RasterPlot


class VisualizationManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def show_spectrograms(self):
        """Show spectrograms for plotted channels"""
        for i in range(4):
            if self.main_window.plotted_channels[i] is None:
                continue
            self.main_window.graph_widget.trace_curves[i].setVisible(False)

            eeg_data = self.main_window.data[
                self.main_window.plotted_channels[i].row,
                self.main_window.plotted_channels[i].col,
            ]["signal"]

            print(f"Creating spectrogram for channel {i + 1}")

            f, _, Sxx = spectrogram(
                eeg_data,
                fs=self.main_window.sampling_rate,
                window="hann",
                nperseg=self.main_window.chunk_size,
                noverlap=self.main_window.overlap,
                nfft=self.main_window.chunk_size,
                scaling="density",
                mode="psd",
            )

            Sxx_db = 10 * np.log10(Sxx)

            freq_mask = (f >= self.main_window.fs_range[0]) & (f <= self.main_window.fs_range[1])
            Sxx_db = Sxx_db[freq_mask, :]

            cmap = pg.colormap.get("inferno")
            lut = cmap.getLookupTable()

            img = pg.ImageItem()
            img.setLookupTable(lut)
            img.setLevels([np.min(Sxx_db), np.max(Sxx_db)])
            img.setImage(Sxx_db.T, autoLevels=False)

            x_range = (self.main_window.time_vector[0], self.main_window.time_vector[-1])
            y_range = (f[freq_mask][0], f[freq_mask][-1])
            self.main_window.graph_widget.plot_widgets[i].setLabels(left="Hz")

            img.setRect(
                QRectF(
                    x_range[0],
                    y_range[0],
                    x_range[1] - x_range[0],
                    y_range[1] - y_range[0],
                )
            )

            self.main_window.graph_widget.plot_widgets[i].addItem(img)
            img.setZValue(-1)
            self.main_window.graph_widget.plot_widgets[i].getViewBox().autoRange()

    def hide_spectrograms(self):
        """Hide spectrograms for all channels"""
        for i in range(4):
            for item in self.main_window.graph_widget.plot_widgets[i].items():
                if isinstance(item, pg.ImageItem):
                    self.main_window.graph_widget.plot_widgets[i].removeItem(item)

            self.main_window.graph_widget.plot_widgets[i].setLabels(left="mV")
            self.main_window.graph_widget.trace_curves[i].setVisible(True)
            self.main_window.graph_widget.plot_widgets[i].getViewBox().autoRange()

    def show_statistics_widgets(self):
        """Show statistics widgets in stats tab"""
        while self.main_window.stats_tab_layout.count():
            item = self.main_window.stats_tab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for group in self.main_window.groups:
            card_widget = QWidget()
            card_layout = QHBoxLayout(card_widget)

            splitter = QSplitter(Qt.Horizontal)

            image_raster_widget = QWidget()
            image_raster_layout = QHBoxLayout(image_raster_widget)

            image_label = QLabel()
            pixmap = QPixmap(group.image)
            image_label.setPixmap(
                pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            image_raster_layout.addWidget(image_label)

            raster_plot_widget = pg.PlotWidget()
            raster_plot_widget.setAspectLocked(False)
            raster_plot_widget.setBackground("w")
            image_raster_layout.addWidget(raster_plot_widget)

            group_data = np.empty_like(self.main_window.data)
            group_data.fill(None)
            for row, col in group.channels:
                group_data[row - 1, col - 1] = self.main_window.data[row - 1, col - 1]
            group_raster_plot = RasterPlot(
                group_data,
                self.main_window.sampling_rate,
                group.channels,
                self.main_window.raster_downsample_factor,
            )
            group_raster_plot.generate_raster()
            group_raster_plot.create_raster_plot(raster_plot_widget)

            splitter.addWidget(image_raster_widget)

            stats_widget = self._create_stats_widget(group)
            splitter.addWidget(stats_widget)

            card_layout.addWidget(splitter)
            scroll_layout.addWidget(card_widget)

        scroll_area.setWidget(scroll_widget)
        self.main_window.stats_tab_layout.addWidget(scroll_area)

    def _create_stats_widget(self, group):
        """Create statistics widget for a group"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)

        group_name_label = QLabel(f"Group: {group.number}")
        stats_layout.addWidget(group_name_label)

        channel_count_label = QLabel(f"Number of Channels: {len(group.channels)}")
        stats_layout.addWidget(channel_count_label)

        seizure_count = 0
        average_seizure_duration = 0
        average_seizure_strength = 0

        se_count = 0
        average_se_duration = 0
        average_se_strength = 0

        for row, col in group.channels:
            seizures = self.main_window.data[row - 1, col - 1]["SzTimes"]
            se = self.main_window.data[row - 1, col - 1]["SETimes"]
            if seizures.size > 0:
                seizure_count += seizures.shape[0]
            if se.size > 0:
                se_count += se.shape[0]

            for start, stop, strength in seizures:
                average_seizure_duration += stop - start
                average_seizure_strength += strength
            for start, stop, strength in se:
                average_se_duration += stop - start
                average_se_strength += strength

        if seizure_count > 0:
            average_seizure_duration /= seizure_count
            average_seizure_strength /= seizure_count
        else:
            average_seizure_duration = 0
            average_seizure_strength = 0

        if se_count > 0:
            average_se_duration /= se_count
            average_se_strength /= se_count
        else:
            average_se_duration = 0
            average_se_strength = 0

        seizure_count_label = QLabel(f"Number of Seizures: {seizure_count}")
        stats_layout.addWidget(seizure_count_label)

        average_seizure_count = seizure_count / len(group.channels)
        average_seizure_count_label = QLabel(
            f"Average Seizures per Channel: {average_seizure_count:.2f}"
        )
        stats_layout.addWidget(average_seizure_count_label)

        average_seizure_duration_label = QLabel(
            f"Average Seizure Duration: {average_seizure_duration:.2f}"
        )
        stats_layout.addWidget(average_seizure_duration_label)

        average_seizure_strength_label = QLabel(
            f"Average Seizure Strength: {average_seizure_strength:.2f}"
        )
        stats_layout.addWidget(average_seizure_strength_label)

        se_count_label = QLabel(f"Number of SEs: {se_count}")
        stats_layout.addWidget(se_count_label)

        average_se_count = se_count / len(group.channels)
        average_se_count_label = QLabel(f"Average SEs per Channel: {average_se_count:.2f}")
        stats_layout.addWidget(average_se_count_label)

        average_se_duration_label = QLabel(f"Average SE Duration: {average_se_duration:.2f}")
        stats_layout.addWidget(average_se_duration_label)

        average_se_strength_label = QLabel(f"Average SE Strength: {average_se_strength:.2f}")
        stats_layout.addWidget(average_se_strength_label)

        return stats_widget

    def show_seizure_order(self):
        """Show seizure order on grid"""
        if self.main_window.data is None:
            return

        self.hide_seizure_order()

        index = self.main_window.ui_manager.order_combo.currentIndex()
        order = None

        if index == 1:
            order = sorted(
                self.main_window.active_channels,
                key=lambda x: self.main_window.raster_plot.get_first_event_time(
                    x[0] - 1, x[1] - 1, "SzTimes"
                ),
            )
        elif index == 2:
            order = sorted(
                self.main_window.active_channels,
                key=lambda x: self.main_window.raster_plot.get_first_event_time(
                    x[0] - 1, x[1] - 1, "SETimes"
                ),
            )

        if order:
            for i, (row, col) in enumerate(order[: self.main_window.order_amount], start=1):
                cell = self.main_window.grid_widget.cells[row - 1][col - 1]
                cell.setText(str(i))

    def hide_seizure_order(self):
        """Hide seizure order from grid"""
        print("Hiding seizure order")
        for row in range(self.main_window.grid_widget.rows):
            for col in range(self.main_window.grid_widget.cols):
                cell = self.main_window.grid_widget.cells[row][col]
                cell.setText("")

    def show_prop_lines(self):
        """Show propagation lines"""
        for arrow_item in self.main_window.prop_arrow_items:
            arrow_item["arrow"].show()
            arrow_item["arrow_head"].show()

    def hide_prop_lines(self):
        """Hide propagation lines"""
        for arrow_item in self.main_window.prop_arrow_items:
            arrow_item["arrow"].hide()
            arrow_item["arrow_head"].hide()
        self.main_window.prop_arrow_items.clear()

    def show_spread_lines(self):
        """Show spread lines"""
        for arrow_item in self.main_window.arrow_items:
            arrow_item["arrow"].show()
            arrow_item["arrow_head"].show()

    def hide_spread_lines(self):
        """Hide spread lines"""
        for arrow_item in self.main_window.arrow_items:
            arrow_item["arrow"].hide()
            arrow_item["arrow_head"].hide()
        self.main_window.arrow_items.clear()

    def draw_spread_arrows(self, row, col, event_type):
        """Draw arrows showing seizure spread"""
        if len(self.main_window.seized_cells) > 1:
            min_distance = float("inf")
            max_strength = 0
            closest_cell = None
            for seized_row, seized_col in self.main_window.seized_cells[:-1]:
                distance = math.sqrt((row - seized_row) ** 2 + (col - seized_col) ** 2)

                current_strength = self.main_window.get_seizure_strength(seized_row, seized_col)

                if distance < min_distance or (
                    distance == min_distance and current_strength > max_strength
                ):
                    min_distance = distance
                    max_strength = current_strength
                    closest_cell = (seized_row, seized_col)

            if closest_cell and min_distance <= 15:
                start_cell = self.main_window.grid_widget.cells[closest_cell[0]][closest_cell[1]]
                end_cell = self.main_window.grid_widget.cells[row][col]

                cell_width = start_cell.rect().width()
                cell_height = start_cell.rect().height()

                offset = QPointF(cell_width * 1, cell_height * 1)

                start_center = (
                    start_cell.scenePos()
                    + QPointF(cell_width / 2, cell_height / 2)
                    - offset
                )
                end_center = (
                    end_cell.scenePos() + QPointF(cell_width / 2, cell_height / 2) - offset
                )

                arrow = QGraphicsLineItem(QLineF(start_center, end_center))
                if event_type == "SE":
                    arrow_color = SE.darker(150)
                else:
                    TEST = QColor("#fb6f92")
                    arrow_color = TEST
                arrow.setPen(QPen(arrow_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

                arrow_head = QPolygonF()
                arrow_head.append(QPointF(0, 0))
                arrow_head.append(QPointF(-6, -5))
                arrow_head.append(QPointF(-6, 5))
                arrow_head_item = QGraphicsPolygonItem(arrow_head)
                arrow_head_item.setBrush(arrow_color)
                arrow_head_item.setPen(QPen(arrow_color))

                angle = math.degrees(
                    math.atan2(
                        end_center.y() - start_center.y(),
                        end_center.x() - start_center.x(),
                    )
                )
                arrow_head_item.setRotation(angle)

                arrow_offset = 0.5
                arrow_head_item.setPos(
                    end_center
                    - QPointF(
                        arrow_offset * math.cos(math.radians(angle)),
                        arrow_offset * math.sin(math.radians(angle)),
                    )
                )

                self.main_window.grid_widget.scene.addItem(arrow)
                self.main_window.grid_widget.scene.addItem(arrow_head_item)

                self.main_window.arrow_items.append(
                    {
                        "arrow": arrow,
                        "arrow_head": arrow_head_item,
                        "start_cell": closest_cell,
                        "end_cell": (row, col),
                    }
                )
                if self.main_window.do_show_spread_lines:
                    arrow.show()
                    arrow_head_item.show()
                else:
                    arrow.hide()
                    arrow_head_item.hide()

    def remove_seizure_arrows(self, row, col):
        """Remove seizure arrows for a specific cell"""
        arrows_to_remove = []
        for arrow_item in self.main_window.arrow_items:
            if arrow_item["end_cell"] == (row, col):
                self.main_window.grid_widget.scene.removeItem(arrow_item["arrow"])
                self.main_window.grid_widget.scene.removeItem(arrow_item["arrow_head"])
                arrows_to_remove.append(arrow_item)
            elif arrow_item["start_cell"] == (row, col):
                self.main_window.grid_widget.scene.removeItem(arrow_item["arrow"])
                self.main_window.grid_widget.scene.removeItem(arrow_item["arrow_head"])
                arrows_to_remove.append(arrow_item)

        for arrow_item in arrows_to_remove:
            self.main_window.arrow_items.remove(arrow_item)

    def redraw_arrows(self):
        """Redraw all arrows after window resize"""
        for arrow_item in self.main_window.arrow_items + self.main_window.prop_arrow_items:
            start_cell = self.main_window.grid_widget.cells[arrow_item["start_cell"][0]][
                arrow_item["start_cell"][1]
            ]
            end_cell = self.main_window.grid_widget.cells[arrow_item["end_cell"][0]][
                arrow_item["end_cell"][1]
            ]

            cell_width = start_cell.rect().width()
            cell_height = start_cell.rect().height()

            offset = QPointF(cell_width * 1, cell_height * 1)

            start_center = (
                start_cell.scenePos()
                + QPointF(cell_width / 2, cell_height / 2)
                - offset
            )
            end_center = (
                end_cell.scenePos() + QPointF(cell_width / 2, cell_height / 2) - offset
            )

            arrow_item["arrow"].setLine(QLineF(start_center, end_center))

            angle = math.degrees(
                math.atan2(
                    end_center.y() - start_center.y(), end_center.x() - start_center.x()
                )
            )
            arrow_item["arrow_head"].setRotation(angle)

            arrow_offset = 0.5
            arrow_item["arrow_head"].setPos(
                end_center
                - QPointF(
                    arrow_offset * math.cos(math.radians(angle)),
                    arrow_offset * math.sin(math.radians(angle)),
                )
            )

    def blend_colors(self, color1, color2, strength):
        """Blend two colors based on strength"""
        r1, g1, b1, _ = color1.getRgb()
        r2, g2, b2, _ = color2.getRgb()

        blended_color = QColor(
            int(r1 + (r2 - r1) * 0.5),
            int(g1 + (g2 - g1) * 0.5),
            int(b1 + (b2 - b1) * 0.5),
        )

        return blended_color