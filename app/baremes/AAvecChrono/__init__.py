# coding=utf-8
from app.models import Participant

def classement(epreuve):
    print Participant.query.all()
    print("Hello from a aac!")

def getDesc():
    return 'Barème A avec chrono'
