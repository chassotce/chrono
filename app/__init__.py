__author__ = 'chassotce'
from flask import Flask
from flask_restful import Api
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from json import load
import os

app = Flask(__name__)
app.config.from_object('config')
api = Api(app)
auth = HTTPBasicAuth()
db = SQLAlchemy(app)

with open(app.config['CONFIG_FILE']) as file:
    result = load(file)
    app.config['TMP_CHARGE_CHRONO'] = result['tmp_charge_chrono']
    app.config['TMP_AFF_TEMPS'] = result['tmp_aff_temps']
    app.config['TMP_AFF_CLASSEMENT'] = result['tmp_aff_class']
file.close()



import models

print('__init__')
if not os.path.exists(app.config['DATABASE_LOCATION']):
    print 'check'
    print db.create_all()
    print 'yes'

import Rs232capture
captureThread = Rs232capture.RS232captureThread()
if not captureThread.isAlive():
    captureThread.start()


