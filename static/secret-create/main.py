import os
import json
import logging
import boto3
import base64
from datetime import datetime, timedelta

# Initialize the S3 client outside of the handler
dynamodb = boto3.resource('dynamodb')

# Initialize the logger
logger = logging.getLogger()
logger.setLevel("INFO")

def lambda_handler(event, context):
    try:
        if event.get('isBase64Encoded', False):
            body = json.loads(base64.b64decode(event['body']))
        else:
            body = json.loads(event['body'])

        # Extract your data
        iv = body['iv']
        payload = body['payload']
        ttl_seconds = body.get('expiry', 86400)  # Default 24 hours

        # Save to DynamoDB
        table_name = os.environ['TABLE_NAME']
        table = dynamodb.Table(table_name)

        secret_id = context.aws_request_id  # Use Lambda request ID as unique ID
        expires_at = int((datetime.now() + timedelta(seconds=ttl_seconds)).timestamp())

        table.put_item(Item={
            'id': secret_id,
            'iv': iv,
            'payload': payload,
            'expiresAt': expires_at
        })

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'id': secret_id})
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
