from flask import Flask, request, jsonify
import face_recognition
import os
import uuid
from PIL import Image
import io

app = Flask(__name__)

# Diretório onde as imagens de referência serão salvas
REF_DIR = "reference_faces"
os.makedirs(REF_DIR, exist_ok=True)  # Cria a pasta caso não exista

# Dicionário para armazenar em memória as informações dos rostos cadastrados
reference_faces = {}

def process_image_file_from_disk(filepath):
    """
    Processa uma imagem salva no disco e converte para RGB.
    Retorna um numpy array compatível com face_recognition.
    """
    image = Image.open(filepath)
    image = image.convert('RGB')
    image_stream = io.BytesIO()
    image.save(image_stream, format='JPEG')
    image_stream.seek(0)
    return face_recognition.load_image_file(image_stream)

def process_image_file_from_upload(file_storage):
    """
    Processa um arquivo enviado via upload (FileStorage).
    Converte para RGB e retorna numpy array compatível com face_recognition.
    """
    image_stream = io.BytesIO()
    image = Image.open(file_storage)
    image = image.convert('RGB')
    image.save(image_stream, format='JPEG')
    image_stream.seek(0)
    return face_recognition.load_image_file(image_stream)

@app.route('/faces', methods=['POST'])
def add_face():
    name = request.form.get('name')
    file = request.files.get('image')

    if not name or not file:
        return jsonify({'error': 'Nome e imagem são obrigatórios'}), 400

    face_id = str(uuid.uuid4())
    filename = f"{face_id}.jpg"
    filepath = os.path.join(REF_DIR, filename)

    # Salva imagem no disco
    file.save(filepath)

    # Processa imagem salva no disco
    image_np = process_image_file_from_disk(filepath)

    encodings = face_recognition.face_encodings(image_np)
    if not encodings:
        os.remove(filepath)
        return jsonify({'error': 'Nenhum rosto detectado'}), 400

    reference_faces[face_id] = {
        'id': face_id,
        'name': name,
        'filepath': filepath,
        'encoding': encodings[0]
    }
    return jsonify({'id': face_id, 'name': name}), 201

@app.route('/faces', methods=['GET'])
def list_faces():
    return jsonify([{'id': f['id'], 'name': f['name']} for f in reference_faces.values()])

@app.route('/faces/<face_id>', methods=['PUT'])
def update_face(face_id):
    face = reference_faces.get(face_id)
    if not face:
        return jsonify({'error': 'Face não encontrada'}), 404

    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'Nova imagem obrigatória'}), 400

    filepath = face['filepath']
    file.save(filepath)  # sobrescreve a imagem existente

    # Processa a nova imagem salva no disco
    image_np = process_image_file_from_disk(filepath)
    encodings = face_recognition.face_encodings(image_np)

    if not encodings:
        return jsonify({'error': 'Nenhum rosto detectado'}), 400

    face['encoding'] = encodings[0]
    return jsonify({'message': 'Rosto atualizado com sucesso'})

@app.route('/faces/<face_id>', methods=['DELETE'])
def delete_face(face_id):
    face = reference_faces.pop(face_id, None)
    if not face:
        return jsonify({'error': 'Face não encontrada'}), 404

    os.remove(face['filepath'])
    return jsonify({'message': 'Rosto removido com sucesso'})

@app.route('/verify', methods=['POST'])
def verify_face():
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'Imagem obrigatória'}), 400

    # Processa imagem enviada direto via upload
    image_np = process_image_file_from_upload(file)
    encodings = face_recognition.face_encodings(image_np)

    if not encodings:
        return jsonify({'status': 'unauthorized'}), 401

    input_encoding = encodings[0]
    for face in reference_faces.values():
        match = face_recognition.compare_faces([face['encoding']], input_encoding)[0]
        if match:
            return jsonify({'status': 'authorized', 'user_id': face['id'], 'name': face['name']})

    return jsonify({'status': 'unauthorized'}), 401

if __name__ == '__main__':
    app.run(debug=True)
