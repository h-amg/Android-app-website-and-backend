from flask import Blueprint
from flask import make_response
from flask import jsonify
from flask import request as flrqst
import time
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from twilio.jwt.access_token.grants import VideoGrant



twilio_blueprint = Blueprint('twilio', __name__,)


## twilio credentials
account_sid = 'account id'
api_key = 'api key'
api_secret = 'api secret'



# get chat access token from twilio backend server
## user identity = monogdb stitch userid
def get_chat_token(identity):

	# Create access token with credentials
	token = AccessToken(account_sid, api_key, api_secret, identity=identity)

	# required for Chat grants
	service_sid = 'service id'

	# Create an Chat grant and add to token
	chat_grant = ChatGrant(service_sid=service_sid)
	token.add_grant(chat_grant)

	token = token.to_jwt().decode('utf-8')

	return token


# get Video access token from twilio backend server
## user identity here is the monogdb stitch userid
def get_video_token(identity, roomName):

	# Create access token with credentials
	token = AccessToken(account_sid, api_key, api_secret, identity=identity)

	# Create a Video grant and add to token
	video_grant = VideoGrant(room=roomName)
	token.add_grant(video_grant)

	token = token.to_jwt().decode('utf-8')

	return token





# process client request
def request_processor():
	# start timer
	start = time.time()

	# build a request object to fetch hhttp request at webhook end
	req = flrqst.get_json(force=True)
	print ('request object: ' +  str(req))

	try:
		identity = req.get('identity')
		# print('identity found: ' + str(identity))
		if identity is None:
			print('Error identity not found')
	except Exception as e:
		identity = None
		print(e + '@identity')

	try:
		roomName = req.get('roomName')
		# print('roomName found: ' + str(roomName))
		if roomName is None:
			print('RoomName not found')
	except Exception as e:
		roomName = None
		print(e + '@roomName')

	try:
		chat = req.get('chat')
		# print('chat found: ' + str(chat))
		if chat is None:
			chat = False
			print('Chat not found')
	except Exception as e:
		chat = False
		print(e + '@chat')

	try:
		video = req.get('video')
		# print('video found: ' + str(video))
		if video is None:
			video = False
			print('Video not found')
	except Exception as e:
		video = False
		print(e + '@video')


	## Check which kind of token is requested
	if chat:
		print('Generating chat token')
		token = get_chat_token(identity)
	elif video:
		print('Generating video token')
		token = get_video_token(identity, roomName)

	# print("token generated: " + token)

	response = {"token": token}

	end = time.time()
	print('Token generated in: {} seconds'.format(end - start))

	return response


# create a route for twilio token request fulfillment
@twilio_blueprint.route('/twilio_access_token_endpoint', methods=['GET', 'POST'])
def billing():
	print("Twilio token requested")
	# return response when twilio is triggered
	return make_response(jsonify(request_processor()))
