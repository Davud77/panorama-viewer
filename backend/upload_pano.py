from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import piexif
import json
import os
from minio import Minio
import psycopg2
from datetime import datetime
import io

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})


def load_db_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, 'db_config.json')
    with open(config_path, 'r') as file:
        return json.load(file)

def load_minio_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, 'minio_config.json')
    with open(config_path, 'r') as file:
        return json.load(file)

db_config = load_db_config()
minio_config = load_minio_config()

minio_client = Minio(
    minio_config['url'].split('//')[1],
    access_key=minio_config['accessKey'],
    secret_key=minio_config['secretKey'],
    secure=minio_config['url'].startswith('https')
)

def connect_db():
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password']
    )

def get_gps_coordinates(exif_data):
    latitude = longitude = None
    if piexif.GPSIFD.GPSLatitudeRef and piexif.GPSIFD.GPSLatitude in exif_data:
        lat_ref = exif_data[piexif.GPSIFD.GPSLatitudeRef].decode()
        lat = exif_data[piexif.GPSIFD.GPSLatitude]
        latitude = convert_to_degrees(lat)
        if lat_ref != 'N':
            latitude = -latitude

    if piexif.GPSIFD.GPSLongitudeRef and piexif.GPSIFD.GPSLongitude in exif_data:
        lon_ref = exif_data[piexif.GPSIFD.GPSLongitudeRef].decode()
        lon = exif_data[piexif.GPSIFD.GPSLongitude]
        longitude = convert_to_degrees(lon)
        if lon_ref != 'E':
            longitude = -longitude

    return latitude, longitude

def convert_to_degrees(value):
    d, m, s = value
    return d[0] / d[1] + m[0] / m[1] / 60 + s[0] / s[1] / 3600

@app.route('/upload', methods=['POST'])
def upload_files():
    uploaded_files = request.files.getlist("files")
    tags = request.form.get("tags", "")
    successful_uploads = []
    failed_uploads = []

    for file in uploaded_files:
        try:
            file_path = f"pano/{file.filename}"
            file_content = file.read()
            file_stream = io.BytesIO(file_content)
            minio_client.put_object("pano", file_path, file_stream, len(file_content))
            file_stream.seek(0)

            with Image.open(file_stream) as img:
                exif_data = img._getexif()
                if exif_data:
                    exif_dict = piexif.load(img.info['exif'])
                    gps_data = get_gps_coordinates(exif_dict['GPS']) if 'GPS' in exif_dict else (None, None)

            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO panolist (filename, tags, latitude, longitude, upload_date) VALUES (%s, %s, %s, %s, %s)",
                (file.filename, tags, gps_data[0], gps_data[1], datetime.now())
            )
            conn.commit()
            cur.close()
            conn.close()
            successful_uploads.append(file.filename)
        except Exception as e:
            print(f"Не удалось загрузить файл {file.filename}: {str(e)}")
            failed_uploads.append(file.filename)

    return jsonify({
        "message": "Отчет о загрузке файлов",
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads
    }), 200



if __name__ == '__main__':
    app.run(debug=True)