import os
import json
import boto3
from datetime import datetime

messages = {
    "missing_expired": "missing_expired",
    "missing_id": "missing_id",
    "general_exception": "general_exception"
}

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Get ID from path or query string
        secret_id = event.get('queryStringParameters', {}).get('id')

        if not secret_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': messages["missing_id"]})
            }

        table_name = os.environ['TABLE_NAME']
        table = dynamodb.Table(table_name)

        # Get the item
        response = table.get_item(Key={'id': secret_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': messages["missing_expired"]})
            }

        item = response['Item']

        table.delete_item(Key={'id': secret_id})

        seconds_now = int(datetime.now().timestamp())
        seconds_then = response["Item"]["expiresAt"]

        if seconds_now > seconds_then:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': messages["missing_expired"]})
            }

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'iv': item['iv'],
                'payload': item['payload']
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': messages["general_exception"]})
        }
