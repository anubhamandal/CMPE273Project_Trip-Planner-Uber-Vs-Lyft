from flask import Flask, Response
from flaskext.mysql import MySQL
import json
import sys
import requests
from key import geo_key, lyft_key, uber_key
from tsp_dp import shortestPath

mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'crime'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
					
lyft_url = 'https://api.lyft.com/v1/cost'
uber_url = 'https://api.uber.com/v1.2/estimates/price'

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
				
	def printPts(self):
		username = 'anubha'
		cursor = mysql.connect().cursor()
		cursor.execute("select * from user1 where user='" + username + "'")
		data = cursor.fetchall()
		print data[0][1]
		return json.dumps(data[0][1]) #json.dumps({'start':self._start, 'end':self._end, 'others':self._other})
		
	def getLatLng(self):
		latLng = [[37.4029455, -121.9437678], [37.4223664, -122.084406], [37.4129401,-121.9388528], [37.4237197, -121.9045721], [37.3907198, -121.8846152]]
		return latLng
		'''
		need to get lat and lon details from database based on myLoc list
		need to be a list of lat-lng pairs of start, others, end
		latLng = [[12,2453], [32, 78989]]		--example
		
		latLng = dict([('start', [lat, lon])])
		.....
		
		lat = latLng['start'][0]
		lng = latLng['start'][1]
		latLng.update([('o1', [lat, lng])])
		'''
	
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
					uCost[i][j] = sys.maxint
					uDistance[i][j] = sys.maxint
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
					lCost[i][j] = sys.maxint
					lDistance[i][j] = sys.maxint
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
	
	def uberApi(self,slat,slng,elat,elng):
		uber_payload = {'start_latitude':slat, 'start_longitude':slng, 'end_latitude':elat, 'end_longitude':elng}
		uber_header = {'Authorization':uber_key, 'Accept-Language':'en_US', 'Content-Type':'application/json'}
		usearch_req = requests.get(uber_url, params=uber_payload, headers=uber_header)
		usearch_json = usearch_req.json()
		my_req = next((item for item in usearch_json['prices'] if item['display_name'] == 'uberX'), None)
		rval = [my_req['high_estimate'], my_req['duration'], my_req['distance']]
		return rval
		
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

class ProviderResult():	
	def __init__(self,myDict):
		self._myDict = myDict
		
	@property
	def myDict(self):
		return self._myDict
		
	def genOutput(self):
		input = PriceDiff(self.myDict)
		u = input.uEst
		l = input.lEst
		uberDetails = {
			"name" : "Uber",
            "total_costs_by_cheapest_car_type" : u[0][0],
			"best_route_by_costs" : u[0][1],
            "currency_code": "USD",
            "total_duration" : u[1]/60,
            "duration_unit": "minute",
            "total_distance" : u[2],
            "distance_unit": "mile"
			}
		lyftDetails = {
			"name" : "Lyft",
            "total_costs_by_cheapest_car_type" : l[0][0]/100,
			"best_route_by_costs" : l[0][1],
            "currency_code": "USD",
            "total_duration" : l[1]/60,
            "duration_unit": "minute",
            "total_distance" : l[2],
            "distance_unit": "mile"
			}
		resp = {
			"id" : 200000,					#need to feed this in db and get the id 
			"start" : self.myDict['start'],
			"providers" : [
							uberDetails,
							lyftDetails
						],
			"end" : self.myDict['end']
			}

		return Response(response=json.dumps(resp))