"""
Graphic Asset Generator for Supermarket Themed Store Management System.
Generates polished, high-resolution vector-style supermarket illustrations
for Screen 1 (Home Storefront), Screen 2 (Shoppers Login), and Screen 3 (Aisle Hub).
Faithfully matches the reference design with high-quality gradients, crisp details,
mascot character with 'Yeah!' neon splash, and clear perspective.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math

ASSETS_DIR = Path(__file__).resolve().parent

def get_font(size: int, bold: bool = False):
    """Attempts to load a standard system TrueType font, falling back to default."""
    font_names = [
        "/System/Library/Fonts/SFProText-Bold.otf" if bold else "/System/Library/Fonts/SFProText-Regular.otf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf"
    ]
    for font_path in font_names:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

# =============================================================================
# SCREEN 1: SUPERMARKET STOREFRONT
# =============================================================================

def generate_storefront_image(filepath: Path, width: int = 1280, height: int = 720):
    """Screen 1: Beautiful Supermarket Storefront with sky, city skyline, trees, and shopping carts."""
    img = Image.new("RGBA", (width, height), "#E0F7FA")
    draw = ImageDraw.Draw(img)

    # 1. Sky Gradient (Light Cyan / Sky Blue)
    sky_h = int(height * 0.52)
    for y in range(sky_h):
        ratio = y / sky_h
        r = int(140 + (224 - 140) * ratio)
        g = int(215 + (247 - 215) * ratio)
        b = int(248 + (250 - 248) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Bright Sun with Soft Glow
    sun_x, sun_y, sun_r = int(width * 0.45), int(height * 0.12), 46
    for gr in range(sun_r + 16, sun_r, -2):
        alpha = int(80 * (1 - (gr - sun_r) / 16))
        draw.ellipse([sun_x - gr, sun_y - gr, sun_x + gr, sun_y + gr], fill=(255, 235, 140, alpha))
    draw.ellipse([sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r], fill="#FFD166")
    draw.ellipse([sun_x - sun_r + 5, sun_y - sun_r + 5, sun_x + sun_r - 5, sun_y + sun_r - 5], fill="#FFE382")

    # Fluffy Cartoon Clouds
    cloud_clusters = [
        (160, 70, 0.9), (240, 60, 1.1), (320, 75, 0.8),
        (840, 80, 1.0), (920, 65, 1.2), (1000, 85, 0.85)
    ]
    for cx, cy, scale in cloud_clusters:
        w_c = int(45 * scale)
        h_c = int(26 * scale)
        draw.ellipse([cx - w_c, cy - h_c, cx + w_c, cy + h_c], fill=(255, 255, 255, 235))
        draw.ellipse([cx - int(w_c*0.6), cy - int(h_c*1.3), cx + int(w_c*0.6), cy + int(h_c*0.5)], fill=(255, 255, 255, 245))

    # 2. Modern City Skyline Buildings (Pastel Purples, Teals & Cyans)
    buildings = [
        (50, 150, 65, "#B8C0E0"), (125, 210, 80, "#A0C4E2"), (215, 175, 70, "#C5D8E8"),
        (295, 195, 85, "#B0CCE1"), (740, 210, 80, "#B8C0E0"), (830, 185, 75, "#C0D6E4"),
        (915, 230, 95, "#A8C5DA"), (1020, 160, 75, "#C8DCE8"), (1105, 200, 85, "#B4CBE0")
    ]
    for bx, bh, bw, bcolor in buildings:
        by = sky_h - bh
        draw.rectangle([bx, by, bx + bw, sky_h], fill=bcolor)
        # Windows grid
        for wy in range(by + 12, sky_h - 15, 18):
            for wx in range(bx + 8, bx + bw - 10, 14):
                draw.rectangle([wx, wy, wx + 7, wy + 10], fill=(255, 255, 255, 190))

    # 3. Green Lawn & Paved Walkway
    lawn_y = sky_h
    draw.rectangle([0, lawn_y, width, height], fill="#52B788")
    draw.rectangle([0, lawn_y + 35, width, height], fill="#40916C")
    # Paved supermarket entrance plaza
    draw_rounded_rect(draw, [int(width * 0.20), lawn_y + 8, int(width * 0.80), height], radius=16, fill="#D8F3DC")

    # 4. Supermarket Building (White structure, blue marquee)
    sb_w = int(width * 0.54)
    sb_h = int(height * 0.38)
    sb_x = (width - sb_w) // 2
    sb_y = lawn_y - sb_h + 25

    # Building base shadow & walls
    draw_rounded_rect(draw, [sb_x - 4, sb_y - 4, sb_x + sb_w + 4, sb_y + sb_h + 4], radius=14, fill="#1B4332")
    draw_rounded_rect(draw, [sb_x, sb_y, sb_x + sb_w, sb_y + sb_h], radius=10, fill="#FFFFFF")

    # Navy Header Marquee
    header_h = 56
    draw_rounded_rect(draw, [sb_x + 8, sb_y + 8, sb_x + sb_w - 8, sb_y + 8 + header_h], radius=8, fill="#0F4C81")

    # "SUPERMARKET" Sign Board Text
    font_sign = get_font(26, bold=True)
    sign_text = "S U P E R M A R K E T"
    draw.text((width // 2, sb_y + 36), sign_text, fill="#FFFFFF", font=font_sign, anchor="mm")

    # Large Modern Glass Display Windows
    win_y = sb_y + header_h + 20
    win_h = sb_h - header_h - 40
    # Left Window
    draw_rounded_rect(draw, [sb_x + 22, win_y, sb_x + int(sb_w * 0.36), win_y + win_h], radius=6, fill="#E0F7FA", outline="#90E0EF", width=3)
    # Right Window
    draw_rounded_rect(draw, [sb_x + int(sb_w * 0.64), win_y, sb_x + sb_w - 22, win_y + win_h], radius=6, fill="#E0F7FA", outline="#90E0EF", width=3)

    # Window Reflection Lines
    draw.line([(sb_x + 40, win_y + 15), (sb_x + int(sb_w * 0.26), win_y + win_h - 20)], fill=(255, 255, 255, 200), width=6)
    draw.line([(sb_x + int(sb_w * 0.70), win_y + 15), (sb_x + sb_w - 45, win_y + win_h - 20)], fill=(255, 255, 255, 200), width=6)

    # Central Glass Entrance Door Frame
    door_w = int(sb_w * 0.24)
    door_x = (width - door_w) // 2
    draw_rounded_rect(draw, [door_x, win_y - 4, door_x + door_w, win_y + win_h + 6], radius=6, fill="#0077B6")
    draw_rounded_rect(draw, [door_x + 5, win_y, door_x + door_w - 5, win_y + win_h + 4], radius=4, fill="#CAF0F8")
    draw.line([(door_x + door_w // 2, win_y), (door_x + door_w // 2, win_y + win_h + 4)], fill="#0077B6", width=3)

    # 5. Pine Tree on Left & Leafy Tree on Right (matching reference image)
    # Left Pine Tree
    p_x = sb_x - 65
    draw.polygon([(p_x, lawn_y - 120), (p_x - 55, lawn_y + 15), (p_x + 55, lawn_y + 15)], fill="#2D6A4F")
    draw.polygon([(p_x, lawn_y - 160), (p_x - 42, lawn_y - 40), (p_x + 42, lawn_y - 40)], fill="#40916C")
    draw.polygon([(p_x, lawn_y - 195), (p_x - 30, lawn_y - 95), (p_x + 30, lawn_y - 95)], fill="#52B788")

    # Right Round Tree
    r_x = sb_x + sb_w + 65
    draw.rectangle([r_x - 8, lawn_y - 20, r_x + 8, lawn_y + 15], fill="#6C584C")
    draw.ellipse([r_x - 50, lawn_y - 145, r_x + 50, lawn_y - 15], fill="#52B788")
    draw.ellipse([r_x - 40, lawn_y - 165, r_x + 40, lawn_y - 45], fill="#74C69D")

    # 6. Shopping Carts near Entrance
    for cx in [door_x - 60, door_x + door_w + 20]:
        draw_rounded_rect(draw, [cx, win_y + win_h - 32, cx + 42, win_y + win_h + 6], radius=4, fill="#00B4D8", outline="#0077B6", width=2)
        # Handle & wheels
        draw.line([(cx + 42, win_y + win_h - 32), (cx + 48, win_y + win_h - 42)], fill="#EF476F", width=3)
        draw.ellipse([cx + 6, win_y + win_h + 6, cx + 15, win_y + win_h + 15], fill="#1B4332")
        draw.ellipse([cx + 28, win_y + win_h + 6, cx + 37, win_y + win_h + 15], fill="#1B4332")

    # 7. Title in Top-Left Sky (matching reference image)
    font_title1 = get_font(24, bold=True)
    font_title2 = get_font(22, bold=True)
    draw.text((45, 30), "CRUD OPERATIONS ON STORE", fill="#0A3663", font=font_title1)
    draw.text((45, 58), "MANAGEMENT SYSTEM", fill="#0A3663", font=font_title2)

    img.save(filepath, "PNG")
    print(f"Storefront image successfully saved: {filepath}")

# =============================================================================
# SCREEN 2: SHOPPERS LOGIN / REGISTER
# =============================================================================

def generate_shoppers_login_image(filepath: Path, width: int = 1280, height: int = 720):
    """Screen 2: Shopping & Supermarket Themed Background for Login / Register."""
    # Warm/Cool Grey backdrop matching reference
    img = Image.new("RGBA", (width, height), "#C8D1D5")
    draw = ImageDraw.Draw(img)

    # Subtle modern gradient
    for y in range(height):
        r = int(195 + (218 - 195) * (y / height))
        g = int(205 + (224 - 205) * (y / height))
        b = int(212 + (228 - 212) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Ground floor line
    ground_y = int(height * 0.78)
    draw.rectangle([0, ground_y, width, height], fill="#B0BEC5")

    # 1. Left side: Supermarket Awning & Shop front
    shop_x = 100
    shop_y = int(height * 0.28)
    shop_w = 460
    shop_h = ground_y - shop_y

    draw_rounded_rect(draw, [shop_x, shop_y, shop_x + shop_w, ground_y], radius=12, fill="#FFFFFF", outline="#CFD8DC", width=2)

    # Red & White Striped Awning
    awning_h = 50
    awning_y = shop_y - 20
    stripes = 10
    sw = shop_w // stripes
    for i in range(stripes):
        color = "#E63946" if i % 2 == 0 else "#FFFFFF"
        draw_rounded_rect(draw, [shop_x + i * sw, awning_y, shop_x + (i + 1) * sw, awning_y + awning_h], radius=6, fill=color)

    # Shop Windows with Groceries
    win_box = [shop_x + 30, shop_y + 45, shop_x + shop_w - 30, shop_y + 200]
    draw_rounded_rect(draw, win_box, radius=8, fill="#E0F7FA")
    for sy in [shop_y + 90, shop_y + 145]:
        draw.line([(shop_x + 40, sy), (shop_x + shop_w - 40, sy)], fill="#A8DADC", width=4)
        for gx in range(shop_x + 50, shop_x + shop_w - 55, 36):
            c = ["#FFB703", "#FB8500", "#06D6A0", "#118AB2", "#E63946"][(gx // 30) % 5]
            draw_rounded_rect(draw, [gx, sy - 20, gx + 20, sy], radius=3, fill=c)

    # 2. Right side: Modern Teal Supermarket Entrance Structure (matching reference)
    right_x = int(width * 0.64)
    right_y = int(height * 0.18)
    right_w = 260
    right_h = ground_y - right_y

    # Modern Teal Columns & Header
    draw_rounded_rect(draw, [right_x, right_y, right_x + right_w, ground_y], radius=10, fill="#2A9D8F")
    draw_rounded_rect(draw, [right_x + 20, right_y + 35, right_x + int(right_w * 0.45), ground_y - 10], radius=6, fill="#E0F7FA")
    draw_rounded_rect(draw, [right_x + int(right_w * 0.52), right_y + 35, right_x + right_w - 20, ground_y - 10], radius=6, fill="#E0F7FA")

    # Decorative Plant leaves on right
    plant_x = right_x + right_w + 20
    draw.ellipse([plant_x, ground_y - 160, plant_x + 45, ground_y], fill="#52B788")
    draw.ellipse([plant_x + 20, ground_y - 200, plant_x + 65, ground_y - 20], fill="#40916C")

    # 3. Stylized Shoppers with Colorful Bags (matching reference art)
    # Shopper 1: Woman on left in teal coat walking left
    w1_x = shop_x - 30
    w1_y = ground_y - 140
    draw.ellipse([w1_x + 10, w1_y, w1_x + 28, w1_y + 20], fill="#F4A261") # head
    draw.polygon([(w1_x + 5, w1_y + 20), (w1_x + 35, w1_y + 20), (w1_x + 42, w1_y + 80), (w1_x, w1_y + 80)], fill="#00B4D8") # coat
    draw.line([(w1_x + 12, w1_y + 80), (w1_x + 4, w1_y + 130)], fill="#1D3557", width=4) # legs
    draw.line([(w1_x + 25, w1_y + 80), (w1_x + 36, w1_y + 130)], fill="#1D3557", width=4)
    draw_rounded_rect(draw, [w1_x - 12, w1_y + 50, w1_x + 6, w1_y + 78], radius=3, fill="#E76F51") # bag

    # Shopper 2: Man in black walking right
    m1_x = shop_x + 140
    m1_y = ground_y - 150
    draw.ellipse([m1_x + 10, m1_y, m1_x + 28, m1_y + 20], fill="#E76F51")
    draw_rounded_rect(draw, [m1_x + 6, m1_y + 20, m1_x + 32, m1_y + 85], radius=6, fill="#264653")
    draw.line([(m1_x + 12, m1_y + 85), (m1_x + 2, m1_y + 140)], fill="#1D3557", width=5)
    draw.line([(m1_x + 26, m1_y + 85), (m1_x + 40, m1_y + 140)], fill="#1D3557", width=5)
    draw_rounded_rect(draw, [m1_x + 32, m1_y + 55, m1_x + 52, m1_y + 85], radius=3, fill="#2A9D8F")

    # Shopper 3 & 4: Shoppers near right entrance
    m2_x = right_x - 80
    m2_y = ground_y - 145
    draw.ellipse([m2_x + 10, m2_y, m2_x + 28, m2_y + 20], fill="#F4A261")
    draw_rounded_rect(draw, [m2_x + 6, m2_y + 20, m2_x + 32, m2_y + 85], radius=6, fill="#0077B6")
    draw.line([(m2_x + 14, m2_y + 85), (m2_x + 14, m2_y + 135)], fill="#1D3557", width=4)
    draw.line([(m2_x + 24, m2_y + 85), (m2_x + 24, m2_y + 135)], fill="#1D3557", width=4)
    draw_rounded_rect(draw, [m2_x + 32, m2_y + 60, m2_x + 48, m2_y + 88], radius=3, fill="#E9C46A")

    # Shopper 5: Shopper in orange jacket on far right
    m3_x = right_x + 120
    m3_y = ground_y - 145
    draw.ellipse([m3_x + 10, m3_y, m3_x + 28, m3_y + 20], fill="#F4A261")
    draw_rounded_rect(draw, [m3_x + 6, m3_y + 20, m3_x + 32, m3_y + 85], radius=6, fill="#E76F51")
    draw.line([(m3_x + 14, m3_y + 85), (m3_x + 6, m3_y + 135)], fill="#1D3557", width=4)
    draw.line([(m3_x + 24, m3_y + 85), (m3_x + 32, m3_y + 135)], fill="#1D3557", width=4)
    draw_rounded_rect(draw, [m3_x - 12, m3_y + 60, m3_x + 4, m3_y + 88], radius=3, fill="#2A9D8F")

    img.save(filepath, "PNG")
    print(f"Shoppers login image successfully saved: {filepath}")

# =============================================================================
# SCREEN 3: AISLE HUB WITH MASCOT & "YEAH!" GRAFFITI
# =============================================================================

def generate_aisle_hub_image(filepath: Path, width: int = 1280, height: int = 720):
    """Screen 3: Supermarket Aisle Interior with Wooden Counter and Smiling Mascot."""
    img = Image.new("RGBA", (width, height), "#FFF3E0")
    draw = ImageDraw.Draw(img)

    # 1. Background: Supermarket Aisle with shelves in perspective
    for y in range(int(height * 0.65)):
        ratio = y / (height * 0.65)
        r = int(255 - ratio * 30)
        g = int(246 - ratio * 42)
        b = int(230 - ratio * 55)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Aisle ceiling perspective lights (overhead glow)
    draw.polygon([(int(width * 0.38), 0), (int(width * 0.62), 0), (int(width * 0.54), 160), (int(width * 0.46), 160)], fill=(255, 255, 255, 220))

    # Shelves on Left side (Warm tones, grocery items)
    shelf_colors = ["#E76F51", "#F4A261", "#E9C46A", "#2A9D8F", "#264653", "#0077B6", "#EF476F", "#06D6A0"]
    for row_idx, sy in enumerate(range(50, int(height * 0.62), 52)):
        draw.line([(0, sy), (int(width * 0.38), sy + 30)], fill="#D4A373", width=6)
        for item_x in range(15, int(width * 0.35), 30):
            c = shelf_colors[(item_x // 25 + row_idx) % len(shelf_colors)]
            draw_rounded_rect(draw, [item_x, sy - 35, item_x + 22, sy], radius=3, fill=c)

    # Shelves on Right side
    for row_idx, sy in enumerate(range(50, int(height * 0.62), 52)):
        draw.line([(width, sy), (int(width * 0.62), sy + 30)], fill="#D4A373", width=6)
        for item_x in range(width - 25, int(width * 0.65), -30):
            c = shelf_colors[(item_x // 25 + row_idx * 2) % len(shelf_colors)]
            draw_rounded_rect(draw, [item_x - 22, sy - 35, item_x, sy], radius=3, fill=c)

    # Soft Gaussian blur for authentic depth-of-field effect
    blurred_bg = img.filter(ImageFilter.GaussianBlur(radius=3.0))
    img = blurred_bg
    draw = ImageDraw.Draw(img)

    # 2. Foreground: Polished Wooden Store Counter Top (matching reference image)
    counter_y = int(height * 0.64)
    # Countertop polished rim
    draw.rectangle([0, counter_y - 14, width, counter_y], fill="#E5BA73")
    draw.line([(0, counter_y - 14), (width, counter_y - 14)], fill="#FAF8F1", width=3)
    # Wood planks
    draw.rectangle([0, counter_y, width, height], fill="#C58940")
    for cy in range(counter_y, height, 22):
        draw.line([(0, cy), (width, cy)], fill="#A77B37", width=2)

    # 3. Mascot Character on the Right (sitting on wooden counter)
    mascot_cx = int(width * 0.82)
    mascot_cy = int(height * 0.58)

    # "Yeah!" Graffiti Splash above Mascot (matching reference!)
    font_yeah = get_font(34, bold=True)
    # Pink / Magenta neon lettering
    draw.text((mascot_cx - 50, mascot_cy - 165), "Yeah!", fill="#FF4081", font=font_yeah)
    # Cyan neon sparkles / bursts
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        px1 = int(mascot_cx - 20 + 40 * math.cos(rad))
        py1 = int(mascot_cy - 150 + 25 * math.sin(rad))
        px2 = int(mascot_cx - 20 + 55 * math.cos(rad))
        py2 = int(mascot_cy - 150 + 35 * math.sin(rad))
        draw.line([(px1, py1), (px2, py2)], fill="#00E5FF", width=3)

    # Mascot Body (Red Cup / Bucket)
    cup_pts = [
        (mascot_cx - 65, mascot_cy - 55),
        (mascot_cx + 65, mascot_cy - 55),
        (mascot_cx + 50, mascot_cy + 55),
        (mascot_cx - 50, mascot_cy + 55),
    ]
    draw.polygon(cup_pts, fill="#E63946")

    # Cup rim
    draw_rounded_rect(draw, [mascot_cx - 70, mascot_cy - 62, mascot_cx + 70, mascot_cy - 48], radius=6, fill="#FFFFFF")

    # White Swirl Cream Topping
    draw.ellipse([mascot_cx - 55, mascot_cy - 105, mascot_cx + 55, mascot_cy - 52], fill="#FFFFFF")
    draw.ellipse([mascot_cx - 35, mascot_cy - 125, mascot_cx + 35, mascot_cy - 82], fill="#FFFFFF")
    draw.ellipse([mascot_cx - 15, mascot_cy - 140, mascot_cx + 15, mascot_cy - 110], fill="#FFFFFF")
    # Colorful Sprinkles
    draw.line([(mascot_cx - 22, mascot_cy - 90), (mascot_cx - 12, mascot_cy - 85)], fill="#06D6A0", width=4)
    draw.line([(mascot_cx + 15, mascot_cy - 100), (mascot_cx + 25, mascot_cy - 95)], fill="#FFD166", width=4)
    draw.line([(mascot_cx - 2, mascot_cy - 75), (mascot_cx + 8, mascot_cy - 70)], fill="#118AB2", width=4)

    # Big Turquoise Square Glasses
    glass_w, glass_h = 42, 32
    # Left Lens
    draw_rounded_rect(draw, [mascot_cx - 52, mascot_cy - 35, mascot_cx - 52 + glass_w, mascot_cy - 35 + glass_h], radius=5, fill="#00B4D8", outline="#03045E", width=4)
    # Right Lens
    draw_rounded_rect(draw, [mascot_cx + 10, mascot_cy - 35, mascot_cx + 10 + glass_w, mascot_cy - 35 + glass_h], radius=5, fill="#00B4D8", outline="#03045E", width=4)
    # Bridge
    draw.line([(mascot_cx - 10, mascot_cy - 20), (mascot_cx + 10, mascot_cy - 20)], fill="#03045E", width=5)
    # Pupils
    draw.ellipse([mascot_cx - 35, mascot_cy - 24, mascot_cx - 25, mascot_cy - 14], fill="#FFFFFF")
    draw.ellipse([mascot_cx + 27, mascot_cy - 24, mascot_cx + 37, mascot_cy - 14], fill="#FFFFFF")

    # Wide Happy Grin with Teeth
    draw_rounded_rect(draw, [mascot_cx - 36, mascot_cy + 15, mascot_cx + 36, mascot_cy + 42], radius=8, fill="#03045E")
    draw_rounded_rect(draw, [mascot_cx - 32, mascot_cy + 18, mascot_cx + 32, mascot_cy + 38], radius=6, fill="#FFFFFF")
    # Teeth dividers
    for tx in [-16, 0, 16]:
        draw.line([(mascot_cx + tx, mascot_cy + 18), (mascot_cx + tx, mascot_cy + 38)], fill="#03045E", width=2)

    # Mascot Little Hands
    draw.ellipse([mascot_cx - 72, mascot_cy - 10, mascot_cx - 52, mascot_cy + 10], fill="#FFFFFF", outline="#03045E", width=3)
    draw.ellipse([mascot_cx + 52, mascot_cy - 10, mascot_cx + 72, mascot_cy + 10], fill="#FFFFFF", outline="#03045E", width=3)

    img.save(filepath, "PNG")
    print(f"Aisle hub image successfully saved: {filepath}")

def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    generate_storefront_image(ASSETS_DIR / "supermarket_front.png")
    generate_shoppers_login_image(ASSETS_DIR / "supermarket_shoppers.png")
    generate_aisle_hub_image(ASSETS_DIR / "supermarket_aisle_hub.png")
    print("All theme graphic illustrations successfully generated!")

if __name__ == "__main__":
    main()
