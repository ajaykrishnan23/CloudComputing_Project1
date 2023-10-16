import json
import boto3

def lambda_handler(event, context):
    # TODO implement
    # Initialize the Lex Runtime V2 client
    lex_runtime = boto3.client('lexv2-runtime')

    # Replace these values with your Lex bot details
    bot_alias_id = '###'
    bot_id = '##'
    locale_id = 'en_US'  # Language code
    
    # session_id = event.get('sessionId', None)
    session_id = 'gku7p8pbw6b'
    user_input = event['messages'][0]['unstructured']['text']

    # Send user input to Lex and get a response
    response = lex_runtime.recognize_text(
        botAliasId=bot_alias_id,
        botId=bot_id,
        localeId=locale_id,
        sessionId=session_id,
        text=user_input
    )

    botResponse =  [{
        'type': 'unstructured',
        'unstructured': {
          'text': response['messages']
        }}]
    return {
        'statusCode': 200,
        'messages': botResponse
    }
