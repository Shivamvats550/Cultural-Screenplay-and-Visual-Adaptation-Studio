from pathlib import Path
from PIL import Image, ImageDraw


def generate_mock_visual_card(output_path, title, subtitle, details):
  

    width, height = 1200, 800
    image = Image.new("RGB", (width, height), "#172033")
    draw = ImageDraw.Draw(image)

    draw.text((60, 50), title, fill="white")
    draw.text((60, 110), subtitle, fill="#b9c7e6")

    y = 200
    for item in details:
        draw.text((80, y), f"- {item}", fill="white")
        y += 45

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)



