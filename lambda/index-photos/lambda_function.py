import boto3
import json
import os
import base64
from datetime import datetime
# import requests # Need to add layer for this
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
import http.client
import urllib.parse

#######Testing Pipeline
# Initialize AWS Rekognition client
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
# opensearch = boto3.client('opensearch', region_name='us-east-1')
credentials = boto3.Session().get_credentials().get_frozen_credentials()
AWS_REGION = "us-east-1"
# OpenSearch endpoint from environment variables
# OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']
OPENSEARCH_ENDPOINT = 'https://search-photos-search-a3enfdo3dugpg5ba6msyyctykm.us-east-1.es.amazonaws.com'

def lambda_handler(event, context):
    print("Event, Context",event,context)
    for record in event['Records']:
        # Get S3 bucket and object key
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        try:
            # Detect labels using Rekognition
            response = s3.get_object(Bucket=bucket, Key=key)
            base64_image = response['Body'].read()  # Base64-encoded data
            # Decode the Base64 data to binary
            image_binary = base64.b64decode(base64_image)


            rekognition_response = rekognition.detect_labels(
                # Image={'S3Object': {'Bucket': bucket, 'Name': key}},
                Image={'Bytes': image_binary},
                MaxLabels=5
            )
            print(f"Labels detected: {rekognition_response['Labels']}")
            labels = [label['Name'] for label in rekognition_response['Labels']]
            # Extract custom labels from metadata
            custom_labels = record.get('customLabels', [])
            
            # Prepare the document for Elasticsearch
            document = {
                "photo_id": key,
                "s3_bucket": bucket,
                "s3_key": key,
                "labels": labels,
                "custom_labels": custom_labels,
                "timestamp": datetime.utcnow().isoformat()
            }
            print('Document before indexing',document)
            index_document(document, key)

        except rekognition.exceptions.InvalidImageFormatException as e:
            # Log the error and prevent further retries
            print(f"Invalid image format for {key}: {str(e)}")
            return {
                'statusCode': 400,
                'body': f"Invalid image format for {key}: {str(e)}"
            }
        except Exception as e:
            # Catch other exceptions
            print(f"Error processing image {key}: {str(e)}")
            return {
                'statusCode': 500,
                'body': f"Error processing image {key}: {str(e)}"
            }

    
    return {
        'statusCode': 200,
        'body': json.dumps('Photos indexed successfully!')
    }

def index_document(document, key):
    """
    Indexes the document in OpenSearch using an HTTP request with SigV4 signing.
    """
    try:
        # Construct the OpenSearch index URL
        index_url = f"{OPENSEARCH_ENDPOINT}/photos/_doc/{key}"
        parsed_url = urllib.parse.urlparse(index_url)

        # Create the request
        request = AWSRequest(
            method='PUT',
            url=index_url,
            data=json.dumps(document),
            headers={'Content-Type': 'application/json'}
        )
        SigV4Auth(credentials, "es", AWS_REGION).add_auth(request)

        # Send the HTTP request
        connection = http.client.HTTPSConnection(parsed_url.hostname, parsed_url.port or 443)
        connection.request(
            method=request.method,
            url=parsed_url.path,
            body=request.body,
            headers=dict(request.headers)
        )
        response = connection.getresponse()

        # Check the response
        if response.status not in [200, 201]:
            raise Exception(f"Failed to index document: {response.read().decode()}")
        print("Document indexed successfully:", response.read().decode())
    except Exception as e:
        print(f"Failed to index document in OpenSearch: {str(e)}")
        raise

