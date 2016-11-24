import os
import boto3
from werkzeug.utils import secure_filename
from flask import current_app
from io import BytesIO


def allowed_file(filename):
    return filename.rsplit('.', 1)[1] in current_app.config.get('ALLOWED_EXTENSIONS')


def s3_upload_file_from_request(request, key, path=''):
    if not request.files:
        raise Exception('No files in request')

    fileObj = request.files.get(key)

    if not fileObj:
        raise Exception('Invalid request.files key')

    return s3_upload_fileObj(fileObj, path)


def s3_upload_fileObj(fileObj, path=''):
    if not allowed_file(fileObj.filename):
        raise Exception('Invalid file extension')

    filename = secure_filename(fileObj.filename)
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(current_app.config.get('S3_BUCKET_NAME'))

    bucket.upload_fileobj(fileObj, os.path.join(path, filename))

    return filename


def s3_download_file(file, path):
    filename = secure_filename(file)

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(current_app.config.get('S3_BUCKET_NAME'))

    data = BytesIO()
    bucket.download_fileobj(os.path.join(path, filename), data)

    return data.getvalue()
