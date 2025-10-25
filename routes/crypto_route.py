import os, base64
from flask import Blueprint, jsonify, session

crypto_bp = Blueprint('crypto', __name__, url_prefix='/api/crypto')

@crypto_bp.route('/session-key', methods=['GET'])
def get_session_key():
    # Check if session already has a key
    if 'session_key' not in session:
        # Generate a 256-bit random key (32 bytes)
        key = os.urandom(32)
        session['session_key'] = base64.b64encode(key).decode('utf-8')

    return jsonify({ "keyB64": session['session_key'] })