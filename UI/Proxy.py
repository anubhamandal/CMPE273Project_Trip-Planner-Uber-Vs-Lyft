"""
Proxy Server
@author: Uday Dungarwal, uday.dungarwal@sjsu.edu

Requirements: Flask, Requests, Logging
Use Case:
1. Dynamic host registration
2. Redirect requests to in-memory hosts
3. Retry request with different host if HTTP Status-Code >=500
"""

from flask import Flask, redirect, url_for
from flask import request, Response
from wtforms import Form, TextField, validators
from flask import render_template
import json
from flask import jsonify
import requests
import logging

"""CONSTANTS"""

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("Proxy")
APPROVED_HOSTS = ["http://localhost:5000", "http://localhost:5001", "http://localhost:5000"]
CURRENT_HOST = 0
TRIPS_API = '/trips'
LOCATIONS_API = '/locations'
HOSTS_API = '/hosts'


def get_host():
    global CURRENT_HOST
    c = CURRENT_HOST
    if CURRENT_HOST == len(APPROVED_HOSTS)-1:
        CURRENT_HOST = 0
    else:
        CURRENT_HOST += 1
    return APPROVED_HOSTS[c]


def get_all_hosts():
    hosts = {}
    for n, h in enumerate(APPROVED_HOSTS):
        hosts[n+1] = h
    return hosts


@app.route('/')
def index():
    return render_template('index.html')


"""POST LOCATION"""


@app.route(LOCATIONS_API, methods=['POST'])
def post_locations():
    def func(count):
        address = json.dumps(request.form)
        url = get_host() + LOCATIONS_API
        LOG.info("Fetching %s", url)
        try:
            r = post_request(url, address)
            if r.status_code >= 500:
                if count < len(APPROVED_HOSTS):
                    count += 1
                    LOG.error("Error {}, Retrying {}".format(r.status_code, count))
                    r = func(count)
        except requests.ConnectionError as e:
            if count < len(APPROVED_HOSTS):
                count += 1
                LOG.error("Error {}, Retrying {}".format(e.message, count))
                r = func(count)
            else:
                r = parse_exception(e)
                return r
        return r
    retry_count = 1
    return parse_responseview(func(retry_count))

"""GET/UPDATE/DELETE LOCATION"""

@app.route('/',methods=['POST'])
def search():
    location = request.form['location']
    return redirect((url_for('change_locations', location_id = location)))


@app.route(LOCATIONS_API + '/<location_id>', methods=['GET'])
def change_locations(location_id):
    def func(count):
        data = {}
        url = get_host() + LOCATIONS_API + '/' + location_id
        LOG.info("Processing {} on {}".format(request.method, url))
        try:
            if request.method == 'GET':
                r = get_request(url)
            # elif request.method == 'DELETE':
            #     r = delete_request(url)
            # elif request.method == 'PUT':
            #     r = update_request(url, request.get_data())
            if r.status_code >= 500:
                if count < len(APPROVED_HOSTS):
                    count += 1
                    LOG.error("Error {}, Retrying {}".format(r.status_code, count))
                    r = func(count)
        except requests.ConnectionError as e:
            if count < len(APPROVED_HOSTS):
                count += 1
                LOG.error("Error {}, Retrying {}".format(e.message, count))
                r = func(count)
            else:
                r = parse_exception(e)

        return r
    retry_count = 1
    return parse_responsechange(func(retry_count))

"""UPDATE/DELETE LOCATION"""


@app.route(LOCATIONS_API + '/<location_id>', methods=['POST'])
def update_locations(location_id):
    def func(count):
        name = requests.form['lname']
        url = get_host() + LOCATIONS_API + '/' + location_id
        LOG.info("Processing {} on {}".format(request.method, url))
        try:
            if request.method == 'POST':
                r = update_request(url, json.dumps(name))
            # elif request.method == 'DELETE':
            #     r = delete_request(url)
            # elif request.method == 'PUT':
            #     r = update_request(url, request.get_data())
            if r.status_code >= 500:
                if count < len(APPROVED_HOSTS):
                    count += 1
                    LOG.error("Error {}, Retrying {}".format(r.status_code, count))
                    r = func(count)
        except requests.ConnectionError as e:
            if count < len(APPROVED_HOSTS):
                count += 1
                LOG.error("Error {}, Retrying {}".format(e.message, count))
                r = func(count)
            else:
                r = parse_exception(e)
        return r
    retry_count = 1
    return parse_responsechange(func(retry_count))

    

"""POST TRIP"""


@app.route(TRIPS_API, methods=['POST'])
def post_trips():
    def func(count):
        others = request.form['others']
        otherslist = others.split(',')
        start = request.form['start']
        end = request.form['end']
        trip = {"start" : start, "others" : otherslist, "end" : end}
        url = get_host() + TRIPS_API
        LOG.info("Fetching %s", url)
        try:
            r = post_request(url, json.dumps(trip))
            if r.status_code >= 500:
                if count < len(APPROVED_HOSTS):
                    count += 1
                    LOG.error("Error {}, Retrying {}".format(r.status_code, count))
                    r = func(count)
        except requests.ConnectionError as e:
            if count < len(APPROVED_HOSTS):
                count += 1
                LOG.error("Error {}, Retrying {}".format(e.message, count))
                r = func(count)
            else:
                r = parse_exception(e)
        return r
    retry_count = 1
    return parse_responsetrips(func(retry_count))

"""HOSTS"""


@app.route(HOSTS_API, methods=['PUT'])
def post_hosts():
    global APPROVED_HOSTS
    APPROVED_HOSTS.append(request.data)
    LOG.info("Updated hosts with {}".format(request.data))
    resp = Response("{}".format(get_all_hosts()), status=200)
    return resp


@app.route(HOSTS_API + '/<host_id>', methods=['DELETE'])
def delete_hosts(host_id):
    global APPROVED_HOSTS
    if host_id-1 <= len(APPROVED_HOSTS):
        APPROVED_HOSTS.pop(int(host_id)-1)
        LOG.info("Deleted {} from hosts".format(request.data))
    resp = Response("{}".format(get_all_hosts()), status=200)
    return resp


@app.route(HOSTS_API, methods=['GET'])
def get_hosts():
    resp = Response("{}".format(get_all_hosts()), status=200)
    return resp

""" REQUEST APIs """


def post_request(url, json_data, headers=None):
    r = requests.post(url, data=json_data, headers=headers)
    return r


def get_request(url, params=None, headers=None):
    r = requests.get(url, params=params, headers=headers)
    return r


def delete_request(url):
    r = requests.delete(url)
    return r


def update_request(url, json_data):
    r = requests.put(url, data=json_data)
    return r

"""RESPONSE APIs"""


def parse_response(r):
    LOG.info("Response %s", r.status_code)
    if r.status_code < 400:
        resp = Response(r.text, status=r.status_code)
    else:
        resp = Response("Internal Error", status=r.status_code)
    return resp

def parse_responsechange(r):
    LOG.info("Response %s", r.status_code)
    if r.status_code < 400:
        data = json.loads(r.text)
        coordinate = data['coordinate']
        resp = Response(r.text, status=r.status_code)
        return render_template("search.html", data= data, coordinate = coordinate)
    else:
        resp = Response("Internal Error", status=r.status_code)
        return resp

def parse_responseview(r):
    LOG.info("Response %s", r.status_code)
    if r.status_code < 400:
        data = json.loads(r.text)
        coordinate = data['coordinate']
        resp = Response(r.text, status=r.status_code)
        return render_template("locations.html", data= data, coordinate = coordinate)
    else:
        resp = Response("Internal Error", status=r.status_code)
        return resp
    

def parse_responsetrips(r):
    LOG.info("Response %s", r.status_code)
    if r.status_code < 400:
        trip = json.loads(r.text)
        providers = trip['providers']
        resp = Response(r.text, status=r.status_code)
        return render_template("showtrips.html", trip = trip, providers = providers)
    else:
        resp = Response("Internal Error", status=r.status_code)
        return resp


def parse_exception(e):
    LOG.error(e.message)
    return Response("Internal Error", status=500)

""" MAIN """


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)