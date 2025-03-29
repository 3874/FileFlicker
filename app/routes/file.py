import bcrypt
from flask import current_app
from flask import Blueprint, request, jsonify, render_template, session
from bson import ObjectId
from datetime import datetime
from .. import users_collection, files_collection 
from ..utils.decorators import login_required

bp = Blueprint('file', __name__, url_prefix='/files')

@bp.route('/', methods=['GET'])
@login_required
def get_files():
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 100))
    search_value = request.args.get('search[value]', '').lower()

    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    query = {}

    if user and user.get('role') == 'admin':
        if search_value:
            query["$or"] = [
                {"file_name": {"$regex": search_value, "$options": "i"}},
                {"summary": {"$regex": search_value, "$options": "i"}},
                {"comments": {"$regex": search_value, "$options": "i"}},
                {"tags": {"$elemMatch": {"$regex": search_value, "$options": "i"}}}
            ]
        else:
            query = {}
    else:
        query = {"owner": session['user_id']}
        if search_value:
            query["$or"] = [
                {"file_name": {"$regex": search_value, "$options": "i"}},
                {"summary": {"$regex": search_value, "$options": "i"}},
                {"comments": {"$regex": search_value, "$options": "i"}},
                {"tags": {"$elemMatch": {"$regex": search_value, "$options": "i"}}}
            ]

    total = files_collection.count_documents(query)
    cursor = files_collection.find(query).sort("createdAt", -1).skip(start).limit(int(length))
    paginated_files = list(cursor)
    for f in paginated_files:
        f['_id'] = str(f['_id'])

    response = {
        "draw": int(request.args.get('draw', 1)),
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": paginated_files
    }
    return jsonify(response)

@bp.route('/uploadFile', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    normalized_filename = normalize('NFC', file.filename)
    file_name = urllib.parse.quote(normalized_filename)

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    userId = session['user_id']

    try:
        head_response = s3_client.head_object(Bucket=bucket_name, Key=f'users/drive/{userId}/{file_name}')
        existing_file_size = head_response['ContentLength']
        if existing_file_size == file_size:
            return jsonify({'error': 'File already exists with the same name and size.'}), 400
    except s3_client.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code != 404:
            logging.error(f"Error checking S3: {e}")
            return jsonify({'error': 'Error checking file in S3.'}), 500

    try:
        s3_client.upload_fileobj(file, bucket_name, f'users/drive/{userId}/{file_name}')
        logging.info(f'File uploaded to S3: {file_name} in bucket {bucket_name}/users/drive/{userId}')
    except Exception as e:
        logging.error(f'Error uploading file to S3: {str(e)}')
        return jsonify({'error': 'Could not upload the file to S3.'}), 500


    current_time = datetime.now().isoformat()
    new_entry = {
        'file_name': urllib.parse.unquote(file_name),
        'location': f's3://{bucket_name}/users/drive/{userId}/{file_name}',
        'tags': [],
        'summary': '',
        'comments': '',
        'owner': session['user_id'],
        'RAG': False,
        'createdAt': current_time,
        'updatedAt': current_time
    }

    result = files_collection.insert_one(new_entry)
    new_entry['_id'] = str(result.inserted_id)  # _id를 문자열로 변환

    return jsonify({'success': True, 'data': new_entry}), 201

@bp.route('/exportFiletoServer', methods=['POST'])
def export_file_to_server():
    data = request.form 

    if not data or 'id' not in data or 'pwd' not in data:
        return jsonify({'error': 'ID and password are required.'}), 400

    user = users_collection.find_one({'ID': data['id']})
    if not user or not bcrypt.checkpw(data['pwd'].encode('utf-8'), user['password']):
        return jsonify({'error': 'Invalid ID or password.'}), 401

    userId = str(user['_id'])

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400

    file = request.files['file']  # request.files에서 파일 가져오기
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    file_name = file.filename

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    try:
        head_response = s3_client.head_object(Bucket=bucket_name, Key=f'users/drive/{userId}/{file_name}')
        existing_file_size = head_response['ContentLength']
        if existing_file_size == file_size:
            return jsonify({'error': 'File already exists with the same name and size.'}), 400
    except s3_client.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code != 404:
            logging.error(f"Error checking S3: {e}")
            return jsonify({'error': 'Error checking file in S3.'}), 500

    try:
        s3_client.upload_fileobj(file, bucket_name, f'users/drive/{userId}/{file_name}')
        logging.info(f'File uploaded to S3: {file_name} in bucket {bucket_name}/users/drive/{userId}')
    except Exception as e:
        logging.error(f'Error uploading file to S3: {str(e)}')
        return jsonify({'error': 'Could not upload the file to S3.'}), 500

    new_entry = {
        'file_name': file_name,
        'location': f's3://{bucket_name}/users/drive/{userId}/{file_name}',
        'tags': data.get('tags', '').split(',') if data.get('tags') else [],
        'summary': data.get('summary'),
        'comments': data.get('comments'), 
        'owner': userId,
        'createdAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat()
    }

    result = files_collection.insert_one(new_entry)
    new_entry['_id'] = str(result.inserted_id)

    return jsonify({'success': True, 'data': new_entry}), 201

@bp.route('/updateFile/<string:fileId>', methods=['PUT'])
@login_required
def update_file(fileId):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data.'}), 400

    # tags 문자열을 콤마로 분리
    tag_array = data.get('tags', '').split(',')
    update_data = {
        'summary': data.get('summary', ''),
        'comments': data.get('comments', ''),
        'tags': tag_array,
        'updatedAt': datetime.now().isoformat()
    }

    try:
        obj_id = ObjectId(fileId)
    except Exception:
        return jsonify({'error': 'Invalid file ID format.'}), 400

    result = files_collection.update_one({'_id': obj_id}, {'$set': update_data})
    if result.matched_count == 0:
        return jsonify({'error': 'File not found.'}), 404

    file_entry = files_collection.find_one({'_id': obj_id})
    file_entry['_id'] = str(file_entry['_id'])
    return jsonify({'success': True, 'data': file_entry}), 200

@bp.route('/removeFile/<string:fileId>', methods=['DELETE'])
@login_required
def remove_file(fileId):
    try:
        obj_id = ObjectId(fileId)
    except Exception:
        return jsonify({'error': 'Invalid file ID format.'}), 400

    file_entry = files_collection.find_one({'_id': obj_id})
    if not file_entry:
        return jsonify({'error': 'File not found.'}), 404

    s3_location = file_entry.get('location')
    if s3_location.startswith('s3://'):
        s3_location = s3_location[5:] 
    else:
        return jsonify({'error': 'Invalid S3 location format.'}), 400

    bucket_name, s3_key = s3_location.split('/', 1) 

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
    except Exception as e:
        logging.error(f'Error deleting file from S3: {str(e)}')
        return jsonify({'error': 'Could not delete the file from S3.'}), 500

    files_collection.delete_one({'_id': obj_id})

    try:
        vector_result = delete_file_from_vectordb(fileId)
        if vector_result[1] == 500:  # 에러 발생 시
            logging.error('Failed to delete from vector DB but file was deleted from S3 and MongoDB')
    except Exception as e:
        logging.error(f'Error while deleting from vector DB: {str(e)}')
        # 벡터 DB 삭제 실패해도 진행 (S3와 MongoDB에서는 이미 삭제됨)

    return jsonify({
        'success': True,
        'message': 'File successfully deleted from S3 and MongoDB'
    }), 200

@bp.route('/getFile/<string:fileId>', methods=['GET'])
@login_required
def get_file(fileId):
    try:
        obj_id = ObjectId(fileId)
    except Exception:
        return jsonify({'error': 'Invalid file ID format.'}), 400

    file_entry = files_collection.find_one({'_id': obj_id})

    if not file_entry:
        return jsonify({'error': 'File not found.'}), 404

    file_entry['_id'] = str(file_entry['_id'])
    return jsonify({'success': True, 'data': file_entry}), 200

@bp.route('/registMissingFilesInAWS', methods=['GET']) 
@login_required
def import_files():
    userId = session['user_id']
    user_folder = f'users/drive/{userId}'
    
    try:
        s3_objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=user_folder)

        if 'Contents' not in s3_objects:
            return jsonify({'status': 'success', 'message': 'No files found in S3.'}), 200
        
        registered_files = files_collection.find({'owner': userId})
        registered_file_names = { file['file_name'] for file in registered_files }

        for obj in s3_objects['Contents']:
            file_name = obj['Key'].split('/')[-1]
            if file_name not in registered_file_names:

                new_entry = {
                    'file_name': normalize('NFC',file_name),
                    'location': f's3://{bucket_name}/{obj["Key"]}',
                    'tags': [],
                    'summary': '',
                    'comments': '',
                    'owner': userId,
                    'createdAt': datetime.now().isoformat(),
                    'updatedAt': datetime.now().isoformat()
                }

                files_collection.insert_one(new_entry)

        return jsonify({'status': 'success', 'message': 'Files imported successfully.'}), 200

    except Exception as e:
        logging.error(f'Error importing files: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/fileSearchInVectorDB', methods=['POST'])
def file_search():
    data = request.get_json()

    if not isinstance(data, list) or len(data) == 0:
        return jsonify({'error': 'Invalid data format'}), 400

    YlemURL = f"{QR_config.get('n8n_URL')}/webhook/file-search"

    try:
        response = requests.post(
            YlemURL,
            json=[{
                "sessionId": data[0].get('fileId'),
                "action": data[0].get('action'),
                "chatInput": data[0].get('chatInput'),
            }]
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': f'HTTP error occurred: {str(e)}'}), 500
    except requests.exceptions.ConnectionError as e:
        return jsonify({'error': f'Connection error occurred: {str(e)}'}), 500
    except requests.exceptions.Timeout as e:
        return jsonify({'error': f'Timeout error occurred: {str(e)}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@bp.route('/searchFile', methods=['GET'])
@login_required
def search_file():
    keywords = request.args.get('keywords', '')
    keywords_list = keywords.split()

    if not keywords_list:
        return jsonify({'error': 'No keywords provided.'}), 400

    and_conditions = []
    for keyword in keywords_list:
        or_condition = {
            "$or": [
                {"file_name": {"$regex": keyword, "$options": "i"}},
                {"tags": {"$elemMatch": {"$regex": keyword, "$options": "i"}}},
                {"summary": {"$regex": keyword, "$options": "i"}},
                {"comments": {"$regex": keyword, "$options": "i"}}
            ]
        }
        and_conditions.append(or_condition)

    query = {"$and": and_conditions} if and_conditions else {}
    results = list(files_collection.find(query))
    # _id를 문자열로 변환 (반복문 처리)
    for r in results:
        r['_id'] = str(r['_id'])
    return jsonify({'success': True, 'results': results}), 200

@bp.route('/downloadFile/<string:fileId>', methods=['GET'])
def download_file(fileId):
    try:
        obj_id = ObjectId(fileId)
    except Exception:
        return jsonify({'error': 'Invalid file ID format.'}), 400

    file_entry = files_collection.find_one({'_id': obj_id})
    if not file_entry:
        return jsonify({'error': 'File not found.'}), 404
    
    s3_key = file_entry["location"][20:]

    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=3600
        )
        logging.info(f'Generated presigned URL: {presigned_url}')
        return jsonify({'url': presigned_url}), 200
    except Exception as e:
        logging.error(f'Error generating presigned URL: {str(e)}')
        return jsonify({'error': 'Could not generate download URL.'}), 500


@bp.route('/storeInVectorDB/<string:fileId>', methods=['GET'])
@login_required
def store_in_vector_db(fileId):
    try:
        obj_id = ObjectId(fileId)
        file_entry = files_collection.find_one({'_id': obj_id})
        
        if not file_entry:
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404

        s3_key = file_entry["location"][20:]
        file_name = file_entry["file_name"]
        file_extension = file_name.split('.')[-1].lower()
        file_rag = file_entry["RAG"]

        if file_rag:
            return jsonify({
                'status': 'error',
                'message': 'File is already inserted for vector storage.'
            }), 400

        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            file_content = response['Body'].read()
        except Exception as e:
            logging.error(f'Error downloading file from S3: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': 'Could not download file from S3.'
            }), 500

        text_content = ""
        file_stream = BytesIO(file_content)
        
        try:
            if file_extension == 'pdf':
                try:
                    with fitz.open(stream=file_stream, filetype="pdf") as doc:
                        for page in doc:
                            text_content += page.get_text("text") + "\n" 
                except Exception as e:
                    logging.error(f'Error extracting text from PDF with PyMuPDF: {e}')
                    return jsonify({
                        'status': 'error',
                        'message': 'Error extracting text from PDF.'
                    }), 500

            elif file_extension in ['doc', 'docx']:
                try:
                    doc = Document(file_stream)
                    for para in doc.paragraphs:
                       text_content += para.text + "\n"
                except Exception as e:
                   logging.error(f'Error extracting text from Word document: {e}')
                   return jsonify({
                        'status': 'error',
                        'message': 'Error extracting text from Word Document.'
                   }), 500
            elif file_extension in ['ppt', 'pptx']:
                try:
                    prs = Presentation(file_stream)
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if hasattr(shape, "text"):
                                text_content += shape.text + "\n"
                except Exception as e:
                   logging.error(f'Error extracting text from powerpoint document: {e}')
                   return jsonify({
                        'status': 'error',
                        'message': 'Error extracting text from Powerpoint Document.'
                   }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Unsupported file type'
                }), 400

            webhook_url = f"{QR_config.get('n8n_URL')}/webhook/storeinvetordb"

            payload = {
                "fileId": str(fileId), 
                "fileName": file_name,
                "text": text_content
            }

            webhook_response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            if not webhook_response.ok:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to store in vector DB. Status: {webhook_response.status_code}'
                }), 500
            
            files_collection.update_one(
                {'_id': obj_id},
                {'$set': {'RAG': True}}
            )

            return jsonify({
                'status': 'success',
                'message': 'Successfully stored in vector database',
                'webhook_response': webhook_response.json()
            }), 200

        except Exception as e:
            logging.error(f'Error in vector storage: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    except Exception as e:
        logging.error(f'Error in store_in_vector_db: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/shareFile', methods=['POST'])
@login_required
def share_file():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid JSON data.'}), 400
    
    s3_key = data.get('s3_key')
    fileName = data.get('fileName')
    recipient_email = data.get('email')
    revised_s3_key = s3_key.replace(f"s3://{bucket_name}/", '')
    Targeturl = generate_presigned_url(bucket_name, revised_s3_key)
    subject = "File is shared by FileFlicker."

    email_content = f"""
        <p>Dear {recipient_email},</p>
        <br>
        <p>I hope this message finds you well.</p>
        <p>I wanted to let you know that the file '{fileName}' has been shared with you by '{session['user_id']}' through FileFlicker.</p>
        <br>
        <p>To download the file, please click on the following link:</p>
        <p><a href="{Targeturl}">Click here to download the file</a></p>
        <br>
        <p>If you have any questions or need further assistance, please feel free to reach out.</p>
        <br>
        <p>Best regards,</p>
        <p>The FileFlicker Team</p>
        <br>
        <p>Brought to you by FileFlicker</p>
    """
    
    result = send_email(recipient_email, subject, email_content)
    return jsonify(result), 200 if result['status'] == 'success' else 500

def delete_file_from_vectordb(fileId):
    try:
        client = QdrantClient(url=QR_config["QDRANT_URL"])
        
        filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.fileId", 
                    match=MatchValue(value=fileId)
                )
            ]
        )
        
        result = client.delete(
            collection_name="files",
            points_selector=filter
        )
        
        if not result:
            logging.error('Error deleting from Qdrant DB')
            return jsonify({'error': 'Could not delete from vector DB.'}), 500
            
        return jsonify({'success': True, 'message': 'Successfully deleted from vector DB'}), 200
        
    except Exception as e:
        logging.error(f'Error deleting from vector DB: {str(e)}')
        return jsonify({'error': 'Could not delete from vector DB.'}), 500


@bp.route('/shareHTML', methods=['POST'])
@login_required
def share_HTML():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid JSON data.'}), 400

    content = data.get('content')
    recipient_email = data.get('email')
    subject = "File is shared by FileFlicker."

    email_content = f"""
        <p>Dear {recipient_email},</p>
        <br>
        <p>I hope this message finds you well.</p>
        <p>I wanted to let you know that the a file has been shared with you by '{session['user_id']}' through FileFlicker.</p>
        <br>
        <div>
        <p>{content}</p>
        </div>
        <br>
        <p>If you have any questions or need further assistance, please feel free to reach out.</p>
        <br>
        <p>Best regards,</p>
        <p>The FileFlicker Team</p>
        <br>
        <p>Brought to you by FileFlicker</p>
    """
    
    result = send_email(recipient_email, subject, email_content)
    return jsonify(result), 200 if result['status'] == 'success' else 500

@bp.route('/shareJson', methods=['POST'])
@login_required
def share_json():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid JSON data.'}), 400
    
    content = data.get('content')
    recipient_email = data.get('email')
    subject = "JSON text is shared by FileFlicker."

    email_content = f"""
        <p>Dear {recipient_email},</p>
        <br>
        <p>I hope this message finds you well.</p>
        <p>I wanted to let you know that the JSON file of a company has been shared with you by '{session['user_id']}' through FileFlicker.</p>
        <br>
        <p>To view and copy the JSON content, please follow these steps:</p>
        <ol>
            <li>Click on the following text to open the JSON content in a new tab:</li>
            <li>{content}</li>
            <li>Once the JSON content is displayed, select all the text (Ctrl+A or Cmd+A) and copy it (Ctrl+C or Cmd+C).</li>
            <li>Visit FileFlicker and import this into the my companies page.</li>
        </ol>
        <br>
        <p>If you have any questions or need further assistance, please feel free to reach out.</p>
        <br>
        <p>Best regards,</p>
        <p>The FileFlicker Team</p>
        <br>
        <p>Brought to you by FileFlicker</p>
    """
    
    result = send_email(recipient_email, subject, email_content)
    return jsonify(result), 200 if result['status'] == 'success' else 500


def send_email(recipient_email, subject, content):
    sender_email = QR_config["SENDER_EMAIL"]
    sender_password = QR_config["SENDER_PWD"]
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(content, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  
            server.login(sender_email, sender_password) 
            server.send_message(msg)  
        return {'status': 'success', 'message': 'Email sent successfully!'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
