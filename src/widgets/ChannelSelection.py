# ChannelSelection.py

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path

from helpers.Constants import MARKER, SIZE

class ChannelSelection(QWidget):
    def __init__(self, parent=None, uploadedImage=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_points = []
        self.uploadedImage = uploadedImage
        self.undo_stack = []
        self.redo_stack = []
        self.setFocusPolicy(Qt.StrongFocus)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        fig = Figure(figsize=(5, 5), dpi=100)
        fig.set_tight_layout(True)
        self.canvas = FigureCanvas(fig)
        layout.addWidget(self.canvas)

        self.ax = fig.add_subplot(111)
        self.ax.set_aspect("equal")

        # Initialize fixed 64x64 grid
        self.x, self.y = np.meshgrid(np.arange(1, 65), np.arange(1, 65))
        self.x, self.y = self.x.flatten(), self.y.flatten()

        # Initial scatter plot
        self.ax.scatter(self.x, self.y, c="k", s=SIZE, alpha=0.3, marker=MARKER)

        # Lasso selector
        self.lasso = LassoSelector(self.ax, self.lasso_callback, button=[1, 3], useblit=True)

        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.invert_yaxis()
        self.canvas.draw()

    def lasso_callback(self, verts):
        path = Path(verts)
        if self.uploadedImage is not None:
            height, width, _ = self.uploadedImage.shape
            new_selected_points = [
                (x, y) for x, y in zip(self.x, self.y)
                if path.contains_point((x * width / 64, y * height / 64))
            ]
        else:
            new_selected_points = [
                (x, y) for x, y in zip(self.x, self.y)
                if path.contains_point((x, y))
            ]

        self.undo_stack.append(self.selected_points.copy())
        self.redo_stack.clear()
        self.selected_points.extend(new_selected_points)
        self.update_selected_points_plot()

        verts = np.append(verts, [verts[0]], axis=0)
        if hasattr(self, "lasso_line"):
            self.lasso_line.remove()
        self.lasso_line = self.ax.plot(verts[:, 0], verts[:, 1], "b-", linewidth=1, alpha=0.8)[0]
        self.canvas.draw()

    def update_selected_points_plot(self):
        if hasattr(self, "selected_points_plot"):
            self.selected_points_plot.remove()

        if self.uploadedImage is not None:
            height, width, _ = self.uploadedImage.shape
            self.selected_points_plot = self.ax.scatter(
                [point[0] * width / 64 for point in self.selected_points],
                [point[1] * height / 64 for point in self.selected_points],
                c="red", s=SIZE, alpha=0.8, marker=MARKER
            )
        else:
            self.selected_points_plot = self.ax.scatter(
                [point[0] for point in self.selected_points],
                [point[1] for point in self.selected_points],
                c="red", s=SIZE, alpha=0.8, marker=MARKER
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C:
            self.clear_selection()
        elif event.key() == Qt.Key_Z:
            if event.modifiers() & Qt.ShiftModifier:
                self.redo_selection()
            else:
                self.undo_selection()

    def clear_selection(self):
        if self.lasso.active:
            self.lasso_line.set_visible(False)
            self.canvas.draw()
        self.undo_stack.append(self.selected_points.copy())
        self.redo_stack.clear()
        self.selected_points.clear()
        self.update_selected_points_plot()
        self.canvas.draw()

    def undo_selection(self):
        if self.undo_stack:
            if self.lasso.active:
                self.lasso_line.set_visible(False)
                self.canvas.draw()
            self.redo_stack.append(self.selected_points.copy())
            self.selected_points = self.undo_stack.pop()
            self.update_selected_points_plot()
            self.canvas.draw()

    def redo_selection(self):
        if self.redo_stack:
            if self.lasso.active:
                self.lasso_line.set_visible(False)
                self.canvas.draw()
            self.undo_stack.append(self.selected_points.copy())
            self.selected_points = self.redo_stack.pop()
            self.update_selected_points_plot()
            self.canvas.draw()

    def showHotkeysHelp(self):
        hotkeys = [
            "No shift+click: keep drawing and use hotkeys.",
            "c: Clear selection",
            "z: Undo selection",
            "shift+z: Redo selection"
        ]
        QMessageBox.information(self, "Hotkeys Help", "\n".join(hotkeys))
