from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
import io
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Remove Background API"
    })

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    try:
        if 'original' not in request.files or 'mask' not in request.files:
            return jsonify({"error": "Debes enviar 'original' y 'mask'"}), 400
        
        # Cargar imágenes
        original = Image.open(request.files['original']).convert('RGBA')
        mask = Image.open(request.files['mask']).convert('RGB')
        
        # Redimensionar máscara si es necesario
        if original.size != mask.size:
            mask = mask.resize(original.size)
        
        # Convertir a numpy arrays
        img_array = np.array(original)
        mask_array = np.array(mask)
        
        # Detectar rojo (R > 100 y G,B < 100)
        red_pixels = (mask_array[:, :, 0] > 100) & \
                     (mask_array[:, :, 1] < 100) & \
                     (mask_array[:, :, 2] < 100)
        
        # Aplicar transparencia
        img_array[:, :, 3] = np.where(red_pixels, 0, 255)
        
        # Convertir de vuelta a imagen
        result = Image.fromarray(img_array, 'RGBA')
        
        # Guardar en buffer
        buf = io.BytesIO()
        result.save(buf, format='PNG')
        buf.seek(0)
        
        return send_file(buf, mimetype='image/png', as_attachment=True, download_name='result.png')
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
