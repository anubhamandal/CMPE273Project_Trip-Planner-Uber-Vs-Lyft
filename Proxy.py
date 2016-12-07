"""
Proxy Server
@author: Uday Dungarwal, uday.dungarwal@sjsu.edu

Requirements: Flask, Requests, Logging
Use Case:
1. Dynamic host registration
2. Redirect requests to in-memory hosts
3. Retry request with different host if HTTP Status-Code >=500
"""

from flask import Flask
from flask import request, Response
import requests
import logging

"""CONSTANTS"""

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("Proxy")
APPROVED_HOSTS = ["http://localhost:8080", "http://localhost:8082", "http://localhost:8081"]
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

"""POST LOCATION"""


@app.route(LOCATIONS_API, methods=['POST'])
def post_locations():
    def func(count):
        url = get_host() + LOCATIONS_API
        LOG.info("Fetching %s", url)
        try:
            r = post_request(url, request.get_data())
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
    return parse_response(func(retry_count))

"""GET/UPDATE/DELETE LOCATION"""


@app.route(LOCATIONS_API + '/<location_id>', methods=['GET', 'PUT', 'DELETE'])
def change_locations(location_id):
    def func(count):
        url = get_host() + LOCATIONS_API + '/' + location_id
        LOG.info("Processing {} on {}".format(request.method, url))
        try:
            if request.method == 'GET':
                r = get_request(url)
            elif request.method == 'DELETE':
                r = delete_request(url)
            elif request.method == 'PUT':
                r = update_request(url, request.get_data())
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
    return parse_response(func(retry_count))

"""POST TRIP"""


@app.route(TRIPS_API, methods=['POST'])
def post_trips():
    def func(count):
        url = get_host() + TRIPS_API
        LOG.info("Fetching %s", url)
        try:
            r = post_request(url, request.get_data())
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
    return parse_response(func(retry_count))

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
    if r.status_code != 500:
        resp = Response(r.text, status=r.status_code)
    else:
        resp = Response("Internal Error", status=r.status_code)
    return resp


def parse_exception(e):
    LOG.error(e.message)
    return Response("Internal Error", status=500)

""" MAIN """


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)