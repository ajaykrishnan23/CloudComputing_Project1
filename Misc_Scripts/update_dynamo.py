import boto3
import csv
import time
dynamodb = boto3.client('dynamodb')
table_name = '######'

with open('yelpScrape.csv', 'r') as csvfile:
    csvreader = csv.DictReader(csvfile)
    for row in csvreader:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'bID': {'S': row['bID']},
                'name': {'S': row['name']},
                'cuisine':{'S': row['cuisine']},
                'address': {'S': row['address']},
                'coordinates':{'S': row['cord']},
                'numOfReview':{'N': str(row['numOfReview'])},
                'rating':{'N': str(row['rating'])},
                'zipcode':{'N': str(row['zipcode'])},
                'insertedAtTimestamp':{'N': str(time.time())}
            }
        )
