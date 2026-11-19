import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from PIL import Image

assets_dir = Path("report_assets")
assets_dir.mkdir(exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Figure 3.1: Inventory Data Processing and Pre-processing Workflow
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 5)
ax.axis('off')

# Box styles
def draw_box(ax, x, y, w, h, title, subtitle, color, text_color='#FFFFFF'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                                 facecolor=color, edgecolor='#0F172A', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h*0.65, title, ha='center', va='center', fontsize=11, fontweight='bold', color=text_color)
    ax.text(x + w/2, y + h*0.3, subtitle, ha='center', va='center', fontsize=8.5, color=text_color)

def draw_arrow(ax, x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", lw=2, color='#028090'))

draw_box(ax, 0.4, 1.8, 1.8, 1.4, "Raw Data Ingestion", "Products, Suppliers\nSales, Stock Records", "#05668D")
draw_arrow(ax, 2.3, 2.5, 2.9, 2.5)

draw_box(ax, 3.0, 1.8, 1.8, 1.4, "Validation & Cleaning", "Schema Enforcement\nMissing Value Imputation", "#028090")
draw_arrow(ax, 4.9, 2.5, 5.5, 2.5)

draw_box(ax, 5.6, 1.8, 1.8, 1.4, "Feature Engineering", "Expiry Days Delta\nStock Margin & Turn Ratios", "#00A896")
draw_arrow(ax, 7.5, 2.5, 8.1, 2.5)

draw_box(ax, 8.2, 1.8, 1.5, 1.4, "Analytical Engine", "BI KPIs, Alerts &\nVisual Dashboard", "#52B788")

ax.set_title("Figure 3.1: Inventory Data Collection and Pre-processing Workflow", fontsize=12, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig("report_assets/fig3_1_workflow.png", dpi=300)
plt.close()
print("Saved fig3_1_workflow.png")

# -----------------------------------------------------------------------------
# 2. Figure 3.2: StorePRO System Architecture
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
ax.axis('off')

# Layer 1: Data Storage
rect1 = patches.FancyBboxPatch((0.5, 0.5), 9.0, 1.2, boxstyle="round,pad=0.08,rounding_size=0.1",
                              facecolor="#E0F7FA", edgecolor="#028090", linewidth=1.5)
ax.add_patch(rect1)
ax.text(5.0, 1.2, "DATA PERSISTENCE & STORAGE LAYER", ha='center', fontsize=10, fontweight='bold', color="#05668D")
ax.text(5.0, 0.8, "Atomic CSV Engine (.tmp + replace) • SQLite Ready DAO • Automated ZIP Backup Archives", ha='center', fontsize=8.5, color="#1D3557")

# Layer 2: Business Logic & Analytics
rect2 = patches.FancyBboxPatch((0.5, 2.2), 9.0, 1.6, boxstyle="round,pad=0.08,rounding_size=0.1",
                              facecolor="#CAF0F8", edgecolor="#00A896", linewidth=1.5)
ax.add_patch(rect2)
ax.text(5.0, 3.3, "BUSINESS LOGIC & DATA SCIENCE CORE", ha='center', fontsize=10, fontweight='bold', color="#0077B6")
ax.text(5.0, 2.9, "Pandas & NumPy Vectorized Aggregation • Expiry Classification Algorithm (4 Tiers)", ha='center', fontsize=8.5, color="#1D3557")
ax.text(5.0, 2.5, "Stock Reorder Level Guard • Low-Stock Notifications & WhatsApp / SMS Dispatch", ha='center', fontsize=8.5, color="#1D3557")

# Layer 3: Presentation Layer
rect3 = patches.FancyBboxPatch((0.5, 4.3), 9.0, 1.8, boxstyle="round,pad=0.08,rounding_size=0.1",
                              facecolor="#D8F3DC", edgecolor="#2D6A4F", linewidth=1.5)
ax.add_patch(rect3)
ax.text(5.0, 5.6, "PRESENTATION & USER EXPERIENCE LAYER", ha='center', fontsize=10, fontweight='bold', color="#2D6A4F")
ax.text(5.0, 5.1, "Streamlit Web Portal (Port 8503) & Native Tkinter Desktop POS Application", ha='center', fontsize=8.5, color="#1D3557")
ax.text(5.0, 4.7, "POS Cashier Checkout • Product CRUD • Matplotlib Trend Visualizations • Audit History", ha='center', fontsize=8.5, color="#1D3557")

# Connecting Arrows
ax.annotate('', xy=(5.0, 2.2), xytext=(5.0, 1.7), arrowprops=dict(arrowstyle="<->", lw=2, color='#028090'))
ax.annotate('', xy=(5.0, 4.3), xytext=(5.0, 3.8), arrowprops=dict(arrowstyle="<->", lw=2, color='#028090'))

ax.set_title("Figure 3.2: StorePRO Multi-Tier System Architecture", fontsize=12, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig("report_assets/fig3_2_architecture.png", dpi=300)
plt.close()
print("Saved fig3_2_architecture.png")

# -----------------------------------------------------------------------------
# 3. Figure 3.3: Dashboard & POS Modules
# -----------------------------------------------------------------------------
src_img = Path("store_management_system/assets/chart_dashboard_sales_trend.png")
if src_img.exists():
    img1 = Image.open(src_img)
    img2 = Image.open("store_management_system/assets/chart_dashboard_category_inventory.png")
    
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)
    axes[0].imshow(img1)
    axes[0].axis('off')
    axes[0].set_title("(a) 30-Day Sales Revenue Trend", fontsize=10, fontweight='bold')
    
    axes[1].imshow(img2)
    axes[1].axis('off')
    axes[1].set_title("(b) Category Inventory Distribution", fontsize=10, fontweight='bold')
    
    plt.suptitle("Figure 3.3: StorePRO Dashboard & Analytics Output Visualizations", fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig("report_assets/fig3_3_dashboard.png", dpi=300)
    plt.close()
    print("Saved fig3_3_dashboard.png")

# -----------------------------------------------------------------------------
# 4. Figure 3.4: Business Intelligence Analytics
# -----------------------------------------------------------------------------
src_img3 = Path("store_management_system/assets/chart_analytics_inventory_health.png")
src_img4 = Path("store_management_system/assets/chart_analytics_top_ranking.png")
if src_img3.exists() and src_img4.exists():
    img3 = Image.open(src_img3)
    img4 = Image.open(src_img4)
    
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)
    axes[0].imshow(img3)
    axes[0].axis('off')
    axes[0].set_title("(a) Inventory Health & Stock Turn Ratio", fontsize=10, fontweight='bold')
    
    axes[1].imshow(img4)
    axes[1].axis('off')
    axes[1].set_title("(b) Top Selling Product Demand Ranking", fontsize=10, fontweight='bold')
    
    plt.suptitle("Figure 3.4: Business Intelligence & Demand Forecasting Indicators", fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig("report_assets/fig3_4_analytics.png", dpi=300)
    plt.close()
    print("Saved fig3_4_analytics.png")
