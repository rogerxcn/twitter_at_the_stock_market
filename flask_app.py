from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
import urllib2
import boto3
from boto3.dynamodb.conditions import Key, Attr
import datetime
import operator
import time
import json
from iexfinance import Stock

app = Flask(__name__)

#-------Connect to DynamoDB---------
AWS_KEY=""
AWS_SECRET=""
REGION=""

conn_db = boto3.resource('dynamodb', aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET,
                            region_name=REGION)

table = conn_db.Table("Stock_Sentiment")
#-----------------------------------

@app.route('/')
def tweet_home():

    #Scan DynamoDB table
    current_time = int(time.time() * 1000)
    start_time = int(current_time - 8.64e7)
    results = table.scan(
        FilterExpression=Key('timestamp').between(str(start_time), str(current_time))
    )
    stock_dict = {}

    for result in results['Items']:
        stock_name = str(result['topic'])
        #print stock_name
        if stock_name in stock_dict:
            stock_dict[stock_name][0] += float(result['score'])
        else:
            stock_dict[stock_name] = []
            fin_data = Stock(stock_name).get_key_stats()
            price = Stock(stock_name).get_price()
            #print fin_data.get_key_stats()
            stock_dict[result['topic']].append(float(result['score']))
            stock_dict[result['topic']].append(price)
            stock_dict[result['topic']].append(fin_data['day5ChangePercent'])

    list_of_data = []

    for item in sorted(stock_dict.iterkeys()):
        data = {}
        data["name"] = item
        data["senti"] = str(stock_dict[item][0])
        # data["senti"] = -1
        data["cprice"] = str(stock_dict[item][1])
        data["fdprice"] = str(stock_dict[item][2])
        list_of_data.append(data)


    return render_template('main.html', list_of_data=list_of_data)

@app.route('/api/get_tweet_by_time/<name>/<start>/<end>', methods=['POST'])
def api_get_tweet_by_time(name, start, end):
    start = str(start)
    end = str(end)

    results = table.scan(
        FilterExpression=Key('timestamp').between(start, end)
    )

    data = []

    for result in results['Items']:
        stock_name = str(result['topic'])
        times = int(result['timestamp'])
        #print stock_name
        if stock_name == name:
            data.append([times, float(result['score'])])

    data.sort(key=lambda x: x[0])

    return json.dumps(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
