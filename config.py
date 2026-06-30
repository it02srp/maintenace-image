import os
from dotenv import load_dotenv

load_dotenv()

# ─── Gemini ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.5-flash-lite"

# ─── API Security ─────────────────────────────────────────────────────────────
X_API_KEY = os.environ.get("X_API_KEY", "")

# ─── Upload ───────────────────────────────────────────────────────────────────
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# ─── Kategori Spare Part ──────────────────────────────────────────────────────
CATEGORIES = {
    'BEARINGS':    'Bearing / bantalan mekanis',
    'LUBRICATION': 'Pelumas: Oli & Grease',
    'PENUNJANG':   'Bahan penunjang (amplas, lem, kawat las, sikat)',
    'AIRMATIC':    'Komponen pneumatik (fitting, coupler selang angin)',
    'ELECTRICAL':  'Komponen listrik (MCB, kabel, lampu, fuse)',
}