from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import tweepy

from random import randrange
import time
import json
import datetime
from threading import Thread

from datetime import date
import boto3

import re

from kafka.client import KafkaClient
from kafka import SimpleClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer




AWS_KEY=""
AWS_SECRET=""
REGION="us-east-2"
direct = False




access_tokens = [
                "",
                "",
                "",
                ""
                ]

access_token_secrets = [
                        "",
                        "",
                        "",
                        ""
                        ]

consumer_keys = [
                "",
                "",
                "",
                ""
                ]

consumer_secrets = [
                    "",
                    "",
                    "",
                    ""
                    ]

current_token = 0

company_list = ["NVDA", "AAPL", "AMD", "IBM", "MSFT", "TSLA"]

client = SimpleClient("")
producer = SimpleProducer(client)




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





def publish(data, name):
    data = json.loads(data)
    if (data["lang"] != "en"):
        pass
    timestamp = data["timestamp_ms"]
    text = data["text"]
    if "|" in text:
        return True
    payload = str(timestamp) + "|" + name + "|" + text
    print payload


    if (direct):
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
                    "topic": name
                }
            )
        except:
            error = 1


    try:
        producer.send_messages("COMPANY_SENTIMENT", payload.encode('utf-8'))
    except:
        print "this throws an error"
    return True






class StdOutListener(StreamListener):

    target_company = ""

    def set_company(self, name):
        self.target_company = name

    def on_data(self, data):
        #print data
        publish(data, self.target_company)
        return True

    def on_error(self, status):
        print status

def create_listener(company):
    consumer_key = consumer_keys[current_token]
    consumer_secret = consumer_secrets[current_token]
    access_token = access_tokens[current_token]
    access_token_secret = access_token_secrets[current_token]

    global current_token
    current_token = current_token+1 if current_token < 3 else 0

    l = StdOutListener()
    l.set_company(company)
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)

    #This line filter Twitter Streams to capture data by the keywords
    stream.filter(track=[company], languages=["en"], async=True)


if __name__ == '__main__':
    print 'Listening...'
    threads = []
    #This handles Twitter authetification and the connection to Twitter Streaming API
    for company in company_list:
        launch = True
        while (launch):
            try:
                t = Thread(target=create_listener, args=(company,))
                threads.append(t)
                t.start()
                time.sleep(15)

            except (tweepy.error.RateLimitError):
                print "420 detected"
                time.sleep(60)
                continue

            launch = False


    for t in threads:
        t.join()
