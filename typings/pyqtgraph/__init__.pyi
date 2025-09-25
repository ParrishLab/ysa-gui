# Type stubs for pyqtgraph
from typing import Any, Optional, Tuple, List, Union
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QPen
import numpy as np
from numpy.typing import NDArray


class PlotCurveItem:
    def setData(self, x: Optional[Union[NDArray[np.float64], List[float]]] = None,
                y: Optional[Union[NDArray[np.float64], List[float]]] = None) -> None: ...
    def setDownsampling(self, auto: bool = True,
                        method: str = "peak", ds: int = 100) -> None: ...

    def setClipToView(self, clip: bool) -> None: ...


class PlotWidget(QWidget):
    def clear(self) -> None: ...

    def plot(self,
             x: Optional[Union[NDArray[np.float64], List[float]]] = None,
             y: Optional[Union[NDArray[np.float64], List[float]]] = None,
             pen: Optional[QPen] = None,
             brush: Optional[Any] = None,
             symbol: Optional[str] = None,
             symbolPen: Optional[QPen] = None,
             symbolBrush: Optional[Any] = None,
             symbolSize: Optional[int] = None,
             name: Optional[str] = None,
             fillLevel: Optional[float] = None,
             **kwargs: Any) -> PlotCurveItem: ...

    def addItem(self, item: Any) -> None: ...
    def removeItem(self, item: Any) -> None: ...
    def items(self) -> List[Any]: ...
    def setTitle(self, title: str, **kwargs) -> None: ...
    def setLabel(self, axis: str, text: str, **kwargs) -> None: ...
    def getAxis(self, axis: str) -> Any: ...
    def getPlotItem(self) -> Any: ...
    def viewRange(self) -> Tuple[Tuple[float, float], Tuple[float, float]]: ...
    def setXRange(self, min: float, max: float,
                  padding: float = 0) -> None: ...


class InfiniteLine:
    def setVisible(self, visible: bool) -> None: ...


class LinearRegionItem:
    ...


class ScatterPlotItem:
    ...


class ImageItem:
    ...


def mkPen(color: Optional[Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]] = None,
          width: Optional[int] = None,
          style: Optional[Any] = None,
          cosmetic: Optional[bool] = None,
          hsv: Optional[Any] = None,
          *args: Any,
          **kwargs: Any) -> QPen: ...
def setConfigOptions(antialias: Optional[bool] = None,
                     imageAxisOrder: Optional[str] = None,
                     background: Optional[str] = None,
                     foreground: Optional[str] = None,
                     useOpenGL: Optional[bool] = None,
                     leftButtonPan: Optional[bool] = None,
                     **kwargs: Any) -> None: ...

