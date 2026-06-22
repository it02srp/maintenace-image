import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, CATEGORIES

_client = genai.Client(api_key=GEMINI_API_KEY)

# ─── Prompt Template ──────────────────────────────────────────────────────────
def _build_prompt() -> str:
    cat_list = "\n".join(f"- {cat}: {desc}" for cat, desc in CATEGORIES.items())
    return f"""Kamu adalah sistem klasifikasi spare part industri.
Lihat gambar ini dengan teliti, lalu lakukan dua hal:

1. IDENTIFIKASI NAMA BARANG:
   - Jika ada ciri spesifik yang JELAS TERLIHAT di gambar (tulisan tipe, kode, brand, spesifikasi) → sebutkan secara spesifik.
     Contoh: "Inverter Omron MX2 2.2kW", "MCB Schneider 16A", "Grease Shell Alvania EP2"
   - Jika TIDAK ADA ciri spesifik yang terbaca / gambar tidak cukup jelas → sebutkan nama umum saja.
     Contoh: "Bearing", "Selang Angin", "Amplas", "Oli"
   - JANGAN mengarang tipe atau spesifikasi yang tidak terlihat di gambar.

2. TENTUKAN KATEGORI dari daftar berikut:
{cat_list}

Jawab dalam format JSON berikut (tanpa markdown, tanpa kode block):
{{
  "item_name": "<nama barang LENGKAP termasuk seri/model, contoh: Inverter Mitsubishi FR-A740-2.2K, MCB Schneider iC60N 16A>"
  "is_specific": <true jika spesifik teridentifikasi, false jika hanya general>,
  "category": "<nama kategori>",
  "confidence": "<HIGH|MEDIUM|LOW>",
  "score": <angka 0-100>,
  "reason": "<alasan singkat dalam bahasa Indonesia, sebutkan ciri apa yang terlihat atau mengapa hanya general>"
}}

Pilih SATU kategori yang paling cocok."""

# ─── Parse & Normalize Response ───────────────────────────────────────────────
def _parse_response(raw: str) -> dict:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

def _resolve_category(raw_category: str) -> str:
    cat = raw_category.upper()
    if cat in CATEGORIES:
        return cat
    for key in CATEGORIES:
        if key in cat:
            return key
    return list(CATEGORIES.keys())[0]

def _build_scores(category: str, score: float) -> dict:
    others = round((100 - score) / (len(CATEGORIES) - 1), 1)
    scores = {cat: others for cat in CATEGORIES}
    scores[category] = round(score, 1)
    return scores

# ─── Main Recognition Function ────────────────────────────────────────────────
def recognize_image(image_bytes: bytes) -> dict:
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[_build_prompt(), image_part],
    )

    result   = _parse_response(response.text.strip())
    category = _resolve_category(result.get("category", ""))
    score    = float(result.get("score", 50))

    return {
        'item_name':           result.get("item_name", category),
        'is_specific':         result.get("is_specific", False),
        'category':            category,
        'confidence':          result.get("confidence", "MEDIUM"),
        'score':               round(score, 1),
        'scores_per_category': _build_scores(category, score),
        'reason':              result.get("reason", ""),
        'item_description':    CATEGORIES[category],
    }