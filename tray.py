import pystray
from PIL import Image, ImageDraw


def _make_icon() -> Image.Image:
    """Generate a simple grid icon programmatically — no image file needed."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = (80, 140, 255, 255)
    # Draw a 2x2 grid of rounded squares to represent window tiles
    padding, gap = 6, 6
    tile = (size - 2 * padding - gap) // 2
    for row in range(2):
        for col in range(2):
            x = padding + col * (tile + gap)
            y = padding + row * (tile + gap)
            draw.rounded_rectangle([x, y, x + tile, y + tile], radius=4, fill=color)
    return img


def create_tray(on_save, on_restore, on_toggle_autostart, on_quit) -> pystray.Icon:
    icon_image = _make_icon()

    menu = pystray.Menu(
        pystray.MenuItem("Save Layout", lambda: on_save()),
        pystray.MenuItem("Restore Layout", lambda: on_restore()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Toggle Auto-start", lambda: on_toggle_autostart()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda: on_quit()),
    )

    return pystray.Icon("WindowMemory", icon_image, "Window Memory", menu)
