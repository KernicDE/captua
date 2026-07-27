"""Generate the neutral mock app window used as the demo screenshot base.

Writes /tmp/demo-app.png — a synthetic music-player window (no real screen
content, so README assets never leak private data). Used by record_demo.py.
"""

from PIL import Image, ImageDraw, ImageFont

W, H = 880, 540
img = Image.new("RGB", (W, H), "#1B1B1F")
d = ImageDraw.Draw(img)
reg = "/usr/share/fonts/noto/NotoSans-Regular.ttf"
bold = "/usr/share/fonts/noto/NotoSans-Bold.ttf"
f10 = ImageFont.truetype(reg, 13)
f12 = ImageFont.truetype(reg, 15)
f14 = ImageFont.truetype(bold, 17)
f18 = ImageFont.truetype(bold, 24)

# Sidebar
d.rectangle([0, 0, 210, H], fill="#121214")
d.text((24, 24), "streamd", font=f18, fill="#E8E8E8")
items = ["Home", "Search", "Your Library", "Playlists", "Settings"]
y = 90
for it in items:
    if it == "Your Library":
        d.rounded_rectangle([12, y - 10, 198, y + 24], 8, fill="#2A2A33")
        d.text((24, y), it, font=f12, fill="#FFFFFF")
    else:
        d.text((24, y), it, font=f12, fill="#9A9AA2")
    y += 48

# Main area
d.text((248, 28), "Your Library", font=f18, fill="#E8E8E8")

# Album art placeholder (gradient)
for i in range(120):
    c = (70 + i, 40 + i // 3, 120 - i // 2)
    d.line([(248, 90 + i), (368, 90 + i)], fill=c)
d.text((248 + 34, 90 + 48), "ART", font=f18, fill="#E8E8E8")

# Track info
d.text((392, 96), "Midnight Run", font=f14, fill="#FFFFFF")
d.text((392, 122), "Neon Coastline", font=f10, fill="#9A9AA2")
d.text((392, 150), "2024 · 3:42", font=f10, fill="#9A9AA2")

# Progress bar
d.rounded_rectangle([248, 210, 830, 216], 3, fill="#3A3A42")
d.rounded_rectangle([248, 210, 560, 216], 3, fill="#FF5D62")
d.ellipse([552, 206, 568, 222], fill="#FFFFFF")

# Track rows
rows = [
    ("1", "Midnight Run", "Neon Coastline", "3:42"),
    ("2", "Solar Drift", "Neon Coastline", "4:05"),
    ("3", "Static Bloom", "Neon Coastline", "2:58"),
    ("4", "Glass Harbour", "Neon Coastline", "3:21"),
]
y = 250
for n, t, a, dur in rows:
    d.text((248, y), n, font=f10, fill="#9A9AA2")
    d.text((280, y), t, font=f12, fill="#E8E8E8")
    d.text((560, y), a, font=f10, fill="#9A9AA2")
    d.text((800, y), dur, font=f10, fill="#9A9AA2")
    y += 40

# API token row (blurred in the demo)
d.rounded_rectangle([248, 428, 830, 470], 8, fill="#232329")
d.text((264, 440), "API Token:", font=f12, fill="#9A9AA2")
d.text((370, 440), "sk-live-9f3k-x71q-mz82-pq44", font=f12, fill="#E8E8E8")

# Buttons
d.rounded_rectangle([620, 490, 710, 524], 8, fill="#2A2A33")
d.text((644, 498), "Revoke", font=f12, fill="#E8E8E8")
d.rounded_rectangle([730, 490, 830, 524], 8, fill="#FF5D62")
d.text((756, 498), "Copy", font=f12, fill="#FFFFFF")

img.save("/tmp/demo-app.png")
print("saved /tmp/demo-app.png", img.size)
