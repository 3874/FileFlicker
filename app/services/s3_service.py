from flask import current_app
import logging
from botocore.exceptions import ClientError

class S3Service:
    @staticmethod
    def upload_file(file, key):
        try:
            current_app.s3_client.upload_fileobj(
                file,
                current_app.config['AWS_S3_BUCKET'],
                key
            )
            return True
        except Exception as e:
            logging.error(f'Error uploading file to S3: {str(e)}')
            return False

    @staticmethod
    def delete_file(key):
        try:
            current_app.s3_client.delete_object(
                Bucket=current_app.config['AWS_S3_BUCKET'],
                Key=key
            )
            return True
        except Exception as e:
            logging.error(f'Error deleting file from S3: {str(e)}')
            return False

    @staticmethod
    def generate_presigned_url(key, expiration=3600):
        try:
            url = current_app.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': current_app.config['AWS_S3_BUCKET'],
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logging.error(f'Error generating presigned URL: {str(e)}')
            return None