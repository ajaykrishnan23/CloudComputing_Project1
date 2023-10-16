import json
import random
import boto3
import logging
from botocore.exceptions import ClientError
import requests 

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def receiveMsgFromSqsQueue():
    sqs = boto3.client('sqs')
    queue_url = '#####'
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=['SentTimestamp'],
        MaxNumberOfMessages=5,
        MessageAttributeNames=['All'],
        VisibilityTimeout=10,
        WaitTimeSeconds=0
        )
    return response

def lambda_handler(event, context):
    # getting response from sqs queue
    sqsQueueResponse = receiveMsgFromSqsQueue()
    if "Messages" in sqsQueueResponse.keys():
        for message in sqsQueueResponse['Messages']:
            callSQS(message)
            #now delete message from queue
            receipt_handle = message['ReceiptHandle']
            deleteMsg(receipt_handle)
            
def deleteMsg(receipt_handle):
    sqs = boto3.client('sqs')
    queue_url = '######'
    sqs.delete_message(QueueUrl=queue_url,
    ReceiptHandle=receipt_handle
    )

def callSQS(message):
    message_attributes = message['MessageAttributes']
    cuisine = message_attributes['cuisine']['StringValue']
    location = message_attributes['location']['StringValue']
    date = message_attributes['date']['StringValue']
    time = message_attributes['time']['StringValue']
    people = message_attributes['people']['StringValue']
    email = message_attributes['email']['StringValue']
    rest_ids = get_rest_id(cuisine)
    rest_info = ""
    for i in range(5):
        rest_info += str(i+1)+ ". "+get_restaurant_info(rest_ids[i]) +"\n"+"\n"
    sendMessage = 'Hello! Here are my '+ cuisine +' restaurant suggestions for ' + people + ' people dining on ' + date + ' at ' + time + " " + '\n' +'\n'+rest_info+'Enjoy your meal !'
    print(email)
    print(sendMessage)
    temp_email(sendMessage,email)

#get restaurant ID from Elastic Open Search with target user query cusine
# need to modify query
def get_rest_id(cuisine):
    es_Query = "#########/#####_index/_search?q={cuisine}".format(cuisine=cuisine)
    esResponse = requests.get(es_Query,auth=('######', '#####'))
    data = json.loads(esResponse.content.decode('utf-8'))
    try:
        esData = data["hits"]["hits"]
    except KeyError:
        logger.debug("Error extracting hits from ES response")
    rest_ids = []
    nums = random.sample(range(0, len(esData)-1), 5)
    for i in range(5):
        tmpList = esData[nums[i]]
        rest_ids.append(tmpList['_source']['bid'])  
    return rest_ids
    
    
#get restaurant name and address from dynamo db based on the id fetched from Elastic search
def get_restaurant_info(rest_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelprestaurants')
    response = table.get_item(
        Key={
            'bID': rest_id
        }
    )
    response_item = response.get("Item")
    rest_name = response_item['name']
    rest_address = response_item['address']
    rest_info = ('Restaurant Name: '+rest_name +'\n'+'Address: '+','.join(rest_address))
    return rest_info

#send user the template mail with the suggestions 
#Note: Free Tier only supports sending mails to verified email addresses 
#Verify the E-Mail address in the SES microservice 
def temp_email(sendMessage,email):
    ses_client = boto3.client("ses", region_name="us-east-1")
    CHARSET = "UTF-8"
    ses_client.send_email(
        Destination={
            "ToAddresses": [
                email,
            ],
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": CHARSET,
                    "Data": sendMessage,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "Dining Suggestions",
            },
        },
        Source="######",
    )
    
