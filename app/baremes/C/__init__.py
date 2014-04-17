# coding=utf-8
from app import app
from app import db
from app.models import Participant
from sqlalchemy import desc

__author__ = 'chassotce'
def classement(epreuve):
    p = db.session.query(Participant).filter_by(id_epreuve = epreuve,hc=False).filter(Participant.temps_init >= app.config['TMP_CHARGE_CHRONO'])\
        .order_by(desc(Participant.etat)).order_by(Participant.temps_init).all()
    tot = len(p)
    i = 0
    res = []
    for pa in p:
        i = i+1
        hc = (i <= (tot *app.config['NUMBER_OF_CL']))
        pa = {
            'rang': i,
            'cl' : hc,
            'id':pa.id_participant,
            'num_depart': pa.num_depart,
            'nom_monture': pa.nom_monture,
            'nom_cavalier': pa.nom_cavalier,
            'points_init': pa.points_init,
            'temps_init':pa.temps_init,
            'points_barr': pa.points_barr,
            'temps_barr':pa.temps_barr,
            'points_barr2': pa.points_barr2,
            'temps_barr2':pa.temps_barr2,
            'hc':pa.hc,
            'etat':pa.etat,
            'serie':pa.serie,
            'id_epreuve': pa.id_epreuve
        }
        res.append(pa)
    print res
    print ((item['rang'],item['temps_init'],item['points_init']) for item in res if item["num_depart"] == 2).next()
    return res

def getDesc():
    return 'Barème C'