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
            .order_by(desc(Participant.etat_init)).order_by(Participant.points_init)\
            .order_by(desc(Participant.etat_barr)).order_by(Participant.points_barr)\
            .order_by(desc(Participant.etat_barr2)).order_by(Participant.points_barr2).all()
        tot = len(p)
        print tot
        delta = 1
        if app.config['MIN_VALUE_SERIE_AUTO'] <= tot <= app.config['MAX_VALUE_SERIE_AUTO']:
            delta = 2
        i = 1
        min_p = -1
        min_p2 = -1
        etat1 = ""
        etat2 = ""
        min_pb = -1
        min_pb2 = -1
        etat_b1 = ""
        etat_b2 = ""
        min_pbb = -1
        min_pbb2 = -1
        etat_bb1 = ""
        etat_bb2 = ""
        num_s1 = 0
        num_s2 = 0
        r=1

        for pa in p:
            serie = pa.serie
            p_init = pa.points_init
            t_init = pa.temps_init
            p_barr = pa.points_barr
            t_barr = pa.temps_barr
            p_barr2 = pa.points_barr2
            t_barr2 = pa.temps_barr2

            if pa.temps_barr > 0:
                p_init = 0
                t_init = 0
            if pa.temps_barr2 > 0:
                p_barr = 0
                t_barr = 0

            if delta == 2:
                if i%2 == 0:
                    serie = 2
                    num_s2 +=1
                    if t_barr2 > 0:
                        if p_barr2 == min_pbb2 and etat_bb2 == pa.etat_barr2:
                            r-=1
                        else:
                            min_pbb2 = p_barr2
                            etat_bb2 = pa.etat_barr2
                            r = num_s2
                    elif t_barr > 0 :
                        if p_barr == min_pb2 and etat_b2 == pa.etat_barr:
                            r-=1
                        else:
                            min_pb2 = p_barr
                            etat_b2 = pa.etat_barr
                            r = num_s2
                    else:
                        if p_init == min_p2 and etat2 == pa.etat_init:
                            r-=1
                        else:
                            min_p2 = p_init
                            etat2 == pa.etat_init
                            r = num_s2
                else:
                    num_s1 +=1
                    if t_barr2 > 0:
                        if p_barr2 == min_pbb and etat_bb1 == pa.etat_barr2:
                            r-=1
                        else:
                            min_pbb = p_barr2
                            etat_bb1 = pa.etat_barr2
                            r = num_s1
                    elif t_barr > 0 :
                        if p_barr == min_pb and etat_b1 == pa.etat_barr:
                            r-=1
                        else:
                            min_pb = p_barr
                            etat_b1 = pa.etat_barr
                            r = num_s1
                    else:
                        if p_init == min_p and etat1 == pa.etat_init:
                            r-=1
                        else:
                            min_p = p_init
                            etat1 = pa.etat_init
                            r = num_s1
            else:
                if t_barr2 > 0:
                    if p_barr2 == min_pbb and etat_bb1 == pa.etat_barr2:
                        r-=1
                    else:
                        min_pbb = p_barr2
                        etat_bb1 = pa.etat_barr2
                        r = i
                elif t_barr > 0 :
                    if p_barr == min_pb and etat_b1 == pa.etat_barr:
                        r-=1
                    else:
                        min_pb = p_barr
                        etat_b1 = pa.etat_barr
                        r = i
                else:
                    if p_init == min_p and pa.etat_init == etat1:
                        r-=1
                    else:
                        min_p = p_init
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
                'points_init': p_init,
                'temps_init':t_init,
                'etat_init':pa.etat_init,
                'points_barr': p_barr,
                'temps_barr':t_barr,
                'etat_barr':pa.etat_barr,
                'points_barr2': p_barr2,
                'temps_barr2':t_barr2,
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
    #print res
    #print ((item['rang'],item['temps_init'],item['points_init']) for item in res if item["num_depart"] == 2).next()
    return res

def getDesc():
    return 'Barème A sans chrono avec barrage'