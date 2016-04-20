# -*- coding: utf-8 -*-

from flask import Flask, session, request, g, json, make_response
import os, requests, sys
import psycopg2
from ciceron_lib import get_user_id, parse_request
from flask.ext.cors import CORS
from flask.ext.session import Session
from multiprocessing import Process
from translator import Translator

if os.environ.get('PURPOSE') == 'PROD':
    DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"
else:
    DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"

VERSION = '1.1'
DEBUG = True
GCM_API_KEY = 'AIzaSyDsuwrNC0owqpm6eznw6mUexFt18rBcq88'

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "sexycookie"

app = Flask(__name__)
app.secret_key = 'Yh1onQnWOJuc3OBQHhLFf5dZgogGlAnEJ83FacFv'
app.config.from_object(__name__)
app.project_number = 145456889576

Session(app)
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})

translator = Translator(developerKey=GCM_API_KEY)

def connect_db():
    return psycopg2.connect(app.config['DATABASE'])

def cut_sentences(sentences):
    sentences_array = sentences.split('\n')

    ready_to_translate_array = []
    for line in sentences_array:
        if len(line) > 2000:
            new_lines = line.split('.')
            for new_line in new_lines:
                ready_to_translate_array.append(new_line + '.')

        else:
            ready_to_translate_array.append(line)

    return ready_to_translate_array

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return make_response('Hello world!', 200)

@app.route('/translate', methods=['POST'])
def translate():
    client_ip = request.environ.get('REMOTE_ADDR')
    print (client_ip)
    #if client_ip not in ['52.196.144.144', '52.196.144.144']:
    #    return make_response(json.jsonify(
    #        message='Unauthorized'), 401)

    parameters = parse_request(request)
    user_email = parameters['user_email']
    paragragh = parameters['paragraph']
    source_lang_id = parameters['source_lang_id']
    target_lang_id = parameters['target_lang_id']

    # Check a user is member or not
    user_id = get_user_id(user_email)
    if user_id == -1:
        return make_response(json.jsonify(
            message='Forbidden'), 403)

    # Real work
    is_ok, result = translator.doWork(source_lang_id, target_lang_id, paragragh)
    if is_ok == False:
        return make_response(json.jsonify(
            message=""), 400)

    else:
        return make_response(json.jsonify(**result), 200)

if __name__ == "__main__":
    # Should be masked!
    app.run(host="0.0.0.0", port=5000)
