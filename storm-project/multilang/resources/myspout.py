from storm import Spout, emit, log
import time
import datetime
from random import randrange

from kafka.client import KafkaClient
from kafka import SimpleClient, SimpleConsumer
from kafka.consumer import KafkaConsumer
from kafka.producer import SimpleProducer


client = SimpleClient("")
consumer = SimpleConsumer(client, "my-group", "COMPANY_SENTIMENT")


def getData():
    data = consumer.get_messages(count=1, block=True, timeout=5)
    try:
        return data[0][1].value
    except:
	    return "nothing"

class MySpout(Spout):
    def nextTuple(self):
        data = getData()
        if (data != "nothing"):
            emit([data])

MySpout().run()
