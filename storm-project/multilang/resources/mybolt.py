import storm
from datetime import date
import time
import datetime
import boto3

import json
import re

AWS_KEY=""
AWS_SECRET=""
REGION=""

today = date.today()

TERMS = {}

sent_file = open('AFINN-111.txt')
sent_lines = sent_file.readlines()
for line in sent_lines:
	s = line.split("\t")
	TERMS[s[0]] = s[1]

sent_file.close()


conn_db = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)

def analyzeData(data):
    text = re.sub('[!@#$)(*<>=+/:;&^%#|\{},.?~`]', '', data)
    splitTweet = text.split()

    sentiment = 0.0

    for word in splitTweet:
       if TERMS.has_key(word):
           sentiment = sentiment + float(TERMS[word])

    return sentiment


class MyBolt(storm.BasicBolt):
    def process(self, tup):
        data = tup.values[0]

        data = data.split('|')
        timestamp = str(data[0])
        company = data[1]
        text = data[2]
        error = 0

        score = analyzeData(text)

        result= str(score)

        #Store analyzed results in DynamoDB
        try:
            table = conn_db.Table("Stock_Sentiment")
            table.put_item(
                Item={
                    "timestamp": timestamp,
                    "text": text,
                    "score": result,
                    "topic": company
                }
            )
        except:
            error = 1

        storm.emit([result])


MyBolt().run()
