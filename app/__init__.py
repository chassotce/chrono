__author__ = 'chassotce'
from flask import Flask
from flask_restful import Api
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config.from_object('config')
api = Api(app)
auth = HTTPBasicAuth()
db = SQLAlchemy(app)



print('__init__')
if not os.path.exists(app.config['DATABASE_LOCATION']):
    print 'check'
    db.create_all()
    print 'yes'

import models

