from flask import Flask, Response
from flaskext.mysql import MySQL
import json
import sys
import requests
from key import lyft_key, uber_key				#importing keys of the Uber and Lyft api's
from tsp_dp import shortestPath

mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = ''
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = ''
app.config['MYSQL_DATABASE_HOST'] = ''
mysql.init_app(app)
					
lyft_url = 'https://api.lyft.com/v1/cost'
uber_url = 'https://api.uber.com/v1.2/estimates/price'

# Class for calculating the requirements
class PriceDiff():
	def __init__(self,myDict):
		self._start = myDict['start']
		self._end = myDict['end']
		self._other = myDict['others']
		self._othLen = len(myDict['others'])
		self._myLoc = self.getMyLoc()
		self._latLng = self.getLatLng()
		self._uEst = self.uberDetails()
		self._lEst = self.lyftDetails()
	'''
	Dummy method to test DB
	--------------------------
	def printPts(self):
		latLng = []
		cursor = mysql.connect().cursor()
		l = len(self.myLoc)
		i=0
		while(i < l):
			cursor.execute("select lat, lng from location where id= %s", (self.myLoc[i]))
			data = cursor.fetchall()
			latLng.append([data[0][0],data[0][1]])
			i=i+1
		return json.dumps(latLng) #json.dumps({'start':self._start, 'end':self._end, 'others':self._other})
	'''
	# List storing the Lat-Lng pairs of the required locations
	# Format: latLng = [[37.4029455, -121.9437678], [37.4223664, -122.084406],....]
	def getLatLng(self):
		latLng = []
		cursor = mysql.connect().cursor()
		l = len(self.myLoc)
		i=0
		while(i < l):
			cursor.execute("select lat, lng from location where id= %s", (self.myLoc[i]))
			data = cursor.fetchall()
			latLng.append([data[0][0],data[0][1]])
			i=i+1
		return latLng

	# List for converting the location id's to index to be used for the TSP algo
	def getMyLoc(self):
		myLoc = []
		myLoc.append(self._start)
		i=0
		while (i<self._othLen):
			myLoc.append(self._other[i])
			i=i+1
		myLoc.append(self._end)
		return myLoc
	
	@property
	def myLoc(self):
		return self._myLoc
		
	@property
	def latLng(self):
		return self._latLng
		
	@property
	def othLen(self):
		return self._othLen
	
	# Method for calculating the shortest path and getting the cost, distance and duration from Uber API
	def uberDetails(self):
		l = len(self.myLoc)
		uCost = [[0 for x in range(l)] for y in range(l)]
		uDuration = [[0 for x in range(l)] for y in range(l)]
		uDistance = [[0 for x in range(l)] for y in range(l)]
		for i in range(0,l):
			for j in range(0,l):
				if i == j:
					continue
				if (j == 0 or i == l-1):
					uCost[i][j] = sys.maxint								# Filling with MAX_INT as locations to start point details and end point 
					uDistance[i][j] = sys.maxint							# to location details are not required. Minimising the number of API calls.
					uDuration[i][j] = sys.maxint
				else:
					slat = self.latLng[i][0]
					slng = self.latLng[i][1]
					elat = self.latLng[j][0]
					elng = self.latLng[j][1]
					ival = self.uberApi(slat,slng,elat,elng)
					uCost[i][j] = ival[0]
					uDuration[i][j] = ival[1]
					uDistance[i][j] = ival[2]
		c = shortestPath(uCost)
		dr = uDuration[0][c[1][0]]
		dt = uDistance[0][c[1][0]]
		i = 1
		while (i < self.othLen):
			dr = dr + uDuration[c[1][i-1]][c[1][i]]
			dt = dt + uDistance[c[1][i-1]][c[1][i]]
			i=i+1
		dr = dr + uDuration[c[1][i-1]][l-1]
		dt = dt + uDistance[c[1][i-1]][l-1]
		uEst = [c, dr, dt]
		return uEst
	
	# Method for calculating the shortest path and getting the cost, distance and duration from Lyft API
	def lyftDetails(self):
		l = len(self.myLoc)
		lCost = [[0 for x in range(l)] for y in range(l)]
		lDuration = [[0 for x in range(l)] for y in range(l)]
		lDistance = [[0 for x in range(l)] for y in range(l)]
		for i in range(0,l):
			for j in range(0,l):
				if i == j:
					continue
				if (j == 0 or i == l-1):
					lCost[i][j] = sys.maxint								# Filling with MAX_INT as locations to start point details and end point 
					lDistance[i][j] = sys.maxint							# to location details are not required. Minimising the number of API calls.
					lDuration[i][j] = sys.maxint
				else:
					slat = self.latLng[i][0]
					slng = self.latLng[i][1]
					elat = self.latLng[j][0]
					elng = self.latLng[j][1]
					ival = self.lyftApi(slat,slng,elat,elng)
					lCost[i][j] = ival[0]
					lDuration[i][j] = ival[1]
					lDistance[i][j] = ival[2]
		c = shortestPath(lCost)
		dr = lDuration[0][c[1][0]]
		dt = lDistance[0][c[1][0]]
		i = 1
		while (i < self.othLen):
			dr = dr + lDuration[c[1][i-1]][c[1][i]]
			dt = dt + lDistance[c[1][i-1]][c[1][i]]
			i=i+1
		dr = dr + lDuration[c[1][i-1]][l-1]
		dt = dt + lDistance[c[1][i-1]][l-1]
		lEst = [c, dr, dt]
		return lEst
	
	# Method for Uber API call
	def uberApi(self,slat,slng,elat,elng):
		uber_payload = {'start_latitude':slat, 'start_longitude':slng, 'end_latitude':elat, 'end_longitude':elng}
		uber_header = {'Authorization':uber_key, 'Accept-Language':'en_US', 'Content-Type':'application/json'}
		usearch_req = requests.get(uber_url, params=uber_payload, headers=uber_header)
		usearch_json = usearch_req.json()
		my_req = next((item for item in usearch_json['prices'] if item['display_name'] == 'uberX'), None)
		rval = [my_req['high_estimate'], my_req['duration'], my_req['distance']]
		return rval
	
	# Method for Lyft API call
	def lyftApi(self,slat,slng,elat,elng):
		lyft_payload = {'start_lat':slat, 'start_lng':slng, 'end_lat':elat, 'end_lng':elng}
		lyft_header = {'Content-Type':'application/json', 'Authorization':lyft_key}
		lsearch_req = requests.get(lyft_url, params=lyft_payload, headers=lyft_header)
		lsearch_json = lsearch_req.json()
		my_req = next((item for item in lsearch_json['cost_estimates'] if item['display_name'] == 'Lyft'), None)
		rval = [my_req['estimated_cost_cents_max'], my_req['estimated_duration_seconds'], my_req['estimated_distance_miles']]
		return rval
	
	@property
	def uEst(self):
		return self._uEst
		
	@property
	def lEst(self):
		return self._lEst

# Class for output generation
class ProviderResult():	
	def __init__(self,myDict,myID):
		self._myDict = myDict
		self._myID = myID
		
	@property
	def myDict(self):
		return self._myDict
	
	@property
	def myID(self):
		return self._myID
		
	def genOutput(self):
		input = PriceDiff(self.myDict)
		u = input.uEst
		l = input.lEst
		myLoc = input.myLoc
		num = len(u[0][1])
		i=0
		uLoc = []
		lLoc = []
		while (i<num):
			uLoc.append(myLoc[u[0][1][i]])
			lLoc.append(myLoc[l[0][1][i]])
			i=i+1
		uberDetails = {
			"name" : "Uber",
            "total_costs_by_cheapest_car_type" : u[0][0],
			"best_route_by_costs" : uLoc,
            "currency_code": "USD",
            "total_duration" : u[1]/60,
            "duration_unit": "minute",
            "total_distance" : "%.2f" % u[2],
            "distance_unit": "mile"
			}
		lyftDetails = {
			"name" : "Lyft",
            "total_costs_by_cheapest_car_type" : l[0][0]/100,
			"best_route_by_costs" : lLoc,
            "currency_code": "USD",
            "total_duration" : l[1]/60,
            "duration_unit": "minute",
            "total_distance" : "%.2f" % l[2],
            "distance_unit": "mile"
			}
		resp = {
			"id" : self.myID,					#need to feed this in db and get the id 
			"start" : self.myDict['start'],
			"providers" : [
							uberDetails,
							lyftDetails
						],
			"end" : self.myDict['end']
			}

		return Response(response=json.dumps(resp))
