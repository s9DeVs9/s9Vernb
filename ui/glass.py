"""
Glass blur effect for S9Checker.
Captures the desktop behind the window, applies Gaussian blur,
and returns a dark-tinted PhotoImage for use as Canvas background.
"""

import logging

logger = logging.getLogger("S9Checker")


def capture_desktop_blur(root, radius=25, tint=0.12):
    """
    Capture the desktop area behind the window, blur it, and apply a dark tint.

    Args:
        root: The tkinter Tk root window
        radius: Gaussian blur radius (higher = more blur)
        tint: Dark tint intensity (0.0 = black, 1.0 = original)

    Returns:
        PIL ImageTk.PhotoImage or None on failure
    """
    try:
        from PIL import ImageGrab, ImageFilter, ImageEnhance, ImageTk
    except ImportError:
        logger.warning("Pillow not installed, glass effect disabled")
        return None

    try:
        root.update_idletasks()

        # Get window position and size
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()

        if w < 100 or h < 100:
            return None

        # Capture the desktop area behind our window
        img = ImageGrab.grab((x, y, x + w, y + h))

        # Apply heavy Gaussian blur
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))

        # Darken the image to create a dark glass overlay
        img = ImageEnhance.Brightness(img).enhance(tint)

        # Slight desaturation for a cool frosted look
        img = ImageEnhance.Color(img).enhance(0.6)

        # Convert to PhotoImage
        return ImageTk.PhotoImage(img)

    except Exception as e:
        logger.warning(f"Glass capture failed: {e}")
        return None
