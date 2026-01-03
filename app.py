from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io
from PIL import Image
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Remove Background API",
        "endpoints": {
            "/remove-bg": "POST - Remove background with red mask"
        }
    })

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    try:
        # Obtener imágenes del request
        if 'original' not in request.files or 'mask' not in request.files:
            return jsonify({
                "error": "Debes enviar 'original' y 'mask' como archivos"
            }), 400
        
        original_file = request.files['original']
        mask_file = request.files['mask']
        
        # Convertir a arrays numpy
        original_bytes = np.frombuffer(original_file.read(), np.uint8)
        mask_bytes = np.frombuffer(mask_file.read(), np.uint8)
        
        img = cv2.imdecode(original_bytes, cv2.IMREAD_COLOR)
        mask = cv2.imdecode(mask_bytes, cv2.IMREAD_COLOR)
        
        if img is None or mask is None:
            return jsonify({"error": "Error al decodificar imágenes"}), 400
        
        # Redimensionar máscara al tamaño de la imagen original
        if img.shape[:2] != mask.shape[:2]:
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]))
        
        # Detectar rojo (BGR format)
        lower_red1 = np.array([0, 0, 100])
        upper_red1 = np.array([100, 100, 255])
        red_mask1 = cv2.inRange(mask, lower_red1, upper_red1)
        
        # Detectar rojo en HSV
        hsv_mask = cv2.cvtColor(mask, cv2.COLOR_BGR2HSV)
        lower_red2 = np.array([0, 50, 50])
        upper_red2 = np.array([50, 255, 255])
        red_mask2 = cv2.inRange(hsv_mask, lower_red2, upper_red2)
        
        # Combinar máscaras
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        
        # Suavizar bordes
        red_mask = cv2.GaussianBlur(red_mask, (5, 5), 0)
        
        # Convertir a RGBA
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        
        # Aplicar transparencia
        img[:, :, 3] = np.where(red_mask > 0, 0, 255)
        
        # Convertir a PNG y devolver
        is_success, buffer = cv2.imencode('.png', img)
        if not is_success:
            return jsonify({"error": "Error al codificar imagen"}), 500
        
        io_buf = io.BytesIO(buffer)
        
        return send_file(
            io_buf,
            mimetype='image/png',
            as_attachment=True,
            download_name='result.png'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
