from flask import Flask, render_template, jsonify, request
import requests
from key import geo_key, lyft_key, uber_key
import json
from customClass import ProviderResult, app, PriceDiff

#app = Flask(__name__)

geo_url = 'https://maps.googleapis.com/maps/api/geocode/json'
lyft_url = 'https://api.lyft.com/v1/cost'
uber_url = 'https://api.uber.com/v1.2/estimates/price'

@app.route('/')
def index():
	return 'Hello! Uber vs Lyft Prices'
	
@app.route("/trips/", methods=["POST"])
def getInput():
	val = json.loads(request.data)
	var = ProviderResult(val)
	x = var.genOutput()
	#var = PriceDiff(val)
	#x = var.printPts()
	return x

	
if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080, debug=True)