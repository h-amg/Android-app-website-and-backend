# import flask dependencies
from flask import Flask
from flask import Blueprint
from app.mod_webhook.lib import *
from flask import make_response
from flask import jsonify
from flask import request as flrqst
import requests as apirequest
import string
import random
import datetime
import time
from pytz import timezone
import pymongo
from pymongo import MongoClient
from bson import ObjectId
import re
import uuid
import firebase_admin
from firebase_admin import messaging
from firebase_admin import auth

webhook_blueprint = Blueprint('webhook', __name__,)

#+++++++++++++++++++++++++++++++++++++++++++++++++++measurements URIs===========================================================####

ounce = "http://www.edamam.com/ontologies/edamam.owl#Measure_ounce"
gram = "http://www.edamam.com/ontologies/edamam.owl#Measure_gram"
pound = "http://www.edamam.com/ontologies/edamam.owl#Measure_pound"
kilogram = "http://www.edamam.com/ontologies/edamam.owl#Measure_kilogram"
pinch = "http://www.edamam.com/ontologies/edamam.owl#Measure_pinch"
liter = "http://www.edamam.com/ontologies/edamam.owl#Measure_liter"
fluid_ounce = "http://www.edamam.com/ontologies/edamam.owl#Measure_fluid_ounce"
gallon = "http://www.edamam.com/ontologies/edamam.owl#Measure_gallon"
pint = "http://www.edamam.com/ontologies/edamam.owl#Measure_pint"
quart = "http://www.edamam.com/ontologies/edamam.owl#Measure_quart"
milliliter = "http://www.edamam.com/ontologies/edamam.owl#Measure_milliliter"
drop = "http://www.edamam.com/ontologies/edamam.owl#Measure_drop"
cup = "http://www.edamam.com/ontologies/edamam.owl#Measure_cup"
tbsp = "http://www.edamam.com/ontologies/edamam.owl#Measure_tablespoon"
tsp = "http://www.edamam.com/ontologies/edamam.owl#Measure_teaspoon"
# measurements uri object
measurements = {"ounce":ounce, "gram": gram, "pound":pound, "kilogram":kilogram, "pinch":pinch, "liter":liter, "fluid_ounce":fluid_ounce, "gallon":gallon, "pint":pint, "quart":quart, "milliliter":milliliter, "drop":drop, "cup":cup, "tbsp":tbsp, "tsp":tsp}

#+++++++++++++++++++++++++++++++++++++++++++++++++++measurements URIs===========================================================####



###========================================initialize MongoFB Atlas=====================================#########
client = MongoClient('insert mongodb cliet uri here')
db = client.xhominid ## initiate DB
## initialize collections
users = db.users
diets = db.diets
meals = db.meals
dailyMacs = db.dailyMacs
recipes = db.recipes
recomnds = db.recomnds
registerations = db.newRegisters
sessions = db.consultingSessions
###========================================initialize MongoFB Atlas=====================================#########



###===================================================intialize Firebase==============================================###
firebase_admin.initialize_app()
###===================================================intialize Firebase==============================================###




# request a nutritionts for the user
def assign_nutritionist(userId):

	userDiet = diets.find_one({'uId':userId})
	if userDiet:
		hasNutritionist = userDiet.get('hasNutritionist')
	else:
		print('Error! user diet Doc not found')
		return False

	if not hasNutritionist:

		# ----=> add finding a nutritionist algorithm and get info

		# update user diet document
		diets.update_one({'uId':userId}, {'$set': {'hasNutritionist': True}})

		# add new registeration record
		registerations.insert_one({
			u'uId': userId,
		    u'acknowledged': False,
		    u'consultantId': 'insert_default_nutritionist_id',
		    u'timestamp': datetime.datetime.utcnow(),
		    })

		# create a new initial session
		create_session(userId, 'insert_default_nutritionist_id')

		# notify admin
		admin_user = users.find_one({'uId':'insert_adminId'})
		registration_token = admin_user.get('messagingToken')
		# print('token found: {}'.format(registration_token))

		if registration_token:
			# send message to admin using admin registeration token
			message = messaging.Message(
				data = {
				'title': 'New user signed up',
				'text': 'Id: {}'.format(userId),
				'id': '007',
				'isSessNotif': 'true',
				'delay': '1000',
				},
				token = registration_token,
				)
			# Send a message to the device corresponding to the provided
			# registration token.
			messaging.send(message)
		else:
			print('Error! Admin messaging token not found')

		return True
	else:
		return False


### find user diet
### 'diet_Id' is an ObjectId data type
def diets_id(userId):
	print("user id: {} @diets_id".format(userId))

	## check if user with specified id exists
	user  = users.find_one({'uId':userId})

	if not user:
		print ("user doc not found for user: {} @diets_id".format(userId))
		return
	else:
		diet_Id = user.get('dietId')
		print("old diet doc id: {} @diets_id".format(diet_Id))
		if not diet_Id:
			new_doc = diets.insert_one({})
			diet_Id = str(new_doc.inserted_id)
			print("new diet doc id: {} @diets_id".format(diet_Id))
			users.update_one({'uId':userId}, {'$set': {'dietId': diet_Id}})
		
		return diet_Id
			




def daily_macros_id(userId, timeZone):
	# print ('timezone: {} @daily_macros_id'.format(timeZone))
	### ++++++++++++++++++++++++++++++++++++++++++set time constraints for querying++++++++++++++++++++++++++++++++++++++++++ ###
	# get machine current date
	day = datetime.datetime.now().day
	month = datetime.datetime.now().month
	year = datetime.datetime.now().year
	tZ = timezone(timeZone)

	# set day boundaries (adjusted for client device timezone)
	day_start = tZ.localize(datetime.datetime(year, month, day, 0, 0, 0, 0))
	day_end = tZ.localize(datetime.datetime(year, month, day, 23, 59, 59, 999999))
	### ++++++++++++++++++++++++++++++++++++++++++set time constraints for querying++++++++++++++++++++++++++++++++++++++++++ ###

	# Returns the document with today's macros
	doc_query = dailyMacs.find_one({'$and': [{ 'timestamp': { '$gte': day_start, '$lte': day_end } }, { 'uId': userId } ]})

	# if the user has no diet document in the database generate a random unique id
	if not doc_query:
		# day_macros document doesn't exists,thus create doc
		foundDoc = False  
		found = False
		return found, foundDoc
	else:
		# day_macros document exists,thus found doc
		foundDoc = doc_query
		# print ('found dailyMAc docuemnt id: {} @daily_macros_id'.format(doc_query.get('_id')))
		found = True
		return found, foundDoc





# calculate user daily caloric intake
# @param   String  gender = "f" for felam or "m" for male [user gender]
# @param   int     age [user age]
# @param   int     wight [user weight]
# @param   int     height [user height]
# @param   int     activity_modifier [iser activity modifier index]
# @param   String  goal = "gain", "lose", "maintain" or "bulk" [user dietary goal]
# @return  int     calories
def calori_intake(gender, age, weight, height, activity_modifier, goal):
	
	# set s value 
	if gender == "m":
		s = 5
	elif gender =="f":
		s = -161
	else:
		print("Error: can't find user gender to calculate s value")
	
	# get BMR (Basal metabolic rate)
	bmr = (10 * weight) + (6.25 * height) - (5 * age) + s
	
	# get Calories from BMR
	calories = bmr * activity_modifier

	# modify caloric intake based on user dietary goal [when goal = "maintain" or "bulk" calories remain the same]
	if goal =="gain":
		calories = calories + (calories * 0.07)
	elif goal =="lose":
		calories = calories - (calories * 0.05)

	return calories



# calculate the daily  macro quantity in grams for user diet plan
# @param  int      calories [the calculated user caloric intake]
# @param  String   goal = "gain", "lose", "maintain" or "bulk" [user dietary goals]
# @return json     macros = {"protein":<int in grams>, "carbs":<int in grams>, "fat":<int in grams>}
def macros_intake(calories, goal):

	# calculate macro in grams for weight gain
	if goal == "gain":
		protein = (0.2 * calories) / 4
		fat   = (0.3 * calories) / 9
		carbs   = (0.5 * calories) / 4
	
	# calculate macro amount for weight loss
	elif goal == "lose":
		protein = (0.3 * calories) / 4
		fat   = (0.2 * calories) / 9
		carbs   = (0.5 * calories) / 4
	
	# calculate macro amount for maintaining weight
	elif goal == "maintain":
		protein = (0.25 * calories) / 4
		fat   = (0.25 * calories) / 9
		carbs   = (0.5 * calories) / 4
	# calculate macro amount for bulking (muscle mass gain)
	elif goal == "bulk":
		protein = (0.35 * calories) / 4
		fat   = (0.15 * calories) / 9
		carbs   = (0.5 * calories) / 4

	macros = {"protein":protein, "fat":fat, "carbs":carbs}
	return macros


## @param reference is the user document firestore refernce object 
def user_info(userId):

	# get user document from DB
	user = users.find_one({'uId': userId}) 

	# Check if document was found
	if not user:
		return None

	# fetch user info from database and set it as @param gender, age, weight, height, activity_modifier, goal
	user_id            = user.get('uId')
	gender             = user.get('gender')
	age                = user.get('age')
	weight             = user.get('weight')
	height             = user.get('height')
	activity_modifier  = user.get('activity_modifier')
	goal               = user.get('goal')
	diet               = user.get('dietId')

	doc = {"gender": gender, "age": age, "weight": weight, "height": height, "activity_modifier": activity_modifier, "goal": goal, "diet": diet, "uId": user_id} 
	return doc





def today_macros(userId, timeZone):

	# get macro doc id 
	isfound, foundDoc = daily_macros_id(userId, timeZone)

	# check if there is a daily macro document creted for today
	if isfound:

		# fetch user info from database and set it as @param gender, age, weight, height, activity_modifier, goal
		consumed_calories  = foundDoc.get('consumed_calories')
		consumed_protein   = foundDoc.get("consumed_macros").get('protein')
		consumed_fat       = foundDoc.get("consumed_macros").get('fat')
		consumed_carbs     = foundDoc.get("consumed_macros").get('carbs')

		return {"calories": consumed_calories, "protein": consumed_protein, "fat": consumed_fat, "carbs": consumed_carbs}
		
	else:
		dailyMacs.insert_one({
	    u'consumed_calories': 0,
	    u'consumed_macros':{
	    u'protein': 0,
	    u'fat': 0,
	    u'carbs': 0,
	    },
	    u'no_meals': 0,
	    u'timestamp': datetime.datetime.utcnow(),
	    u'uId': userId,
	    })
		return None
		


def user_diet(userId):
	# print("user_diet reiggered")

	diet_doc = diets.find_one({'uId': userId})

	if diet_doc:
		# fetch user info from database and set it as @param gender, age, weight, height, activity_modifier, goal
		target_calories  = diet_doc.get('target_calories')
		target_protein  = diet_doc.get('target_protein')
		target_fat  = diet_doc.get('target_fat')
		target_carbs  = diet_doc.get('target_carbs')

		if target_calories == None or target_protein == None or target_fat == None or target_carbs == None:
			print("targets not found")
			# create user diet plan
			set_diet_plan(userId)
			# get user diet plan
			diet_doc = diets.find_one({'uId': userId})
			if diet_doc:
				# fetch user info from database and set it as @param gender, age, weight, height, activity_modifier, goal
				target_calories  = diet_doc.get('target_calories')
				target_protein  = diet_doc.get('target_protein')
				target_fat  = diet_doc.get('target_fat')
				target_carbs  = diet_doc.get('target_carbs')
				return {"calories":target_calories, "protein":target_protein, "fat":target_fat, "carbs":target_carbs}
			else:
				return

		return {"calories":target_calories, "protein":target_protein, "fat":target_fat, "carbs":target_carbs}
	else:
		set_diet_plan(userId)
		# get user diet plan
		diet_doc = diets.find_one({'uId': userId})
		if diet_doc:
			# fetch user info from database and set it as @param gender, age, weight, height, activity_modifier, goal
			target_calories  = diet_doc.get('target_calories')
			target_protein  = diet_doc.get('target_protein')
			target_fat  = diet_doc.get('target_fat')
			target_carbs  = diet_doc.get('target_carbs')
			return {"calories":target_calories, "protein":target_protein, "fat":target_fat, "carbs":target_carbs}





def get_recipe(recipeID):

	recipe = recipes.find_one({'recipeid': recipeID})
	
	if recipe:
		recipename = recipe.get('recipename')
		protein = recipe.get('protein')
		fat = recipe.get('fat')
		carbs = recipe.get('carbs')
		calories = recipe.get('calories')

		macros = {'recipename': recipename, 'protein': protein, 'fat': fat, 'carbs': carbs, 'calories': calories}
		return macros
	else:
		print('recipe not found! recipe: {} @get_recipe'.format(recipe))
		return None


# mark user recommended recipe as eaten
def mark_eaten(recomndID, uId):

	recomnds.update_one({'$and':[{"_id": ObjectId(recomndID)}, {'uId': uId}]},
		{'$set': {
		'eaten': True,
		}})
	



def remaining_macros(userid, timeZone):

	# Get user diet
	diet = diets.find_one({'uId': userId})

	target_calories  = diet.get('calories')
	target_protein  = diet.get('protein')
	target_fat  = diet.get('fat')
	target_carbs  = diet.get('carbs')

	# get users current day consumed macros (consumed_calories, consumed_protein, consumed_fat, consumed_carbs)
	consumed_macros = today_macros(userId, timeZone)
	if consumed_macros is None:
		consumed_calories = 0
		consumed_protein = 0
		consumed_fat = 0
		consumed_carbs = 0
	else:
		consumed_calories = consumed_macros.get('calories')
		consumed_protein = consumed_macros.get('protein')
		consumed_fat = consumed_macros.get('fat')
		consumed_carbs = consumed_macros.get('carbs')

	remaining_calories  = target_calories - consumed_calories
	remaining_protein  = target_protein - consumed_protein
	remaining_fat  = target_fat - consumed_fat
	remaining_carbs  = target_carbs - consumed_carbs

	return {"calories": remaining_calories, "protein": remaining_protein, "fat": remaining_fat, "carbs": remaining_carbs}




# food macros to target macros ratio
def food_tar_rat(calories, protein, fat, carbs, userId):

	# get json object of user diet plan target macros
	diet = user_diet(userId)
	
	if diet is not None:
		target_calories  = diet.get('calories')
		target_protein  = diet.get('protein')
		target_fat  = diet.get('fat')
		target_carbs  = diet.get('carbs')

		calories_rat  = (calories/target_calories)*100
		protein_rat  = (protein/target_protein)*100
		fat_rat  = (fat/target_fat)*100
		carbs_rat  = (carbs/target_carbs)*100

		ratios = {"calories": calories_rat, "protein": protein_rat, "fat": fat_rat, "carbs": carbs_rat}
		return ratios

	else:
		return None
	
	



# consumed macros to target macros ratio
def cons_tar_rat(userId, timeZone):

	# get user current day consumed macros
	consumed_macros   = today_macros(userId, timeZone)
	if consumed_macros is None:
		consumed_calories = 0
		consumed_protein = 0
		consumed_fat = 0
		consumed_carbs = 0
	else:
		consumed_calories = consumed_macros.get("calories")
		consumed_protein  = consumed_macros.get("protein")
		consumed_fat      = consumed_macros.get("fat")
		consumed_carbs    = consumed_macros.get("carbs")

	# print ('consumed_calories: {}, consumed_protein: {}, consumed_fat: {}, consumed_carbs:{} @cons_tar_rat'.format(consumed_calories, consumed_protein, consumed_fat, consumed_carbs))

	# get user diet target macros
	target_macro    = user_diet(userId)
	target_calories = target_macro.get("calories")
	target_protein  = target_macro.get("protein")
	target_fat      = target_macro.get("fat")
	target_carbs    = target_macro.get("carbs")

	# print ('target_calories: {}, target_protein: {}, target_fat: {}, target_carbs:{} @cons_tar_rat'.format(target_calories, target_protein, target_fat, target_carbs))

	# calculate consumed to target macro ratios
	calories_rat    = (consumed_calories/target_calories)*100
	protein_rat    = (consumed_protein/target_protein)*100
	fat_rat    = (consumed_fat/target_fat)*100
	carbs_rat    = (consumed_carbs/target_carbs)*100

	return {"calories": calories_rat, "protein": protein_rat, "fat": fat_rat, "carbs": carbs_rat}



## user diet @ param idx is an arbitrary value used to evalued food item suitability for use diet
def diet_idx(food, userId, timeZone):

	# get food macros
	food_Calories = food.get("calories")
	food_protein = food.get("protein")
	food_fat = food.get("fat")
	food_carbs = food.get("carbs")
	# print ('food_Calories: {}, food_protein: {}, food_fat: {}, food_carbs:{} @diet_idx'.format(food_Calories, food_protein, food_fat, food_carbs))

	# get food macros to target macros ratio
	food_target_ratio = food_tar_rat(food_Calories, food_protein, food_fat, food_carbs, userId)
	# print ('food_target_ratio: {} @diet_idx'.format(food_target_ratio))
	# get consumed macros to to target macros ratio
	consumed_target_ratio = cons_tar_rat(userId, timeZone)
	# print ('consumed_target_ratio: {} @diet_idx'.format(consumed_target_ratio))

	if food_target_ratio is None or consumed_target_ratio is None:
		return None
	else:
		# get the usere diet index based on the food macros and consumed macros
		idx = ((food_target_ratio.get("calories") + consumed_target_ratio.get("calories"))+ (food_target_ratio.get("protein") + consumed_target_ratio.get("protein") ) + (food_target_ratio.get("carbs") + consumed_target_ratio.get("carbs") ) + (food_target_ratio.get("fat") + consumed_target_ratio.get("fat") ))/4
		# print ('idx: {} @diet_idx'.format(idx))
		return idx



# provide macro status for food considered
# @param food json object (food macros)
# @param day_hour int (the hour of the day at which the query is made)
# @param userId string (user ID)
def day_macro_chk(food, day_hour, timeZone, userId):

	user_diet_idx = diet_idx(food, userId, timeZone)

	behind = False
	ahead = False
	on_track = False

	if 0 <= user_diet_idx <= 33:
		if day_hour <= 12:
			on_track = True
		elif day_hour > 12:
			behind = True

	elif 33 < user_diet_idx <= 66:
		if day_hour < 12:
			ahead = True
		elif 12 <= day_hour < 18:
			on_track = True
		elif day_hour >= 18:
			behind = True

	elif 66 < user_diet_idx <= 100:
		if day_hour < 18:
			ahead = True
		elif 18 <= day_hour < 24:
			on_track = True
	elif user_diet_idx > 100: 
		ahead = True


	status = {"behind": behind, "ahead": ahead, "on_track": on_track}
	return status
			


# {@param consultantId} 
def create_session(userId, consultantId):

	# ---===> add: fetching nutritionist's document here and get info
	# ---===> add: fetching users's document here and get info 

	# create new Consultation session for the user with default nutritionist
	sessions.insert_one({
		u'consulteeId': userId,
		u'consultantId': consultantId,
		u'consultantImgUrl': 'https//consultantImgUrl',
		u'consulteeImgUrl': 'None',
	    u'consultantName': 'Default nutritioinist',
	    u'consulteeName': 'None',
	    u'approved': False,
	    u'completed': False,
	    u'missed': False,
	    u'cancelled': False,
	    u'scheduled': False,
	    u'isNutritionist': True,
	    u'roomName': str(uuid.uuid4()),
	    u'timestamp': datetime.datetime.utcnow(),
	    u'lastModified': datetime.datetime.utcnow(),
		})




# set user dieat plan
# @return None
def set_diet_plan(userId):
	# print("set_diet_plan triggerred")

	user_data = user_info(userId)

	# fetch user info from database and set it as @param gender, age, weight, height, activity_modifier, goal
	gender              = user_data.get('gender')
	age                 = user_data.get('age')
	weight              = user_data.get('weight')
	height              = user_data.get('height')
	activity_modifier   = user_data.get('activity_modifier')
	goal                = user_data.get('goal')
	user_docId          = user_data.get('uId')
	# calculate user target caloric intake, and macros in grams.
	user_cloric_intake = calori_intake(gender, age, weight, height, activity_modifier, goal)
	diet_plan = macros_intake(user_cloric_intake, goal)

	protein = diet_plan.get("protein")
	carbs = diet_plan.get("carbs")
	fat = diet_plan.get("fat")

	# print("Macros calclated: protein= {}, fat= {}, carbs= {} @set_diet_plan".format(protein, carbs, fat))

	# get user diet id  and create new one if not available
	# diet_doc_id = diets_id(userId)
	diet_doc_id = str(diets.find_one({"uId":userId}).get("_id"))
	print("diet_doc_id:  {} @set_diet_plan".format(diet_doc_id))
	_id = ObjectId(diet_doc_id)

	# update user dietary targets
	diets.update_one({"_id": _id},
		{'$set': {
		'target_calories': user_cloric_intake,
		'target_protein': protein,
		'target_fat': fat,
		'target_carbs': carbs,
		'uId': str(user_docId)
		}})
		
	return diet_doc_id



def log_macros(food, value, measure, calories, protein, fat, carbs, timeZone, userId):

	## ensure Double numeric data types
	value = value + 0.0
	calories = calories + 0.0
	protein = protein + 0.0
	fat = fat + 0.0
	carbs = carbs + 0.0
	
	# log food item into daily meals record document
	meals.insert_one({
	    u'food': food,
	    u'macros':{
	    u'protein': protein,
	    u'fat': fat,
	    u'carbs': carbs,
	    },
	    u'calories': calories,
	    u'amount': {
	    u'value': value,
	    u'measure': measure,
	    },
	    u'timestamp': datetime.datetime.utcnow(),
	    u'uId': userId,
	})

	
	# get daily macro doc ID and check if already exist
	isFound, foundDoc = daily_macros_id(userId, timeZone)
	
	# add food item macros to today's macros' count
	if isFound:
		# print("macros document found")
		dailyMacs.update_one({'_id': foundDoc.get('_id')},
			{'$inc': {
			'consumed_macros.protein': + protein, 
			'consumed_macros.fat': + fat,
			'consumed_macros.carbs':+ carbs,
			'consumed_calories': + calories,
			'no_meals': +1
			}})
	else:
		# print("No dailymacros document found")
		dailyMacs.insert_one({
			'consumed_macros': {
			'protein': protein,
			'fat': fat,
			'carbs':carbs,
			},
			'consumed_calories': calories,
			'no_meals': 1,
			'timestamp': datetime.datetime.utcnow(),
			'uId': userId,
			})




	
def update_weight(weight, userid):
	
	### find user doc and update user weight
	users.update_one({'uId':userId},
		{'$set': {
		'weight': weight
		}})

	# set user diet plan
	set_diet_plan(userId)



def update_goal(goal, userid):

	### find user doc and update user weight
	users.update_one({'uId':userId },
		{'$set': {
		'goal': goal
		}})

	# set user diet plan
	set_diet_plan(userId)



# function to fetch queried_text macro value
# @param  String   food [food item extracted from the text]
# @param  int      quantity [food quantity extracted from the text]
# @param  String   measure [measurement unit extracted from the text]
# @return String   response [text sentence response to user]
def nutrients_val(food, quantity=None, measure=None):

	## clean up query text
	food = re.sub(r'[\(\)]','',food)
	food = re.sub('"','', food)
	food = re.sub('>','', food)
	food = re.sub(r'\\','', food)
	food = re.sub(r'\/','', food)
	food = re.sub(r'\d','', food)
	food = re.sub(r'\[','', food)
	food = re.sub(r'\]','', food)
	food = re.sub(r'\>','', food)
	food = re.sub(r'\<','', food)
	food = re.sub(r'\:','', food)
	food = re.sub(r'\}','', food)
	food = re.sub(r'\{','', food)
	food = re.sub(r'\,','', food)
	food = re.sub(r'\.','', food)


	# set measurement unit
	for i in measurements:
		if measure == i:
			measure = measurements[i]
			# print("measure: {} @nutrients_val".format(i))
	


	# make an Edamam API hhtp request to parser endpoint
	apiUri2 = 'https://api.edamam.com/api/food-database/parser'

	i = 0  ### iterator
	req_Attempt = 0  ## api request attempts (maximum tries of 2)

	while req_Attempt < 1:
		print('req_Attempt #' + str(req_Attempt))

		response = apirequest.get(apiUri2, 
			params={
			'ingr':food, 
			'app_id':'app_id', 
			'app_key':'app_key'
			})

		# check API response status
		if response.status_code == 200:
			# decode reponse into a json object
			jsonObj = response.json()
			# get the number of foods matched
			no_foods = len(jsonObj['hints'])
			# initate foodid
			foodid = None

			while i < no_foods:
				# print('Item #{} @nutrients_val'.format(str(i)))

				foodLabel = jsonObj['hints'][i]['food']['label']
				# print ('Item label: {} @nutrients_val'.format(foodLabel))

				if food.casefold() == foodLabel.casefold():
					# print ('Matching item found!')
					foodid = jsonObj['hints'][i]['food']['foodId']
					# print (str(jsonObj))
					break

				else:
					# print ('No matching item found!')
					foodid = None
					i += 1
			break
		else:
			req_Attempt += 1
			# print('Api request failed! @nutrients_val')


	# print variable values to console 
	# print("measure: "  + str(measure))
	# print("quantity: "  + str(quantity))

	# fetch macro values for all macros with specified amount
	if quantity is not None and foodid is not None:

		apiUri1 = 'https://api.edamam.com/api/food-database/nutrients'

		# make HTTP request Edamamam Food Database API and parse JSON response
		response = apirequest.post(apiUri1, params={
			'app_id':'app_id', 
			'app_key':'app_key'}, 
			json={"ingredients": [{
			"quantity": round(quantity, 2),
			"measureURI": measure,
			"foodId": foodid
			}]})
		
		#check API response status
		if response.status_code != 200:
			print("Error: response status code " + str(response.status_code) + " @nutrients_val @quantity_w_macro")
			return 0, 0, 0

		jsonObj2 = response.json()
		# print ("Edamam response: {} @nutrients_val".format(jsonObj2))

		
		
		# set protein value
		if "PROCNT" in jsonObj2['totalNutrients']:
			protein = round(jsonObj2['totalNutrients']['PROCNT']['quantity'], 2)
		else:
			protein = 0
		
		# set fat value
		if "FAT" in jsonObj2['totalNutrients']:
			fat = round(jsonObj2['totalNutrients']['FAT']['quantity'], 2)
		else:
			fat = 0
		
		# set carbs value
		if "CHOCDF" in jsonObj2['totalNutrients']:
			carbs = round(jsonObj2['totalNutrients']['CHOCDF']['quantity'], 2)
		else:
			carbs = 0

		# set calories value
		if "ENERC_KCAL" in jsonObj2['totalNutrients']:
			calories = round(jsonObj2['totalNutrients']['ENERC_KCAL']['quantity'], 2)
		else:
			calories = 0


		return calories, protein, fat, carbs


	# macros value when no quantity is provided
	else:
		try:
			# parse edamam API response json object
			nutr_content = jsonObj['hints'][i]['food']['nutrients']
			# print ("nutr_content: " + str(nutr_content))


			#set protein value
			if "PROCNT" in nutr_content:
				protein = round(nutr_content['PROCNT'], 2)
			else:
				protein = 0
			#set fat value
			if "FAT" in nutr_content:
				fat = round(nutr_content['FAT'], 2)
			else:
				fat = 0
			#set carbs value
			if "CHOCDF" in nutr_content:
				carbs = round(nutr_content['CHOCDF'], 2)
			else:
				carbs = 0

			# set calories value
			if "ENERC_KCAL" in nutr_content:
				calories = round(nutr_content['ENERC_KCAL'], 2)
			else:
				calories = 0

			return calories, protein, fat, carbs
					
		
		except:
			print("Error: food info not found")
			return 0, 0, 0, 0




# function to fetch queried_text nutritional content
# @param  String   food [food item extracted from the text]
# @param  String   macro [macro required extracted from the text]
# @param  int      quantity [food quantity extracted from the text]
# @param  String   measure [measurement unit extracted from the text]
# @return String   response [text sentence response to user]
def nutrients(food, macro=None,quantity=None, measure=None):

	## clean up query text
	food = re.sub(r'[\(\)]','',food)
	food = re.sub('"','', food)
	food = re.sub('>','', food)
	food = re.sub(r'\\','', food)
	food = re.sub(r'\/','', food)
	food = re.sub(r'\d','', food)
	food = re.sub(r'\[','', food)
	food = re.sub(r'\]','', food)
	food = re.sub(r'\>','', food)
	food = re.sub(r'\<','', food)
	food = re.sub(r'\:','', food)
	food = re.sub(r'\}','', food)
	food = re.sub(r'\{','', food)
	food = re.sub(r'\,','', food)
	food = re.sub(r'\.','', food)

	#set measurement unit
	for i in measurements:
		if measure == i:
			measure = measurements[i]
			# print("measure: " + str(i))
	

	# make an Edamam API hhtp request to parser endpoint
	apiUri2 = 'https://api.edamam.com/api/food-database/parser'

	i = 0  ### iterator
	req_Attempt = 0  ## api request attempts

	while req_Attempt < 1:
		# print('req_Attempt #' + str(req_Attempt))

		response = apirequest.get(apiUri2, 
			params={
			'ingr':food, 
			'app_id':'app_id', 
			'app_key':'app_key'
			})

		# check API response status
		if response.status_code == 200:
			# decode reponse into a json object
			jsonObj = response.json()
			# get the number of foods matched
			no_foods = len(jsonObj['hints'])

			while i < no_foods:
				# print('Item #{} @nutrients'.format(str(i)))

				foodLabel = jsonObj['hints'][i]['food']['label']
				# print ('Item label: {} @nutrients'.format(foodLabel))

				if food.casefold() == foodLabel.casefold():
					# print ('Matching item found!')
					foodid = jsonObj['hints'][i]['food']['foodId']
					# print (str(jsonObj))
					break

				else:
					# print ('No matching item found!')
					foodid = None
					i += 1
			break
		else:
			req_Attempt += 1
			# print('Api request failed! @nutrients_val')



	# print variable values to console 
	# print("measure: "  + str(measure))
	# print("quantity: "  + str(quantity))


	#fetch value for a specific macro with amount provided
	if macro is not None and foodid is not None:
		if quantity is not None:

			# make an Edamam API hhtp request to nutrients endpoint
			try:

				apiUri2 = 'https://api.edamam.com/api/food-database/nutrients'

				# print (food + '@nutrients')
				response = apirequest.post(apiUri2, 
					params={'app_id':'app_id', 
					'app_key':'app_key'}, 
					json={"ingredients": [{
					"quantity": round(quantity, 2),
					"measureURI": measure,
					"foodId": foodid
					}]})
				
				#check API response status
				if response.status_code != 200:
					print("Error: response status code " + str(response.status_code) + " @nutrients @macro_w_quantity")
					result = "I\'m sorry, please try again"
					return result

				# decode reponse into a json object
				jsonObj2 = response.json()
				# print ("Edamam response: " + str(jsonObj2))
			except:
				# print('Error: makking http call @nutrients @macro_w_quantity')
				result = "I\'m Sorry, please try again"

			# find macro queried and construct response senctence
			try:
				if 'protein' in macro.casefold():
					# print('protein matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['PROCNT']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['PROCNT']['unit']) + " of protein"
					
				# fetch fat value
				if 'fat' in macro.casefold():
					# print('fat matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['FAT']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['FAT']['unit']) + " of fat"

				# fetch amino acids value
				if 'amino' in macro.casefold():
					# print('amino acids matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['FAT']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['FAT']['unit']) + " of fat"
					
				# fetch carb value
				if 'carb' in macro.casefold():
					# print('carbs matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['CHOCDF']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['CHOCDF']['unit']) + " of carbs"

				# fetch fatty acids value
				if 'Fatty' in macro.casefold():
					# print('fatty acids matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['FAT']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['FAT']['unit']) + " of fat"

				# fetch saturated value
				if 'saturated' in macro.casefold():
					# print('saturated fat matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['FASAT']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['FASAT']['unit']) + " of  saturated fat"
					
				# fetch sugar value
				if 'sugar' in macro.casefold():
					# print('sugar matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['SUGAR']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['SUGAR']['unit']) + " of  sugar"
					
				# fetch vitamin a value
				if 'vitamin a' in macro.casefold():
					# print('vitamin a matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['VITA_RAE']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['VITA_RAE']['unit']) + " of  vitamin A"
					
				# fetch cholesterol value			
				if 'cholesterol' in macro.casefold():
					# print('cholestrol matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['CHOLE']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['CHOLE']['unit']) + " of  Cholesterol"
				
				# fetch calories value			
				if 'calorie' in macro.casefold():
					# print('calories matched')
					result = " has " + str(round(jsonObj2['totalNutrients']['ENERC_KCAL']['quantity'], 2)) + " calories"
			except:
				# print("nutrient not found @nutrients @macro_with_amount")
				result = "I\'m sorry!, this information is not available"

		else:
			try:
				nutr_content = jsonObj['hints'][i]['food']['nutrients']
				# fetch macro data queried and consruct reponse sentence
				result = None

				if 'calories' in macro.casefold():
					calori = nutr_content['ENERC_KCAL']
					result = " has " + str(round(calori, 2)) + ' Calories'
				
				if 'protein' in macro.casefold():
					protein = nutr_content['PROCNT']
					result = " has " + str(round(protein, 2)) + ' g of protein'
				
				if 'fat' in macro.casefold():
					fat = nutr_content['FAT']
					result = " has " + str(round(fat, 2)) + ' g of fat'
				
				if 'carb' in macro.casefold():
					carbs = nutr_content['CHOCDF']
					result = " has " + str(round(carbs, 2)) + ' g of carbs'
				
				if 'fiber' in macro.casefold():
					fiber = nutr_content['FIBTG']
					result = " has " + str(round(fiber, 2)) + ' g of fiber'
				
				if result == None:
					# print("nutrient not found @nutrients")
					result = "I\'m sorry!, this information is not available"

			except:
				# print("nutrient not found @nutrients @macro_withour_amount")
				result = "I\'m sorry!, this information is not available"
	

	# fetch macro values for all macros with specified amount
	elif quantity is not None and foodid is not None:

		apiUri0 = 'https://api.edamam.com/api/food-database/nutrients'

		# make HTTP request Edamamam Food Database API and parse JSON response
		response = apirequest.post(apiUri0, 
			params={'app_id':'app_id', 
			'app_key':'app_key'}, 
			json={"ingredients": [{
			"quantity": round(quantity, 2),
			"measureURI": measure, 
			"foodId": foodid
			}]})
		
		#check API response status
		if response.status_code != 200:
			print("Error: response status code " + str(response.status_code) + " @nutrients @quantity_w_macro")
			result = "I\'m sorry, please try again"
			return result

		jsonObj2 = response.json()
		# print ("Edamam response: " + str(jsonObj2))

		
		# set calori value
		if "ENERC_KCAL" in jsonObj2['totalNutrients']:
			calori = str(round(jsonObj2['totalNutrients']['ENERC_KCAL']['quantity'], 2)) + " calories"
		else:
			calori = ""
		
		# set protein value
		if "PROCNT" in jsonObj2['totalNutrients']:
			protein = str(round(jsonObj2['totalNutrients']['PROCNT']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['PROCNT']['unit']) + " of protein"
		else:
			protein = ""
		
		# set fat value
		if "FAT" in jsonObj2['totalNutrients']:
			fat = str(round(jsonObj2['totalNutrients']['FAT']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['FAT']['unit']) + " of fat"
		else:
			fat = ""
		
		# set carbs value
		if "CHOCDF" in jsonObj2['totalNutrients']:
			carbs = str(round(jsonObj2['totalNutrients']['CHOCDF']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['CHOCDF']['unit']) + " of carbs"
		else:
			carbs = ""
		
		# set fiber value
		if "FIBTG" in jsonObj2['totalNutrients']:
			fiber = str(round(jsonObj2['totalNutrients']['FIBTG']['quantity'], 2)) + ' ' + str(jsonObj2['totalNutrients']['FIBTG']['unit']) + " of fiber"
		else:
			fiber = ""

		# construct reponse sentetnce using retrieved data
		if calori + protein + fat + carbs + fiber != "":
			result = " has "
			for i in [calori, protein, fat, carbs, fiber]:
				if i != "":
					if " has " == result:
						result = result + i
					else:
						result = result + " and " + i
		else:
			result = "I\'m sorry!, this information is not available now"


	# elif quantity is None and macro is None:
	else:
		try:
			nutr_content = jsonObj['hints'][i]['food']['nutrients']
			# print ("nutr_content: " + str(nutr_content))

			#set calori value
			if "ENERC_KCAL" in nutr_content:
				calori = str(round(nutr_content['ENERC_KCAL'], 2)) + ' Calories '
			else:
				calori = ""
			#set protein value
			if "PROCNT" in nutr_content:
				protein = str(round(nutr_content['PROCNT'], 2)) + ' g of protein '
			else:
				protein = ""
			#set fat value
			if "FAT" in nutr_content:
				fat = str(round(nutr_content['FAT'], 2)) + ' g of fat '
			else:
				fat = ""
			#set carbs value
			if "CHOCDF" in nutr_content:
				carbs = str(round(nutr_content['CHOCDF'], 2)) + ' g of carbs '
			else:
				carbs = ""

			if "FIBTG" in nutr_content:
				fiber = str(round(nutr_content['FIBTG'], 2)) + ' g of fiber'
			else:
				fiber = ""

			# construct the response senctence
			if calori + protein + fat + carbs + fiber != "":
				result = " has "
				for i in [calori, protein, fat, carbs, fiber]:
					if i != "":
						if " has " == result:
							result = result + i
						else:
							result = result + " and " + i
			else:
				result = "I\'m sorry!, this information is not available now"
					
		except:
			result = "I\'m sorry!, information for this food is not available"

	return result 



# function for responses
def request_processor():
	start = time.time()

	# build a request object to fetch hhttp request at webhook end
	req = flrqst.get_json(force=True)
	print ('request object: ' +  str(req))


	################## Extract paramaters from user query ##################
	# fetch queried_text from query
	try:
		queried_text = req.get('queryResult').get('queryText')
		# print ('queried_text: ' +  queried_text)
	except:
		queried_text = ""
		print ("Error no queried_text found")

	# fetch intent from query
	try:
		intent = req.get('queryResult').get('intent').get('displayName')
		# print ('intent queried: ' +  intent)
	except:
		intent = ""
		print("Error not intent found")

	# fetch user id
	try:
		uId  = req.get('originalDetectIntentRequest').get('payload').get('uId')
		print ('user id: ' +  uId)
	except:
		uId = ""
		print ("Error No user id found!")
	

	########################################## Respond to user query ################################
	# instantiate a fulfillment response object
	response = fulfillment_response()

	if intent == "macro_query":

		##########################################collect parameters###################################
		# fetch macro from query
		try:
			macro = req.get('queryResult').get('parameters').get('macro')
			if macro == "":
				# print("Error no macro found")
				macro = None
		except:
			macro = None
			print("Error no macro found")

		# fetch amount from query
		try:
			amount = req.get('queryResult').get('parameters').get('amount')
			if amount == "":
				print("Error no amount found")
				amount = None
		except:
			amount = None
			print("Error no amount found")

		# fetch number from query
		try:
			number = req.get('queryResult').get('parameters').get('number')
			if number == "":
				# print("Error no number found")
				number = None
		except:
			number = None
			# print("Errpr no number found")

		# fetch measurement from query
		try:
			measure = req.get('queryResult').get('parameters').get('quantity')
			if measure == "":
				print("Error no measure found")
				measure = None
		except:
			measure = ""
			print("Error no measure found")

		# fetch food from query (food is a list)
		try:
			food = req.get('queryResult').get('parameters').get('food')
			# print ('food queried: ' +  str(food))
		except:
			food = ""
			print ("Error no food queried")


		
		##########################################fetch data from Edamam API###################################
		
		# Use food database API endpoint for a single food item
		if len(food) == 1:
			# print("food object length: " + str(len(food)))
			food = food[0]

			# find nutrients if Quantity is provided as (one, two, three, half, quarter, etc..)
			if amount is not None:
				# print("Query type: amout provided")
				fulfillmenText = response.fulfillment_text("it" + nutrients(food, macro, amount, measure))
			
			# find nutrients if Quantity is provided as numbers (1, 2, 3, 4 , 5, 6, etc.....)
			elif number is not None:
				# print("Query type: number provided")
				fulfillmenText = response.fulfillment_text("it" + nutrients(food, macro, number, measure))
			
			# find nutrients if only the food and macro is provided
			elif amount is None and number is None and macro is not None:
				# print("Query type: Number/Amount are None")
				fulfillmenText = response.fulfillment_text("it" + nutrients(food, macro))

			# find nutrients if only the food is provided
			else:
				# print("Query type: Number/Amount/macro are None")
				fulfillmenText = response.fulfillment_text("it" + nutrients(food))

			# return response
			response = response.main_response(fulfillmenText)
			
			end = time.time()
			print('runtime: {} seconds'.format(end - start))
			return response

		
		# Use food food text analysis API endpoint for a multiple food item
		else:
			# print("food object length: " + str(len(food)))
			
			# set as None to indicate no food item processed yet
			pre_fulfillmenText = None

			for i in food:
				# find nutrients if Quantity is provided as (one, two, three, half, quarter, etc..)
				if amount is not None:
					# print("Query type: amout provided")
					raw_fulfillmenText = response.fulfillment_text(nutrients(i, macro, amount, measure))
				
				# find nutrients if Quantity is provided as numbers (1, 2, 3, 4 , 5, 6, etc.....)
				elif number is not None:
					# print("Query type: number provided")
					raw_fulfillmenText = nutrients(i, macro, number, measure)
				
				# find nutrients if only the food and macro is provided
				elif amount is None and number is None and macro is not None:
					# print("Query type: Number/Amount are None")
					raw_fulfillmenText = nutrients(i, macro)

				# find nutrients if only the food is provided
				else:
					# print("Query type: Number/Amount/macro are None")
					raw_fulfillmenText = nutrients(i)

				
				# consttruct respomse sentence
				if pre_fulfillmenText == None:
					pre_fulfillmenText = i + " " + raw_fulfillmenText
				else:
					pre_fulfillmenText = pre_fulfillmenText + " and "+ i + " " + raw_fulfillmenText

				
			# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
			fulfillmenText = response.fulfillment_text(pre_fulfillmenText)
			# return response
			response = response.main_response(fulfillmenText)

			end = time.time()
			print('runtime: {} seconds'.format(end - start))
			return response


	elif intent == "update_weight":
		# user current weight and goal
		old_weight = user_info(uId).get("weight")
		goal        = user_info(uId).get("goal")

		# fetch weight from query
		try:
			new_weight = req.get('queryResult').get('parameters').get('weight')
		except:
			new_weight = None
			print("Error no new_weight found")

		if new_weight is not None:
			# when the user weighs more than what he used to
			if new_weight > old_weight:
				if goal == "gain":
					pre_fulfillmenText = "you are doing great!, keep it up"
				elif goal == "lose":
					pre_fulfillmenText = "seems like you've gained weight, that's ok, we need to pay more attention to your diet and activity level"
				elif goal == "maintain":
					pre_fulfillmenText = "seems like you've gained weight, that's ok, we need to pay more attention to your diet and activity level"
				elif goal == "bulk":
					pre_fulfillmenText = "seems like you've gained weight, that's ok, we need to pay more attention to your diet and activity level"
					
				update_weight(new_weight, uId)

				# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
				fulfillmenText = response.fulfillment_text(pre_fulfillmenText)
				# return response
				response = response.main_response(fulfillmenText)

				end = time.time()
				print('runtime: {} seconds'.format(end - start))
				return response

			# when the user weighs less than what he used to
			elif new_weight < old_weight:
				if goal == "gain":
					pre_fulfillmenText = "seems like you've lost weight!, that's ok, we need to pay more attention to your diet and activity level"
				elif goal == "lose":
					pre_fulfillmenText = "you are doing great!, keep it up"
				elif goal == "maintain":
					pre_fulfillmenText = "seems like you've lost weight!, that's ok, we need to pay more attention to your diet and activity level"
				elif goal == "bulk":
					pre_fulfillmenText = "seems like you've lost weight!, that's ok, we need to pay more attention to your diet and activity level"
		
				update_weight(new_weight, uId)

				# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
				fulfillmenText = response.fulfillment_text(pre_fulfillmenText)
				# return response
				response = response.main_response(fulfillmenText)

				end = time.time()
				print('runtime: {} seconds'.format(end - start))
				return response


			# when the user has the same weight of last time
			elif new_weight == old_weight:
				if goal == "gain":
					pre_fulfillmenText = "seems like you're weight hasn't changed, that's ok, we need to pay more attention to your diet and activity level"
				elif goal == "lose":
					pre_fulfillmenText = "seems like you're weight hasn't changed, that's ok, we need to pay more attention to your diet and activity level"
				elif goal == "maintain":
					pre_fulfillmenText = "you are doing great!, keep it up"
				elif goal == "bulk":
					pre_fulfillmenText = "seems like you're weight hasn't changed, that's ok, we need to pay more attention to your diet and activity level"
			
				# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
				fulfillmenText = response.fulfillment_text(pre_fulfillmenText)
				# return response
				response = response.main_response(fulfillmenText)

				end = time.time()
				print('runtime: {}'.format(end - start))
				return response

		else:
			print("Error: no weight paramater found to update")

			# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
			fulfillmenText = response.fulfillment_text("Sorry!, please try again")
			# return response
			response = response.main_response(fulfillmenText)

			end = time.time()
			print('runtime: {} seconds'.format(end - start))
			return response


	elif intent == "update_goal":
		# fetch goal from query
		try:
			new_goal = req.get('queryResult').get('parameters').get('goal')
			if new_goal != None:
				pre_fulfillmenText = "your goal has been updated, thanks for letting me know!"
				# print ('new_goal queried: ' +  new_goal)
			else:
				pre_fulfillmenText = "I'm sorry, please try again"
				# print("no new_goal found")
		except:
			pre_fulfillmenText = "I'm sorry, please try again"
			# print("no new_goal found")

		update_goal(new_goal, uId)

		# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
		fulfillmenText = response.fulfillment_text(pre_fulfillmenText)
		# return response
		response = response.main_response(fulfillmenText)

		end = time.time()
		print('runtime: {}'.format(end - start))
		return response
	

	# # verify if diet can be had uder the current diet paln
	elif intent == "check_diet":

		##########################################collect parameters###################################

		# fetch amount from query
		try:
			amount = req.get('queryResult').get('parameters').get('amount')
			if amount == "":
				amount = None
		except:
			amount = None
			print("Error no amount found @check_diet")

		# fetch number from query
		try:
			number = req.get('queryResult').get('parameters').get('number')
			if number == "":
				# print("Error no number found")
				number = None
		except:
			number = None
			# print("Error no number found @check_diet")

		# fetch measurement from query
		try:
			measure = req.get('queryResult').get('parameters').get('quantity')
			if measure == "":
				print("Error no measure found @check_diet")
				measure = None
		except:
			measure = ""
			print("Error no measure found @check_diet")

		# fetch food from query (food is a list)
		try:
			food = req.get('queryResult').get('parameters').get('food')
			# print ('food queried: {} @check_diet'.format(str(food)))
		except:
			food = ""
			print ("Error no food queried @check_diet")


		# fetch dayHour from query
		try:
			dayHour = req.get('queryResult').get('parameters').get('dayhour')
			if dayHour == 0:
				dayHour = 0
		except:
			dayHour = 0
			print("Error no dayHour found @check_diet")

		# fetch timeZone from query (timeZone is a string)
		try:
			timeZone = req.get('queryResult').get('parameters').get('timezone')
			# print ('timeZone queried: {} @check_diet'.format(timeZone))
		except:
			timeZone = ""
			print ("Error no timeZone queried @check_diet")


		
		##########################################fetch data from Edamam API###################################
		
		# Get macros values for a single food item
		if len(food) == 1:
			print("food object length: {} @check_diet".format(str(len(food))))
			food = food[0]

			# find nutrients if Quantity is provided as (one, two, three, half, quarter, etc..)
			if amount is not None:
				calories, protein, fat, carbs = nutrients_val(food, amount, measure)
			
			# find nutrients if Quantity is provided as numbers (1, 2, 3, 4 , 5, 6, etc.....)
			elif number is not None:
				calories, protein, fat, carbs = nutrients_val(food, number, measure)
			
			# find nutrients if only food is provided.
			else:
				calories, protein, fat, carbs = nutrients_val(food)



			# if food was not recognized/found return with 'item not recognized'
			if calories == 0 and protein == 0 and fat == 0 and carbs == 0:
				# print ('food wasn\'t recognized @check_diet')
				# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
				fulfillmenText = response.fulfillment_text('Food entered wasn\'t recognized. Please try again.')
				# return response
				response = response.main_response(fulfillmenText)

				end = time.time()
				print('runtime: {}'.format(end - start))
				return response


			
			food_macros = {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs}

			# check how food item fits into user diet for the day 
			macros_check = day_macro_chk(food_macros, dayHour, timeZone, uId)
			
			# set value
			if amount !=  None:
				value = amount
			elif number != None:
				value = number
			else:
				value = 0

			parameters = {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs, "food": food, "value": value, "measure": measure}

			if macros_check.get("behind"):
				# print("user is behind on macros @log_macro")
				response_txt = "Yeah that's fine"
			elif macros_check.get("ahead"):
				# print("user is ahead on macros @log_macro")
				response_txt = "Nope, not a good idea. Having " + food + " will mess up your diet!!"
			elif macros_check.get("on_track"):
				# print("user is on track on macros @log_macro")
				response_txt = "That's alright you can have that"
			else:
				print("Error, No macros check condition matched!\nMacro check: {} @log_macro".format(macros_check))
				
				end = time.time()
				print('runtime: {}'.format(end - start))
				return

			# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
			fulfillmenText = response.fulfillment_text(response_txt)
			# return response
			response = response.main_response(fulfillmenText)

			end = time.time()
			print('runtime: {}'.format(end - start))
			return response


		# Get macros values for multiple food items
		else:
			# print("food object length: {} @check_diet maultiple".format(str(len(food))))
			
			# set value
			if amount !=  None:
				value = amount
			elif number != None:
				value = number
			else:
				value = 0

			# set initial values for total macror (protein, fat, carbs)
			total_calories = 0
			total_protein  = 0
			total_fat      = 0
			total_carbs    = 0
			total_food     = []
				
			for i in food:
				# find nutrients if Quantity is provided as (one, two, three, half, quarter, etc..)
				if amount is not None:
					# print("Query type: amout provided @check_diet maultiple")
					calories, protein, fat, carbs = nutrients_val(i, amount, measure)
				
				# find nutrients if Quantity is provided as numbers (1, 2, 3, 4 , 5, 6, etc.....)
				elif number is not None:
					# print("Query type: number provided @check_diet maultiple")
					calories, protein, fat, carbs = nutrients_val(i, number, measure)
				

				# find nutrients if only the food is provided
				else:
					# print("Query type: Number/Amount/macro are None @check_diet maultiple")
					calories, protein, fat, carbs = nutrients_val(i)



				# if food was not recognized/found return with 'item not recognized'
				if calories == 0 and protein == 0 and fat == 0 and carbs == 0:
					# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
					fulfillmenText = response.fulfillment_text('Food entered wasn\'t recognized. Please try again.')
					# return response
					response = response.main_response(fulfillmenText)

					end = time.time()
					print('runtime: {}'.format(end - start))
					return response



				total_calories += calories
				total_protein  += protein
				total_fat      += fat
				total_carbs    += carbs
				total_food.append(i)


			total_macros = {"calories": total_calories, "protein": total_protein, "fat": total_fat, "carbs": total_carbs}
			
			# check how food item fits into user diet for the day 
			# print("total_macros macros: {} @check_diet maultiple".format(total_macros))
			macros_check = day_macro_chk(total_macros, dayHour, timeZone, uId)
			

			parameters = {"calories": total_calories, "protein": total_protein, "fat": total_fat, "carbs": total_carbs, "food": food, "value": value, "measure": measure}

			if macros_check.get("behind"):
				# print("user is behind on macros @log_macro")
				response_txt = "Yeah that's fine"
			elif macros_check.get("ahead"):
				# print("user is ahead on macros @log_macro")
				response_txt = "Nope, not a good idea. Having " + food + " will mess up your diet!!"
			elif macros_check.get("on_track"):
				# print("user is on track on macros @log_macro")
				response_txt = "That's alright you can have that"
			else:
				print("Error, No macros check condition matched!\nMacro check: {} @log_macro".format(macros_check))
				
				end = time.time()
				print('runtime: {}'.format(end - start))
				return

			# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
			fulfillmenText = response.fulfillment_text(response_txt)
			# return response
			response = response.main_response(fulfillmenText)

			end = time.time()
			print('runtime: {}'.format(end - start))
			return response



	elif intent == "log_macro":

	##########################################collect parameters###################################
		# fetch amount from query
		try:
			amount = req.get('queryResult').get('parameters').get('amount')
			if amount == "":
				print("Error no amount found")
				amount = None
		except:
			amount = None
			print("Error no amount found @log_macro")

		# fetch number from query
		try:
			number = req.get('queryResult').get('parameters').get('number')
			if number == "":
				# print("Error no number found")
				number = None
		except:
			number = None
			# print("Error no number found @log_macro")

		# fetch measurement from query
		try:
			measure = req.get('queryResult').get('parameters').get('quantity')
			if measure == "":
				print("Error no measure found @log_macro")
				measure = None
		except:
			measure = ""
			print("Error no measure found @log_macro")

		# fetch food from query (food is a list)
		try:
			food = req.get('queryResult').get('parameters').get('food')
			# print ('food queried: {} @log_macro'.format(str(food)))
		except:
			food = ""
			print ("Error no food queried @log_macro")

		# fetch hour from query (hour of the day query made at client device)
		try:
			dayHour = req.get('queryResult').get('parameters').get('dayhour')
			if dayHour == 0:
				dayHour = 0
		except:
			dayHour = 0
			print("Error no dayHour found @log_macro")

		# fetch timeZone from query (timeZone is a string)
		try:
			timeZone = req.get('queryResult').get('parameters').get('timezone')
			# print ('timeZone queried: {} @log_macro'.format(timeZone))
		except:
			timeZone = ""
			print ("Error no timeZone queried @log_macro")

		############################################set value parameter#######################################
			
		if amount !=  None:
			value = amount
		elif number != None:
			value = number
		else:
			value = 0

		##########################################fetch data from Edamam API###################################
		
		# Get macros values for a single food item
		if len(food) == 1:
			# print("food object length: {} @log_macro".format(str(len(food))))
			food = food[0]

			# find nutrients if Quantity is provided as (one, two, three, half, quarter, etc..)
			if amount is not None:
				# print("Query type: amount provided @log_macro")
				calories, protein, fat, carbs = nutrients_val(food, amount, measure)
			
			# find nutrients if Quantity is provided as numbers (1, 2, 3, 4 , 5, 6, etc.....)
			elif number is not None:
				# print("Query type: number provided")
				calories, protein, fat, carbs = nutrients_val(food, number, measure)
			
			# find nutrients if only food is provided.
			else:
				# print("Query type: Number/Amount are None")
				calories, protein, fat, carbs = nutrients_val(food)



			# if food was not recognized/found return with 'item not recognized'
			if calories == 0 and protein == 0 and fat == 0 and carbs == 0:
				# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
				fulfillmenText = response.fulfillment_text('Food entered wasn\'t recognized. Please try again.')
				# return response
				response = response.main_response(fulfillmenText)

				end = time.time()
				print('runtime: {}'.format(end - start))
				return response



			# log macros to user diett plan
			log_macros(food, value, measure, calories, protein, fat, carbs, timeZone, uId)
			# print("macros logged @log_macro")
			
			food_macros = {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs}

			# check how food item fits into user diet for the day 
			# print("food macros: {} @log_macro".format(food_macros))
			macros_check = day_macro_chk(food_macros, dayHour, timeZone, uId)
			
			parameters = {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs, "food": food, "value": value, "measure": measure}

			if macros_check.get("behind"):
				# print("user is behind on macros @log_macro")
				response_txt = "Food logged successfully! You are a little bit behind on your macros"
			elif macros_check.get("ahead"):
				# print("user is ahead on macros @log_macro")
				response_txt = "Food logged successfully! You are a little bit ahead on your macros"
			elif macros_check.get("on_track"):
				# print("user is on track on macros @log_macro")
				response_txt = "Food logged successfully! All good, you are on track!"
			else:
				print("Error, No macros check condition matched!\nMacro check: {} @log_macro".format(macros_check))
				
				end = time.time()
				print('runtime: {}'.format(end - start))
				return

			# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
			fulfillmenText = response.fulfillment_text(response_txt)
			# return response
			response = response.main_response(fulfillmenText)

			end = time.time()
			print('runtime: {}'.format(end - start))
			return response


		# Get macros values for multiple food items
		else:
			# print("food object length: {} @log_macro maultiple".format(str(len(food))))
			
			# set initial values for total macror (protein, fat, carbs)
			total_calories = 0
			total_protein  = 0
			total_fat      = 0
			total_carbs    = 0
			total_food     = []
				
			for i in food:
				# find nutrients if Quantity is provided as (one, two, three, half, quarter, etc..)
				if amount is not None:
					# print("Query type: amout provided @log_macro maultiple")
					calories, protein, fat, carbs = nutrients_val(i, amount, measure)
				
				# find nutrients if Quantity is provided as numbers (1, 2, 3, 4 , 5, 6, etc.....)
				elif number is not None:
					# print("Query type: number provided @log_macro maultiple")
					calories, protein, fat, carbs = nutrients_val(i, number, measure)
				

				# find nutrients if only the food is provided
				else:
					# print("Query type: Number/Amount/macro are None @log_macro maultiple")
					calories, protein, fat, carbs = nutrients_val(i)



				# if food was not recognized/found return with 'item not recognized'
				if calories == 0 and protein == 0 and fat == 0 and carbs == 0:
					# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
					fulfillmenText = response.fulfillment_text('Food entered wasn\'t recognized. Please try again.')
					# return response
					response = response.main_response(fulfillmenText)

					end = time.time()
					print('runtime: {}'.format(end - start))
					return response



				# log macros to user diett plan (i is the food item in the "food" list)
				log_macros(i, value, measure, calories, protein, fat, carbs, timeZone, uId)
				# print("macros logged @log_macro")

				total_calories += calories
				total_protein  += protein
				total_fat      += fat
				total_carbs    += carbs
				total_food.append(i)

			total_macros = {"calories": total_calories, "protein": total_protein, "fat": total_fat, "carbs": total_carbs}
			
			# check how food item fits into user diet for the day 
			# print("total_macros macros: {} @log_macro maultiple".format(total_macros))
			macros_check = day_macro_chk(total_macros, dayHour, timeZone, uId)
			
			parameters = {"calories": total_calories, "protein": total_protein, "fat": total_fat, "carbs": total_carbs, "food": food, "value": value, "measure": measure}

			if macros_check.get("behind"):
				# print("user is behind on macros @log_macro")
				response_txt = "Food logged successfully! You are a little bit behind on your macros"
			elif macros_check.get("ahead"):
				# print("user is ahead on macros @log_macro")
				response_txt = "Food logged successfully! You are a little bit ahead on your macros"
			elif macros_check.get("on_track"):
				# print("user is on track on macros @log_macro")
				response_txt = "Food logged successfully! All good, you are on track!"
			else:
				print("Error, No macros check condition matched!\nMacro check: {} @log_macro".format(macros_check))
				
				end = time.time()
				print('runtime: {}'.format(end - start))
				return

			# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
			fulfillmenText = response.fulfillment_text(response_txt)
			# return response
			response = response.main_response(fulfillmenText)

			end = time.time()
			print('runtime: {}'.format(end - start))
			return response


	elif intent == "on_track - yes":

		##########################################collect parameters###################################

		# fetch amount from query
		try:
			amount = req.get('queryResult').get('parameters').get('amount')
			if amount == "":
				print("Error no amount found")
				amount = None
		except:
			amount = None
			print("Error no amount found @on_track - yes")

		# fetch number from query
		try:
			number = req.get('queryResult').get('parameters').get('number')
			if number == "":
				# print("Error no number found")
				number = None
		except:
			number = None
			# print("Error no number found @on_track - yes")

		# fetch measurement from query
		try:
			measure = req.get('queryResult').get('parameters').get('quantity')
			if measure == "":
				print("Error no measure found @on_track - yes")
				measure = None
		except:
			measure = ""
			print("Error no measure found @on_track - yes")

		# fetch foods from query
		try:
			foods = req.get('queryResult').get('parameters').get('food')
			# print ('foods queried: {} @on_track - yes'.format(str(foods)))
		except:
			foods = ""
			print ("Error no food queried @on_track - yes")

		# fetch calories from query
		try:
			calories = req.get('queryResult').get('parameters').get('calories')
			# print ('calories queried: {} @check_diet'.format(str(calories)))
		except:
			calories = ""
			print ("Error no calories queried @on_track - yes")

		# fetch protein from query
		try:
			protein = req.get('queryResult').get('parameters').get('protein')
			# print ('protein queried: {} @on_track - yes'.format(str(protein)))
		except:
			protein = ""
			print ("Error no protein queried @on_track - yes")

		# fetch fat from query
		try:
			fat = req.get('queryResult').get('parameters').get('fat')
			# print ('fat queried: {} @on_track - yes'.format(str(fat)))
		except:
			fat = ""
			print ("Error no fat queried @on_track - yes")

		# fetch carbs from query
		try:
			carbs = req.get('queryResult').get('parameters').get('carbs')
			# print ('carbs queried: {} @on_track - yes'.format(str(carbs)))
		except:
			carbs = ""
			print ("Error no carbs queried @on_track - yes")

		# fetch timeZone from query (timeZone is a string)
		try:
			timeZone = req.get('queryResult').get('parameters').get('timezone')
			# print ('timeZone queried: {} @on_track - yes'.format(timeZone))
		except:
			timeZone = ""
			print ("Error no timeZone queried @on_track - yes")

		# set value
		if amount !=  None:
			value = amount
		elif number != None:
			value = number
		else:
			value = None
		
		##########################################log data on database###################################

		for food in foods:
			log_macros(food, value, measure, calories, protein, fat, carbs, timeZone, uId)
			# print("macros logged @on_track - yes")

		end = time.time()
		print("runtime: {}".format(end - start))
		

	### log meals marked as ete by the user on client device
	elif intent == "log_meal":

		# fetch recipeID from query
		try:
			recipeID = req.get('queryResult').get('parameters').get('recipeid')
			if recipeID == "":
				print("Error no recipeID found")
				recipeID = None
		except:
			recipeID = None
			print("Error no recipeID found @log_meal") 

		# fetch recipeID from query
		try:
			recomndID = req.get('queryResult').get('parameters').get('recomndid')
			if recomndID == "":
				print("Error no recomndID found")
				recomndID = None
		except:
			recomndID = None
			print("Error no recomndID found @log_meal")

		# fetch hour from query (hour of the day query made at client device)
		try:
			dayHour = req.get('queryResult').get('parameters').get('dayhour')
			if dayHour == 0:
				print("no dayHour found")
		except:
			dayHour = 0
			print("Error no dayHour found @log_meal")

		# fetch timeZone from query (timeZone is a string)
		try:
			timeZone = req.get('queryResult').get('parameters').get('timezone')
			# print ('timeZone queried: {} @log_meal'.format(timeZone))
		except:
			timeZone = ""
			print ("Error no timeZone queried @log_meal")

		### get recipe macros
		mealMacros = get_recipe(recipeID)

		if mealMacros:
			protein  = mealMacros.get('protein') + 0.0
			fat = mealMacros.get('fat') + 0.0
			carbs = mealMacros.get('carbs') + 0.0
			calories = mealMacros.get('calories') + 0.0
			food = mealMacros.get('recipename')
			measure = 'meal'
			value = 1.0

			# log macros to user diet plan
			log_macros(food, value, measure, calories, protein, fat, carbs, timeZone, uId)
			
			food_macros = {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs}

			# check how food item fits into user diet for the day 
			# print("food macros: {} @log_macro".format(food_macros))
			macros_check = day_macro_chk(food_macros, dayHour, timeZone, uId)
			
			parameters = {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs, "food": food, "value": value, "measure": measure}

			if macros_check.get("behind"):
				# print("user is behind on macros @log_macro")
				# mark meal as eaten
				mark_eaten(recomndID, uId)
				response_txt = "Food logged successfully! You are a little bit behind on your macros"
			elif macros_check.get("ahead"):
				# print("user is ahead on macros @log_macro")
				# mark meal as eaten
				mark_eaten(recomndID, uId)
				response_txt = "Food logged successfully! You are a little bit ahead on your macros"
			elif macros_check.get("on_track"):
				# print("user is on track on macros @log_macro")
				# mark meal as eaten
				mark_eaten(recomndID, uId)
				response_txt = "Food logged successfully! All good, you are on track!"
			else:
				print("Error, No macros check condition matched!\nMacro check: {} @log_macro".format(macros_check))
				
				end = time.time()
				print('runtime: {}'.format(end - start))
				return

			# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
			fulfillmenText = response.fulfillment_text(response_txt)
			# return response
			response = response.main_response(fulfillmenText)

			end = time.time()
			print('runtime: {}'.format(end - start))
			return response

		else:
			print('Error Couldn\'t retrieve recipe document @log_meal')

	elif intent == "set_diet":

		set_diet_plan(uId)

		# create fulfillmenText json object from final pre_fulfillmenText for main_response processing
		fulfillmenText = response.fulfillment_text("Your diet plan was successfully configured") ## temporary implementation
		# return response
		response = response.main_response(fulfillmenText)

		end = time.time()
		print('runtime: {}'.format(end - start))
		return response


	elif intent == "new_setup":

		# set user diet
		set_diet_plan(uId)

		# Update user doc
		users.update_one({"uId": uId},
			{'$set': {
			'dietCreated': True,
			}})

		# assign the user a nutritinist and create sessions for scheduling
		assigned = assign_nutritionist(uId)

		if assigned:
			fulfillmenText = response.fulfillment_text("Successfull assigned a nutritionist")
		else:
			fulfillmenText = response.fulfillment_text("Successfull assigned a nutritionist")
		# return response
		response = response.main_response(fulfillmenText)

		end = time.time()
		print('runtime: {} seconds'.format(end - start))
		return response





# create a route for webhook
@webhook_blueprint.route('/ghe54ytrs54', methods=['GET', 'POST'])
def webhook():
	print("webhook running")
	# return response when web hook is triggered
	return make_response(jsonify(request_processor()))
