"""
Theme constants for S9Checker UI.
Glass dark theme - dark panels over blurred desktop background.
"""

# ---------------------------------------------------------------------------
# Color palette - Dark glass over blurred desktop
# ---------------------------------------------------------------------------
BG_DARK = "#0c0c0c"          # Sidebar (near-black)
BG_MAIN = "#111111"          # Page background (very dark)
BG_CARD = "#1a1a1a"          # Card background (dark gray)
BG_CARD_HOVER = "#242424"    # Card hover state
BORDER = "#333333"           # Subtle borders

ACCENT = "#ffffff"           # White - primary accent
GREEN = "#4ade80"            # Green - valid
RED = "#f87171"              # Red - invalid
ORANGE = "#fbbf24"           # Orange - warnings
PURPLE = "#c084fc"           # Purple - secondary

FG = "#ffffff"               # Primary text (white)
FG2 = "#666666"              # Secondary text (gray)
INPUT_BG = "#0d0d0d"         # Input fields

# Glass-specific
GLASS_ALPHA = 0.88           # Window translucency (1.0 = opaque)
GLASS_TINT = 0.12            # Desktop darken factor (lower = darker)
GLASS_BLUR_RADIUS = 25       # Gaussian blur radius

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT = ("Consolas", 10)
FONT_BOLD = ("Consolas", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUB = ("Consolas", 11, "bold")
FONT_MONO = ("Consolas", 9)
FONT_STAT = ("Segoe UI", 22, "bold")
FONT_STAT_LABEL = ("Consolas", 9)
FONT_SIDEBAR = ("Segoe UI", 16)
FONT_SIDEBAR_ACTIVE = ("Segoe UI", 16, "bold")

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
SIDEBAR_WIDTH = 60
WINDOW_WIDTH = 1050
WINDOW_HEIGHT = 700
WINDOW_MIN_W = 900
WINDOW_MIN_H = 600
TITLEBAR_HEIGHT = 36

# Card styling
CARD_CORNER_RADIUS = 6
CARD_BORDER_WIDTH = 1
CARD_PAD_X = 12
CARD_PAD_Y = 10
