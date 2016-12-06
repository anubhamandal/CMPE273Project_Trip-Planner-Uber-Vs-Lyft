from flask import Flask, abort
from flask import request
from model import db
from model import Location
from model import CreateDB
from model import app as application
import simplejson as json
from sqlalchemy.exc import IntegrityError
import os
import sys
import urllib2
import requests
import json
from customClass import ProviderResult, app, PriceDiff


# initate flask app
app = Flask(__name__)

@app.route('/')
def index():
	return 'Hello! Uber vs Lyft Prices'

#CHANGES TO INCLUDE METHODS
# Trying with requst forms and with postman instead of browser arguments
    

@app.route('/locations', methods=['POST'])
def insert_user():
        json_data = json.loads(request.data)
        print json_data
        x = json_data['address']
        # x is '3700 Casa Verde St'
        x = x.replace(' ','+')
        # now x is '3700+Casa+Verde+St'
        y = json_data['city']
        y = y.replace(' ','+')
        # y is 'San Jose'
        z = json_data['state']
        # z is 'CA'
        a = str(json_data['zip'])
        string_for_google = x+'+'+y+'+'+z+'+'+a
        # string_for_google is '3700+Casa+Verde+St+San+Jose+CA+95134'
        apidata = json.load(urllib2.urlopen('http://maps.google.com/maps/api/geocode/json?address=%s&sensor=False'%(string_for_google)))
        #print 'apidata received'
        #print apidata
        #print '---------'
        data = apidata['results'][0]
        geometry_data = data['geometry']
        location_data = geometry_data['location']
        latitude = location_data['lat']
        #print 'latitude is'
        #print latitude
        longitude = location_data['lng']
        #print 'longitude is'
        #print longitude
        database = CreateDB(hostname = '')
        db.create_all()
        try:
                location = Location(json_data['name'],
                                    json_data['address'],
                                    json_data['city'],
                                    json_data['state'],
                                    json_data['zip'],
                                    latitude,
                                    longitude)		
                db.session.add(location)
                db.session.commit()
                user_id=location.id
                return json.dumps({'id':str(location.id),'name':location.name,'address':location.address,'city':location.city,'state':location.state,'zip':location.zip,'coordinate':{'lat':location.lat,'lng':location.lng}}),201
        except IntegrityError:
                return json.dumps({'status':False})

# this page called /v1/expenses/expense id can allow three methods - get, post and delete. 
@app.route('/locations/<location_id>', methods=['GET', 'PUT', 'DELETE' ])
def location_reset(location_id):
        if request.method == 'GET':
                try:
                        location_get = Location.query.filter_by(id=location_id).first()
                        return json.dumps({'id':str(location_get.id),'name':location_get.name,'address':location_get.address,'city':location_get.city,'state':location_get.state,'zip':location_get.zip,'coordinate':{'lat':location_get.lat,'lng':location_get.lng}})
                except AttributeError:
                        abort(404)
 
        if request.method == 'DELETE':
                try:
                        location_delete=Location.query.filter_by(id=location_id).delete()
                        db.session.commit()
                        return ('', 204)
                except AttributeError:
                        abort(404)



        if request.method == 'PUT':
                json_data = json.loads(request.data)
                try:
                        location_update=Location.query.filter_by(id=location_id).first()
                        new_name = json_data['name']
                        location_update.name = new_name
                        db.session.commit()
                        return json.dumps({'name':location_update.name}),202
                except AttributeError:
                        abort(404)
       
# Post request for the Uber vs Lyft details
# input format:
# {
    # "start": 1,
    # "others" : [4,5,6],
    # "end": 1
# }	
@app.route("/trips", methods=["POST"])
def getPrice():
	val = json.loads(request.data)				# Input
	var = ProviderResult(val)					# Class for calculating the Uber and Lyft details
	x = var.genOutput()
	return x                        
                        

@app.route('/info')
def app_status():
	return json.dumps({'server_info':application.config['SQLALCHEMY_DATABASE_URI']})

#run app service 
if __name__ == "__main__":
	app.run(host='0.0.0.0',port=5000, debug=True)