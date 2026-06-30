from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import base64
from config import MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS, CATEGORIES, GEMINI_API_KEY, X_API_KEY
from prompt import recognize_image

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["20 per minute"],
    headers_enabled=True,  # kirim header X-RateLimit-* ke client
)

# ─── Auth ─────────────────────────────────────────────────────────────────────
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-KEY')
        if not X_API_KEY or key != X_API_KEY:
            return jsonify({'error': 'Unauthorized: X-API-KEY tidak valid'}), 401
        return f(*args, **kwargs)
    return decorated

# ─── Helpers ──────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_image_bytes(req) -> bytes:
    """Auto-detect: multipart file atau JSON base64."""
    if req.content_type and 'multipart/form-data' in req.content_type:
        if 'image' not in req.files or req.files['image'].filename == '':
            raise ValueError('Tidak ada file image')
        file = req.files['image']
        if not allowed_file(file.filename):
            raise ValueError(f'Format tidak didukung. Gunakan: {", ".join(ALLOWED_EXTENSIONS)}')
        return file.read()

    # JSON base64
    body = req.get_json(silent=True)
    if not body or 'image' not in body:
        raise ValueError('Field "image" (base64) tidak ditemukan')
    raw = body['image']
    if ',' in raw:
        raw = raw.split(',', 1)[1]
    return base64.b64decode(raw)

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({'error': 'Terlalu banyak request. Coba lagi dalam 1 menit.'}), 429

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'gemini_api_key': 'configured' if GEMINI_API_KEY else 'missing',
        'x_api_key':      'configured' if X_API_KEY else 'missing',
    })

@app.route('/api/recognize', methods=['POST'])
@limiter.limit("20 per minute")
@require_api_key
def recognize():
    try:
        image_bytes = extract_image_bytes(request)
        result      = recognize_image(image_bytes)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'recognition':          result,
        'category':             result['category'],
        'category_description': CATEGORIES[result['category']],
    })

@app.route('/api/identify', methods=['POST'])
@limiter.limit("20 per minute")
@require_api_key
def identify():
    """
    Lightweight endpoint — hanya kembalikan nama barang.
    Support multipart/form-data dan application/json (base64).
    Response: { "name": "Inverter Mitsubishi FR-A740" }
    """
    try:
        image_bytes = extract_image_bytes(request)
        result      = recognize_image(image_bytes)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'name': result['item_name']})

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 55)
    print("  Spare Part Image Recognition — Gemini AI")
    print("=" * 55)
    print(f"  API KEY : {'OK ✓' if GEMINI_API_KEY else 'NOT FOUND ✗'}")
    print(f"  Categories: {', '.join(CATEGORIES.keys())}")
    print("  Endpoints:")
    print("    POST /api/recognize  → full result (file/base64)")
    print("    POST /api/identify   → name only  (file/base64)")
    print("=" * 55)
    print("  Buka browser: http://localhost:5000")
    print("=" * 55)
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)