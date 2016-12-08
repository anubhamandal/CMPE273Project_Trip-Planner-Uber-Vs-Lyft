"""application using Google Maps API, Uber API and Lyft API for getting locations latitude logitude
and for trip planning, price estimation and for providing  available products counts of Uber and Lyft"""



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


##initate flask app
app = Flask(__name__)



##POST METHOD FOR locations
    

@app.route('/locations', methods=['POST'])
def insert_user():
        json_data = json.loads(request.data)
        print json_data
        x = json_data['address']
        x = x.replace(' ','+')
        
        y = json_data['city']
        y = y.replace(' ','+')
        
        z = json_data['state']
        
        a = str(json_data['zip'])
        string_for_google = x+'+'+y+'+'+z+'+'+a
        
        apidata = json.load(urllib2.urlopen('http://maps.google.com/maps/api/geocode/json?address=%s&sensor=False'%(string_for_google)))
        
       
        data = apidata['results'][0]
        geometry_data = data['geometry']
        location_data = geometry_data['location']
        latitude = location_data['lat']
        longitude = location_data['lng']
        
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

##GET PUT and DELETE METHODS FOR locations
 
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
             
"""GET METHOD FOR UBER PRODUCTS """                       
       

@app.route('/uberproductsnear/<location_id>', methods=['GET'])
def location_uberproducts(location_id):
                try:
                        location_get = Location.query.filter_by(id=location_id).first()
                        
                        url = 'http://api.uber.com/v1/products?latitude=%s&longitude=%s'%(location_get.lat,location_get.lng)
                       
                        server_token = ''
                        uber_payload = {'latitude':location_get.lat, 'longitude':location_get.lng}
                        uber_header = {'Authorization':server_token, 'Accept-Language':'en_US', 'Content-Type':'application/json'}
                        usearch_req = requests.get(url, params=uber_payload, headers=uber_header)
                        usearch_json = usearch_req.json()
                        total_products = len(usearch_json["products"])
                        print total_products
                        return json.dumps({'Cars nearby':total_products})
                except AttributeError:
                        abort(404)

@app.route('/lyftproductsnear/<location_id>', methods=['GET'])
def location_lyftproducts(location_id):
                try:
                        location_get = Location.query.filter_by(id=location_id).first()
                        
                        url = 'http://api.lyft.com/v1/ridetypes?lat=%s&lng=%s'%(location_get.lat,location_get.lng)
                        #print url
                        lyft_server_token = ''
                        lyft_payload = {'latitude':location_get.lat, 'longitude':location_get.lng}
                        lyft_header = {'Authorization':lyft_server_token, 'Accept-Language':'en_US', 'Content-Type':'application/json'}
                        lyft_usearch_req = requests.get(url, params=lyft_payload, headers=lyft_header)
                        apidata = lyft_usearch_req.json()
                        total_products = len(apidata["ride_types"])
                        return json.dumps({'Cars nearby':total_products})
                except AttributeError:
                        abort(404)                        
                        
# Post request for the Uber vs Lyft details
# input format:
# {
    # "start": 1,
    # "others" : [4,5,6],
    # "end": 1
# }	
##POST METHOD FOR TRIPS BASED ON location_id

@app.route("/trips", methods=["POST"])
def getPrice():
	val = json.loads(request.data)				# Input
	var = ProviderResult(val)					# Class for calculating the Uber and Lyft details
	x = var.genOutput()
	return x                        
                        

@app.route('/info')
def app_status():
	return json.dumps({'server_info':application.config['SQLALCHEMY_DATABASE_URI']})

##run app service 

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=5000, debug=True)
