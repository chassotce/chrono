__author__ = 'chassotce'
from app import db
from models import Participant,Epreuve


baremes=[
            {
            'code':0,
            'nom':'Bareme A au chrono'
            },
            {
            'code':1,
            'nom':'Bareme A sans chrono'
            },
            {
            'code':2,
            'nom':'Bareme A sans chrono avec barrage'
            },
            {
            'code':3,
            'nom':'Bareme A sans chrono avec un tour du vainqueur'
            },
            {
            'code':4,
            'nom':'Bareme C'
            }
        ]

def AAvecChrono():
    print "A avec chrono.\n"
    return 1

def ASansChrono():
    print "A sans chrono\n"
    return 1

def ASansChronoAvecBarr():
    print "A sans chrono avec barrage\n"
    return 1

def ASansChronoTourV():
    print "A sans chrono tour du vainqueur\n"
    return 1

def C():
    print "C\n"
    return 1

options = {
    0 : AAvecChrono,
    1 : ASansChrono,
    2 : ASansChronoAvecBarr,
    3 : ASansChronoTourV,
    4 : C,
}

class Baremes:
    @staticmethod
    def getBaremes():
        return baremes

    @staticmethod
    def doBaremes(num):
        a = options[num]()
        print a
        print db.session.query(Epreuve).all()
        print db.session.query(Participant).all()