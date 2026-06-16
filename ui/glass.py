
import logging

logger = logging.getLogger("S9Checker")


def capture_desktop_blur(root, radius=25, tint=0.12):
    try:
        from PIL import ImageGrab, ImageFilter, ImageEnhance, ImageTk
    except ImportError:
        logger.warning("Pillow not installed, glass effect disabled")
        return None

    try:
        root.update_idletasks()

        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()

        if w < 100 or h < 100:
            return None

        img = ImageGrab.grab((x, y, x + w, y + h))

        img = img.filter(ImageFilter.GaussianBlur(radius=radius))

        img = ImageEnhance.Brightness(img).enhance(tint)

        img = ImageEnhance.Color(img).enhance(0.6)

        return ImageTk.PhotoImage(img)

    except Exception as e:
        logger.warning(f"Glass capture failed: {e}")
        return None
