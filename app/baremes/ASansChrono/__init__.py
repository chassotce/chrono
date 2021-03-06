__author__ = 'chassotce'
# coding=utf-8
from app import app
from app import db
from app.models import Participant,Epreuve
from sqlalchemy import desc
from math import ceil

def classement(epreuve):
    e = db.session.query(Epreuve).filter_by(id_epreuve=epreuve).one()
    n = e.nb_serie
    z=1
    res = []
    while z<=n:
        p = db.session.query(Participant).filter_by(id_epreuve = epreuve,hc=False,serie=z)\
            .filter(Participant.temps_init >= app.config['TMP_CHARGE_CHRONO'])\
            .order_by(desc(Participant.etat_init)).order_by(Participant.points_init).all()
        tot = len(p)
        delta = 1
        if app.config['MIN_VALUE_SERIE_AUTO'] < tot <= app.config['MAX_VALUE_SERIE_AUTO']:
            delta = 2
        i = 1
        min_p = -1
        min_p2 = -1
        etat1 = ""
        etat2 = ""
        num_s1 = 0
        num_s2 = 0
        r=1
        for pa in p:
            serie = pa.serie
            if delta ==2 :
                if i%2 == 0:
                    serie = 2
                    num_s2 +=1
                    if pa.points_init == min_p2  and pa.etat_init == etat2:
                        r -= 1
                    else :
                        min_p2 = pa.points_init
                        etat2 = pa.etat_init
                        r = num_s2
                else:
                    num_s1 +=1
                    if pa.points_init == min_p and pa.etat_init == etat1:
                        r -= 1
                    else :
                        min_p = pa.points_init
                        etat1 = pa.etat_init
                        r = num_s1

            else:
                if pa.points_init == min_p and pa.etat_init == etat1:
                    r -=1
                else:
                    min_p = pa.points_init
                    etat1 = pa.etat_init
                    r = i
            cl = (r <= ceil(((tot/delta) *app.config['NUMBER_OF_CL'])))
            pa = {
                'rang': r,
                'cl' : cl,
                'id':pa.id_participant,
                'num_depart': pa.num_depart,
                'nom_monture': pa.nom_monture,
                'nom_cavalier': pa.nom_cavalier,
                'points_init': pa.points_init,
                'temps_init':pa.temps_init,
                'etat_init':pa.etat_init,
                'points_barr': pa.points_barr,
                'temps_barr':pa.temps_barr,
                'etat_barr':pa.etat_barr,
                'points_barr2': pa.points_barr2,
                'temps_barr2':pa.temps_barr2,
                'etat_barr2':pa.etat_barr2,
                'hc':pa.hc,
                'serie':serie,
                'id_epreuve': pa.id_epreuve
            }
            res.append(pa)
            if (i % delta)==0 :
                r +=1
            i +=1
        z+=1
    return res

def getDesc():
    return 'Barème A sans chrono'