from flask import Response

def home_response():
    Response("Welcome!", status=200, headers={'Content-type': 'text/html'})