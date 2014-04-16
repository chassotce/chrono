from app import models,db

def classement():
    print models.Participant.query.all()
    print("Hello from a aac!")

def getDesc():
    return 'Bareme A avec chrono'
