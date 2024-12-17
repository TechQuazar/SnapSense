import boto3
import json

# Initialize AWS services
lex_client = boto3.client('lexv2-runtime')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Extract user query from API Gateway query string
        print('Event',event)
        user_query = event['queryStringParameters']['q']
        print('User Query',user_query)
        if not user_query:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Query parameter 'q' is required."}),
                "headers": {
                "Access-Control-Allow-Origin": "*",  # Or replace '' with the specific domain
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"}
        }
        
        # Step 1: Pass query to Lex bot
        lex_response = lex_client.recognize_text(
            botId='7VBQRQBOTE',
            botAliasId='TSTALIASID',
            localeId='en_US',
            sessionId='user-session',
            text=user_query
        )

        keyword1 = lex_response['sessionState']['intent']['slots']['keyword1']
        keyword2 = lex_response['sessionState']['intent']['slots']['keyword2']
        if keyword1 is not None:
            keyword1 = keyword1['value']['interpretedValue']
        if keyword2 is not None:
            keyword2 = keyword2['value']['interpretedValue']
        
        if not keyword1:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No valid keywords detected in query."}),
                "headers": {
                "Access-Control-Allow-Origin": "*",  # Or replace '' with the specific domain
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"}
            }
        
        search_payload = {
            "keyword1": keyword1,
            "keyword2": keyword2
        }
        print('____Search Payload',search_payload)
        response = lambda_client.invoke(
            FunctionName="search-photos3",  # Replace with your Lambda function name
            InvocationType="RequestResponse",
            Payload=json.dumps(search_payload)
        )
        

        # Step 3: Return image URLs to API Gateway
        search_results = json.loads(response['Payload'].read())
        print('SEARCHHHHHHHHH',search_results)
        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Or replace '' with the specific domain
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"},
            'body': json.dumps(search_results)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
           "headers": {
                "Access-Control-Allow-Origin": "*",  # Or replace '' with the specific domain
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"}
        }
