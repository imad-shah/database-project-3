from io import BytesIO

from PIL import Image, ImageDraw

SIZE = (640, 420)
SKY = (176, 214, 236)
GRASS = (112, 160, 92)
ROOF = (84, 62, 56)
WINDOW = (232, 240, 196)
DOOR = (96, 58, 40)
TRIM = (245, 243, 236)


def draw_house(wall: tuple[int, int, int], wings: int) -> bytes:
    image = Image.new("RGB", SIZE, SKY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 300, 640, 420), fill=GRASS)
    for wing in range(wings):
        left = 60 + wing * 180
        draw.rectangle((left, 170, left + 200, 330), fill=wall, outline=TRIM, width=3)
        draw.polygon([(left - 20, 170), (left + 100, 80), (left + 220, 170)], fill=ROOF)
        draw.rectangle(
            (left + 30, 200, left + 80, 250), fill=WINDOW, outline=TRIM, width=3
        )
        draw.rectangle(
            (left + 120, 200, left + 170, 250), fill=WINDOW, outline=TRIM, width=3
        )
    draw.rectangle((140, 260, 185, 330), fill=DOOR)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
