from botocore.exceptions import NoCredentialsError, ClientError
from flask import current_app
import logging

class AWSService:
    @staticmethod
    def generate_presigned_url(bucket_name, file_key, expiration=3600):
        try:
            response = current_app.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expiration
            )
            return response
        except NoCredentialsError:
            logging.error("AWS credentials not available")
            return None
        except Exception as e:
            logging.error(f"Error generating presigned URL: {str(e)}")
            return None

    @staticmethod
    def upload_file(file_obj, bucket_name, file_key):
        try:
            current_app.s3_client.upload_fileobj(
                file_obj,
                bucket_name,
                file_key
            )
            return True
        except NoCredentialsError:
            logging.error("AWS credentials not available")
            return False
        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            return False

    @staticmethod
    def delete_file(bucket_name, file_key):
        try:
            current_app.s3_client.delete_object(
                Bucket=bucket_name,
                Key=file_key
            )
            return True
        except Exception as e:
            logging.error(f"Error deleting file: {str(e)}")
            return False

    @staticmethod
    def check_file_exists(bucket_name, file_key):
        try:
            current_app.s3_client.head_object(
                Bucket=bucket_name,
                Key=file_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logging.error(f"Error checking file existence: {str(e)}")
            return False

    @staticmethod
    def list_files(bucket_name, prefix=''):
        try:
            response = current_app.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            logging.error(f"Error listing files: {str(e)}")
            return []

    @staticmethod
    def get_file_metadata(bucket_name, file_key):
        try:
            response = current_app.s3_client.head_object(
                Bucket=bucket_name,
                Key=file_key
            )
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'metadata': response.get('Metadata', {})
            }
        except Exception as e:
            logging.error(f"Error getting file metadata: {str(e)}")
            return None