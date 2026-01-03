import os
import json
import boto3
import base64
from datetime import datetime, timedelta

# Initialize the S3 client outside of the handler
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
request_invalid_message = "Request is not valid."

allowed_intervals = [
    3600,
    86400,
    172800,
    604800
]

def is_base64_encoded(payload):
    try:
        encoded_payload = payload.encode('latin-1').decode('unicode_escape').encode('utf-8')
        payload_validates = base64.b64encode(base64.b64decode(encoded_payload)) == encoded_payload
        if not payload_validates:
            raise Exception(request_invalid_message)
    except Exception as e:
        raise Exception(request_invalid_message)

def lambda_handler(event, context):
    try:
        if event.get('isBase64Encoded', False):
            body = json.loads(base64.b64decode(event['body']))
        else:
            body = json.loads(event['body'])

        iv = body['iv']
        payload = body['payload']
        secret_id = context.aws_request_id

        ttl_seconds = body.get('expiry', 86400)

        if ttl_seconds not in allowed_intervals:
            raise Exception(request_invalid_message)

        expires_at = int((datetime.now() + timedelta(seconds=ttl_seconds)).timestamp())

        is_base64_encoded(iv)
        is_base64_encoded(payload)

        table = dynamodb.Table(table_name)

        if not table:
            raise Exception("Internal error")

        table.put_item(
            Item = {
                'id': secret_id,
                'iv': iv,
                'payload': payload,
                'expiresAt': expires_at
            }
        )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'id': secret_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
