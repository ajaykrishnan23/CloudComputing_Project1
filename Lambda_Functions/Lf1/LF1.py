import math
import dateutil.parser
import datetime
import time
import os
import logging
import json 
import boto3
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Handle greeting intent
def greeting_intent_behavior(intent_request):
     return {
            "sessionState": {
                "dialogAction": {
                    "type": "ElicitIntent"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Hey! How can I help you?"
                }
            ]
        }

# Handle thankyou intent
def thankyou_intent_behavior(intent_request):
    return {
            "sessionState": {
                "dialogAction": {
                    "type": "ElicitIntent"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Happy to help! See you later!"
                }
            ]
        }



# Validation functions
def isvalid_city(city):
    valid_cities = ['new york', 'los angeles', 'chicago', 'houston', 'philadelphia', 'phoenix', 'san antonio',
                    'san diego', 'dallas', 'san jose', 'austin', 'jacksonville', 'san francisco', 'indianapolis',
                    'columbus', 'fort worth', 'charlotte', 'detroit', 'el paso', 'seattle', 'denver', 'washington dc',
                    'memphis', 'boston', 'nashville', 'baltimore', 'portland']
    return city.lower() in valid_cities

def isvalid_cuisine_type(cuisine_type):
    cuisine_types = ['chinese', 'indian', 'italian']
    return cuisine_type.lower() in cuisine_types
    
def isvalid_numpeople(number):
    number_types = ['1','2','3','4','5','6','7','8','9','10','one','two','three','four','five','six','seven','eight','nine','ten']
    return number.lower() in number_types

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def is_valid_time(date, time):
    return (dateutil.parser.parse(date).date() > datetime.date.today()) or (
            dateutil.parser.parse(date).date() == datetime.date.today() and dateutil.parser.parse(
        time).time() > datetime.datetime.now().time())

def isvalid_email(email):
        if(email.endswith('nyu.edu') or email.endswith('gmail.com')):
            return True
        return False

# User input Validation
def validate_reco_input(slots):
    location = try_ex(lambda: slots['Location'])
    cuisine_type = try_ex(lambda: slots['Cuisine'])
    reco_date = try_ex(lambda: slots['Date'])
    reco_time = try_ex(lambda: slots['Time'])
    num_people = try_ex(lambda: slots['NumPeople'])
    email = try_ex(lambda: slots['Email'])
    print(slots)
    print(location)
    
    if location and not isvalid_city(location['value']['originalValue']):
        return build_validation_result(
            False,
            'Location',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(location['value']['originalValue'])
        )

    if reco_date and not isvalid_date(reco_date['value']['interpretedValue']):
            return build_validation_result(False, 'Date', 'I did not understand the date.  When would you like to check in?')
      
    if cuisine_type and not isvalid_cuisine_type(cuisine_type['value']['originalValue']):
        return build_validation_result(False, 'Cuisine', 'I did not recognize that cuisine.  Would you like to have Italian, Indian or Chinese?')
    
    if num_people and not isvalid_numpeople(num_people['value']['originalValue']):
        return build_validation_result(False, 'NumPeople', 'Please enter a number Below 10')
    
    if email and not isvalid_email(email['value']['originalValue']):
        return build_validation_result(False, 'Email', 'Please enter a valid Email address (Only nyu or gmail ids)')
    
    if reco_time is not None and reco_date is not None:
        if not is_valid_time(reco_date['value']['interpretedValue'], reco_time['value']['interpretedValue']):
            return build_validation_result(False,'Time','Please enter time in the future. Suggestions cannot be given for the time in past')
        
    return {'isValid': True}

# Handle Dining Suggestions Intent
def dining_intent_behavior(intent_request):
    
    location = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Location'])
    reco_date = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Date'])
    reco_time = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Time'])
    num_people = try_ex(lambda: intent_request['sessionState']['intent']['slots']['NumPeople'])
    cuisine_type = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Cuisine'])
    email = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Email'])
    
    session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState']['sessionAttributes'] is not None else {}

    # Load confirmation history and track the current reservation.
    reco_input_info = json.dumps({
        'Location': location,
        'Cuisine': cuisine_type,
        'Date': reco_date,
        'Time': reco_time,
        'NumPeople': num_people,
        'Email': email
    })
    session_attributes['currentInputData'] = reco_input_info
    
    slots = intent_request['sessionState']['intent']['slots']
    print(slots)
    intent = intent_request['sessionState']['intent']['name']
    order_validation_result = validate_reco_input(slots)
    if intent_request['invocationSource'] == 'DialogCodeHook':
        if not order_validation_result['isValid']:
            if 'message' in order_validation_result:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": order_validation_result['invalidSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            "name": intent,
                            "slots": slots
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": order_validation_result['message']
                        }
                    ]
                }
            else:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": order_validation_result['invalidSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            "name": intent,
                            "slots": slots
                        }
                    }
                }
        else:
            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "Delegate"
                    },
                    "intent": {
                        'name': intent,
                        'slots': slots
                    }
                }
            }
        
    if intent_request['invocationSource'] == 'FulfillmentCodeHook':
        send_recommendations(intent_request)
        return {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent,
                    "slots": slots,
                    "state": "Fulfilled"
                }

            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Recommendations are sent to your email!"
                }
            ]
        }

# Send Recommendations
def send_recommendations(intent_request):
    client = boto3.client('sqs')
    
    slots = intent_request['sessionState']['intent']['slots']
    location = slots["Location"]
    cuisine = slots["Cuisine"]
    people = slots["NumPeople"]
    date  =  slots["Date"]
    time  =  slots["Time"]
    email= slots["Email"]
    response = client.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/353244348651/LexV2SlotsQueue',
        MessageAttributes={
                    'cuisine': {
                        'DataType': 'String',
                        'StringValue': cuisine['value']['originalValue']
                    },
                    'location': {
                        'DataType': 'String',
                        'StringValue': location['value']['originalValue']
                    },
                    'people': {
                        'DataType': 'String',
                        'StringValue': people['value']['originalValue']
                    },
                    'date': {
                        'DataType': 'String',
                        'StringValue': date['value']['interpretedValue']
                    },
                    'time': {
                        'DataType': 'String',
                        'StringValue': time['value']['interpretedValue']
                    },
                    'email': {
                        'DataType': 'String',
                        'StringValue': email['value']['originalValue']
                    }
            
        },
        MessageBody=("user"),
    )
    print(response)
    logger.debug("SQS mssg sent")



def dispatch(intent_request):
    intent_name = intent_request['sessionState']['intent']['name']
    if intent_name == 'GreetingIntent':
        # print("GreetingIntent Func")
        return greeting_intent_behavior(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thankyou_intent_behavior(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return dining_intent_behavior(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    # TODO implement
    print(event)
    return dispatch(event)

# Helper functions
def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None
    
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "invalidSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'invalidSlot': violated_slot,
        'message': message_content
    }