from flask import Blueprint
from flask import make_response
from flask import jsonify
from flask import request as flrqst
import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import *
from google.cloud import pubsub_v1
import pymongo
from pymongo import MongoClient



billing_blueprint = Blueprint('billing', __name__,)

###========================================initialize MongoFB Atlas=====================================#########
client = MongoClient('insert mongodb client uri here')
db = client.xhominid_app ## initiate DB
purchases = db.purchases ## initiate purchases collection
subs = db.subscriptions ## initiate subscriptions collection
###========================================initialize MongoFB Atlas=====================================#########


### TODO: 
## add billing verification (send get request to google play server with purchase token for purchase expiry status check)


# send messages to playBilling pub/sub topic 
def verifyToken(token):
	project_id = "project id"
	topic_name = "topic name"

	publisher = pubsub_v1.PublisherClient()
	# Creates a fully qualified identifier
	topic_path = publisher.topic_path(project_id, topic_name)
    # encode token string  as utf-8 must be a bytestring
	data = token.encode('utf-8')
    # When you publish a message, the client returns a future.
	future = publisher.publish(topic_path, data=data)
	print('Published message. future: {}'.format(future.result()))

	subscription_name = "billing"

	subscriber = pubsub_v1.SubscriberClient()
	# Creates a fully qualified identifier
	subscription_path = subscriber.subscription_path(project_id, subscription_name)

	result = subscriber.subscribe(subscription_path, callback=callback)

	# The subscriber is non-blocking. We must keep the main thread from
	# exiting to allow it to process messages asynchronously in the background.
	print('Listening for messages on {}'.format(subscription_path))
	time.sleep(60)

	return result



# receive messages
def callback(message):
    print('Received message: {}'.format(message))
    # acknowledges received mesages
    message.ack()
    if message.attributes:
    	print('Attributes:')
    	for key in message.attributes:
    		value = message.attributes.get(key)
    		print('{}: {}'.format(key, value))


	



def fulfillPurchase(uId, purchaseToken, orderId, purchaseName, prdouctId, purchaseDate, expirydate):
	## add document to mongodb fulfillment
	purchases.insert_one({
	    u'uId': uId,
	    u'purchaseToken': purchaseToken,
	    u'orderId': orderId,
	    u'purchaseName': purchaseName,
	    u'prdouctId': prdouctId,
	    u'purchaseDate': purchaseDate,
	    u'expirydate': expirydate,
	    })


	## add document to mongodb fulfillment
	subs.insert_one({
	    u'uId': uId,
	    u'subexpiry': expirydate,
	    u'valid': True,
	    })

	# TODO: check if insertion was successful
	return True, True



# process client request
def request_processor():
	# start timer
	start = time.time()

	# build a request object to fetch hhttp request at webhook end
	req = flrqst.get_json(force=True)
	print ('request object: ' +  str(req))


	try:
		uId = req.get('purchase').get('uId')
		if uId is None:
			print('Error user id not found')
	except Exception as e:
		uId = None
		print(e + '@uId')

	try:
		purchaseToken = req.get('purchase').get('purchaseToken')
		if purchaseToken is None:
			print('Error purchaseToken not found')
	except Exception as e:
		purchaseToken = None
		print(e + '@purchaseToken')

	try:
		orderId = req.get('purchase').get('orderId')
		if orderId is None:
			print('Error orderId not found')
	except Exception as e:
		orderId = None
		print(e + '@orderId')

	try:
		purchaseName = req.get('purchase').get('purchaseName')
		if purchaseName is None:
			print('Error purchaseName not found')
	except Exception as e:
		purchaseName = None
		print(e + '@purchaseName')

	try:
		prdouctId = req.get('purchase').get('prdouctId')
		if prdouctId is None:
			print('Error prdouctId not found')
	except Exception as e:
		prdouctId = None
		print(e + '@prdouctId')

	try:
		purchaseDate = req.get('purchase').get('purchaseDate')
		if purchaseDate is None:
			print('Error purchaseDate not found')
	except Exception as e:
		purchaseDate = None
		print(e + '@purchaseDate')

	try:
		expirydate = req.get('purchase').get('expirydate')
		if expirydate is None:
			print('Error expirydate not found')
	except Exception as e:
		expirydate = None
		print(e + '@expirydate')

	result = {'verified': False, 'fulfilled': False, 'message': 'Error handling request'}
	# if one of the arguments is null/None
	if uId == None or purchaseToken == None or orderId == None or purchaseName == None or prdouctId == None or purchaseDate == None:
		result = {'verified': False, 'fulfilled': False, 'message': 'Error with purchase fulfillment'}
	else:
		# complete verified purchase token (add recurrsion to handle failure insrting purchase documents)
		verified, fulfilled = fulfillPurchase(uId, purchaseToken, orderId, purchaseName, prdouctId, purchaseDate, expirydate)
		result = {'verified': verified, 'fulfilled': fulfilled, 'message': 'verification and fulfillment successful'}

	end = time.time()
	print('runtime: {}'.format(end - start))

	return result


# create a route for billing
@billing_blueprint.route('/billing_endpoint', methods=['GET', 'POST'])
def billing():
	print("billing running")
	# return response when billing is triggered
	return make_response(jsonify(request_processor()))