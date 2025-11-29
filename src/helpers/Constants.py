from PyQt5.QtGui import QColor

# WARN: must use double quotes around version number (see build-and-release.yaml)
__version__ = "1.0.6"

BACKGROUND = QColor("#4a4e69")
ACTIVE = QColor("#808080")
SEIZURE = QColor("#0096c7")
SE = QColor("#ffb703")
PROPAGATION = QColor("#a8dadc")

HOVER = QColor("#00ff00")
SELECTED = QColor("#008000")
PLOTTED = QColor("#ef233c")

SIZE = 30
MARKER = "s"

STROKE_WIDTH = 3

GRAPH_DOWNSAMPLE = 5_000

TOTAL_POINTS = 20_000

CELL_SIZE = 60  # micrometers

MAC = "darwin"
WIN = "win32"
FONT_FILE = "GeistMonoNerdFontMono-Regular.otf"
FONT_FAMILY = "GeistMono Nerd Font Mono"
SCREEN_DIAGONAL_THRESHOLD = 13
SMALL_FONT_SIZE = 9
LARGE_FONT_SIZE = 13
