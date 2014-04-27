__author__ = 'chassotce'
from app import db,api,app
from flask_restful import Resource, marshal, abort,reqparse,fields
import json
from json import load
from flask import jsonify
import sqlite3,datetime


class Epreuve(db.Model):
    __tablename_ = 'epreuve'
    id_epreuve = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(32),unique=True)
    bareme_code = db.Column(db.String(32))
    temps_accorde = db.Column(db.Integer)
    nb_serie = db.Column(db.Integer,default=1)

class Participant(db.Model):
    __tablename__ = 'participant'
    id_participant = db.Column(db.Integer, primary_key=True)
    num_depart = db.Column(db.Integer,index=True)
    nom_monture = db.Column(db.String(32))
    nom_cavalier = db.Column(db.String(32))
    points_init = db.Column(db.Integer,index=True,default=0)
    temps_init = db.Column(db.Integer,default=0)
    etat_init = db.Column(db.Enum("undef", "elimine", "abandon"),name='etat_init',default="undef")
    points_barr = db.Column(db.Integer,index=True,default=0)
    temps_barr = db.Column(db.Integer,default=0)
    etat_barr = db.Column(db.Enum("undef", "elimine", "abandon"),name='etat_barr',default="undef")
    points_barr2 = db.Column(db.Integer,index=True,default=0)
    temps_barr2 = db.Column(db.Integer,default=0)
    etat_barr2 = db.Column(db.Enum("undef", "elimine", "abandon"),name='etat_barr2',default="undef")
    hc = db.Column(db.Boolean(),default=False)
    serie = db.Column(db.Integer,default=1)
    id_epreuve = db.Column(db.Integer, db.ForeignKey(Epreuve.id_epreuve), nullable=False)

def add_bdd():
    epreuve = Epreuve(nom='mon_epreuve',bareme_code=1,temps_accorde=10,nb_serie=1)
    print(epreuve.nom)
    db.session.add(epreuve)
    db.session.commit()

    participant = Participant(id_epreuve=epreuve.id_epreuve)
    db.session.add(participant)
    db.session.commit()


config_fields = {
    'tmp_charge_chrono': fields.Integer,
    'tmp_aff_temps': fields.Integer,
    'tmp_aff_class': fields.Integer,
    'pen_tmps_depasse': fields.Float,
    'pen_tmps_depasse_barr': fields.Float,
    'pen_tmps_depasse_2_phase': fields.Float,
    'send_aff': fields.Boolean
}

class Config(Resource):
    #decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tmp_charge_chrono', type = int, location = 'json')
        self.reqparse.add_argument('tmp_aff_temps', type = int, location = 'json')
        self.reqparse.add_argument('tmp_aff_class', type = int, location = 'json')
        self.reqparse.add_argument('pen_tmps_depasse', type = float, location = 'json')
        self.reqparse.add_argument('pen_tmps_depasse_barr', type = float, location = 'json')
        self.reqparse.add_argument('pen_tmps_depasse_2_phase', type = float, location = 'json')
        self.reqparse.add_argument('send_aff', type = bool, location = 'json')
        super(Config, self).__init__()

    def get(self):
        with open(app.config['CONFIG_FILE']) as file:
            result = load(file)
        file.close()
        result['pen_tmps_depasse'] = app.config['A_TEMPS_DEPASSE']
        result['pen_tmps_depasse_barr'] = app.config['A_TEMPS_DEPASSE_BARR']
        result['pen_tmps_depasse_2_phase'] = app.config['A_TEMPS_DEPASSE_2PHASE']
        result['send_aff'] = app.config['SEND_AFF']
        return {'config':marshal(result, config_fields)}

    def put(self):
        args = self.reqparse.parse_args()
        print args['tmp_charge_chrono'],args['tmp_aff_temps'],args['tmp_aff_class'],args['pen_tmps_depasse']
        with open(app.config['CONFIG_FILE'], "r+") as configfile:
            data = load(configfile)
            app.config['TMP_CHARGE_CHRONO'] = data['tmp_charge_chrono'] = args['tmp_charge_chrono']
            app.config['TMP_AFF_TEMPS'] = data['tmp_aff_temps'] = args['tmp_aff_temps']
            app.config['TMP_AFF_CLASSEMENT'] = data['tmp_aff_class'] = args['tmp_aff_class']
            configfile.seek(0)
            json.dump(data, configfile, indent=4)
            configfile.truncate()
        configfile.close()
        app.config['A_TEMPS_DEPASSE'] = args['pen_tmps_depasse']
        app.config['A_TEMPS_DEPASSE_BARR'] = args['pen_tmps_depasse_barr']
        app.config['A_TEMPS_DEPASSE_2PHASE'] = args['pen_tmps_depasse_2_phase']
        app.config['SEND_AFF'] = args['send_aff']
        print args['tmp_charge_chrono'],args['tmp_aff_temps'],args['tmp_aff_class'],args['pen_tmps_depasse'],\
            args['pen_tmps_depasse_barr'],args['pen_tmps_depasse_2_phase'],args['send_aff']
        return {'config':marshal(args, config_fields)}

    def options(self):
        return {'Allow' : 'GET,PUT' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'PUT,GET' }

class Compet(Resource):
    def get(self):
        con = sqlite3.connect(app.config['DATABASE_LOCATION'])
        backupname = app.config['BACKUP_DIR']+'/'+datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")+'.sql'
        with open(backupname, 'w') as f:
            for line in con.iterdump():
                f.write('%s\n' % line)
        con.close()
        db.metadata.tables.items()
        for name,table in db.metadata.tables.items():
            table.delete()
        db.drop_all()
        db.create_all()
        return {'success':'true'}

    def options(self):
        return {'Allow' : 'GET' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'GET' }

epreuve_fields = {
    'id' : fields.Integer,
    'nom': fields.String,
    'bareme_code': fields.String,
    'temps_accorde': fields.Integer,
    'nb_serie': fields.Integer,
    'uri': fields.Url('epreuve')
}

epreuves = []

class EpreuveList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('nom', type = str, location = 'json')
        self.reqparse.add_argument('bareme_code', type = str, location = 'json')
        self.reqparse.add_argument('temps_accorde', type = int, location = 'json')
        self.reqparse.add_argument('nb_serie', type = int, location = 'json')
        super(EpreuveList, self).__init__()

    def get(self):
        epreuves = []
        result = Epreuve.query.all()
        for ep in result:
            epr = {
                'id':ep.id_epreuve,
                'nom':ep.nom,
                'bareme_code':ep.bareme_code,
                'temps_accorde':ep.temps_accorde,
                'nb_serie':ep.nb_serie
            }
            epreuves.append(epr)
        return {'epreuves': map(lambda t: marshal(t, epreuve_fields), epreuves)}

    def post(self):
        args = self.reqparse.parse_args()
        if args['nb_serie']< 1:
            args['nb_serie'] = 1
        epreuve = Epreuve(nom=args['nom'],bareme_code=args['bareme_code'],temps_accorde=args['temps_accorde'],nb_serie=args['nb_serie'])
        db.session.add(epreuve)
        db.session.commit()
        epr = {
                'id':epreuve.id_epreuve,
                'nom':epreuve.nom,
                'bareme_code':epreuve.bareme_code,
                'temps_accorde':epreuve.temps_accorde,
                'nb_serie':epreuve.nb_serie
            }
        return {'epreuve':marshal(epr, epreuve_fields)}

    def options(self):
        return {'Allow' : 'GET,PUT' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'PUT,GET' }


class EpreuveSingle(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('nom', type = str, location = 'json')
        self.reqparse.add_argument('bareme_code', type = str, location = 'json')
        self.reqparse.add_argument('temps_accorde', type = str, location = 'json')
        self.reqparse.add_argument('nb_serie', type = int, location = 'json')
        super(EpreuveSingle, self).__init__()

    def get(self,id):
        tt = epreuve = db.session.query(Epreuve).filter_by(id_epreuve=id).one()
        if tt == 0:
            abort(404)
        epr = {
                'id':epreuve.id_epreuve,
                'nom':epreuve.nom,
                'bareme_code':epreuve.bareme_code,
                'temps_accorde':epreuve.temps_accorde,
                'nb_serie':epreuve.nb_serie
            }
        return {'epreuve':marshal(epr,epreuve_fields)}

    def put(self,id):
        args = self.reqparse.parse_args()
        print args['bareme_code']
        if args['nb_serie']< 1:
            args['nb_serie'] = 1
        epr = {
            'id':id,
            'nom':args['nom'],
            'bareme_code':args['bareme_code'],
            'temps_accorde':args['temps_accorde'],
            'nb_serie':args['nb_serie']
        }
        tt = db.session.query(Epreuve).filter_by(id_epreuve=id).update({"nom":epr['nom'],"bareme_code":epr['bareme_code'],"temps_accorde":epr['temps_accorde'],"nb_serie":epr['nb_serie']})
        if tt == 0:
            abort(404)
        db.session.commit()
        return {'epreuve':marshal(epr,epreuve_fields)}

    def delete(self,id):
        tt= db.session.query(Epreuve).filter_by(id_epreuve=id).delete()
        if tt == 0:
            abort(404)
        db.session.query(Participant).filter_by(id_epreuve=id).delete()

        db.session.commit()
        return { 'result': True }

    def options(self):
        return {'Allow' : 'GET,PUT,DELETE' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'PUT,GET,DELETE' }

participant_fields = {
    'id':fields.Integer,
    'num_depart': fields.Integer,
    'nom_monture': fields.String,
    'nom_cavalier': fields.String,
    'points_init': fields.Float,
    'temps_init':fields.Integer,
    'etat_init':fields.String,
    'points_barr': fields.Float,
    'temps_barr':fields.Integer,
    'etat_barr':fields.String,
    'points_barr2': fields.Float,
    'temps_barr2':fields.Integer,
    'etat_barr2':fields.String,
    'hc':fields.Boolean,
    'serie':fields.Integer,
    'id_epreuve': fields.Integer,
    'uri': fields.Url('participant')
}

participant_fields_rang = {
    'id':fields.Integer,
    'rang':fields.Integer,
    'cl':fields.Boolean,
    'num_depart': fields.Integer,
    'nom_monture': fields.String,
    'nom_cavalier': fields.String,
    'points_init': fields.Float,
    'temps_init':fields.Integer,
    'etat_init':fields.String,
    'points_barr': fields.Float,
    'temps_barr':fields.Integer,
    'etat_barr':fields.String,
    'points_barr2': fields.Float,
    'temps_barr2':fields.Integer,
    'etat_barr2':fields.String,
    'hc':fields.Boolean,
    'serie':fields.Integer,
    'id_epreuve': fields.Integer,
    'uri': fields.Url('participant')
}

class ParticipantList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('num_depart', type = int, location = 'json')
        self.reqparse.add_argument('nom_monture', type = str, location = 'json')
        self.reqparse.add_argument('nom_cavalier', type = str, location = 'json')
        self.reqparse.add_argument('points_init', type = float, location = 'json')
        self.reqparse.add_argument('temps_init', type = int, location = 'json')
        self.reqparse.add_argument('etat_init', type =str, location = 'json')
        self.reqparse.add_argument('points_barr', type = float, location = 'json')
        self.reqparse.add_argument('temps_barr', type = int, location = 'json')
        self.reqparse.add_argument('etat_barr', type =str, location = 'json')
        self.reqparse.add_argument('points_barr2', type = float, location = 'json')
        self.reqparse.add_argument('temps_barr2', type = int, location = 'json')
        self.reqparse.add_argument('etat_barr2', type =str, location = 'json')
        self.reqparse.add_argument('hc', type =bool, location = 'json')
        self.reqparse.add_argument('serie', type =int, location = 'json')
        self.reqparse.add_argument('id_epreuve', type =int, location = 'json')
        super(ParticipantList, self).__init__()

    def get(self,id_epreuve):
        participants = []
        result = db.session.query(Participant).filter_by(id_epreuve=id_epreuve).all()
        print result
        for pa in result:
            pa = {
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
                'serie':pa.serie,
                'id_epreuve': pa.id_epreuve
            }
            participants.append(pa)
        return {'participants': map(lambda t: marshal(t, participant_fields), participants)}

    def post(self,id_epreuve):
        args = self.reqparse.parse_args()
        print args['id_epreuve']
        print args['hc']
        if args['serie'] < 1:
            args['serie'] = 1;
        pa = Participant(num_depart=args['num_depart'],nom_monture=args['nom_monture'],nom_cavalier=args['nom_cavalier']\
            ,points_init=args['points_init'],temps_init=args['temps_init'],etat_init=args['etat_init'],\
                         points_barr=args['points_barr'],temps_barr=args['temps_barr'],etat_barr=args['etat_barr']
            ,points_barr2=args['points_barr2'],temps_barr2=args['temps_barr2'],etat_barr2=args['etat_barr2']\
            ,hc=args['hc'],serie=args['serie']\
            ,id_epreuve=id_epreuve)
        db.session.add(pa)
        db.session.commit()
        part = {
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
                'serie':pa.serie,
                'id_epreuve': pa.id_epreuve
            }
        print part
        return {'participant':marshal(part, participant_fields)}

    def options(self):
        return {'Allow' : 'GET,POST' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'PUT,POST' }

class ParticipantSingle(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('num_depart', type = int, location = 'json')
        self.reqparse.add_argument('nom_monture', type = str, location = 'json')
        self.reqparse.add_argument('nom_cavalier', type = str, location = 'json')
        self.reqparse.add_argument('points_init', type = float, location = 'json')
        self.reqparse.add_argument('temps_init', type = int, location = 'json')
        self.reqparse.add_argument('etat_init', type =str, location = 'json')
        self.reqparse.add_argument('points_barr', type = float, location = 'json')
        self.reqparse.add_argument('temps_barr', type = int, location = 'json')
        self.reqparse.add_argument('etat_barr', type =str, location = 'json')
        self.reqparse.add_argument('points_barr2', type = float, location = 'json')
        self.reqparse.add_argument('temps_barr2', type = int, location = 'json')
        self.reqparse.add_argument('etat_barr2', type =str, location = 'json')
        self.reqparse.add_argument('hc', type =bool, location = 'json')
        self.reqparse.add_argument('serie', type =int, location = 'json')
        self.reqparse.add_argument('id_epreuve', type =int, location = 'json')
        super(ParticipantSingle, self).__init__()

    def get(self,id):
        pa = db.session.query(Participant).filter_by(id_participant=id).first()
        print pa
        part = {
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
                'serie':pa.serie,
                'id_epreuve': pa.id_epreuve
            }
        return {'participant': marshal(part, participant_fields)}

    def put(self,id):
        args = self.reqparse.parse_args()
        if args['serie'] < 1:
            args['serie'] = 1;
        part = {
            'id':id,
            'num_depart': args['num_depart'],
            'nom_monture': args['nom_monture'],
            'nom_cavalier': args['nom_cavalier'],
            'points_init': args['points_init'],
            'temps_init':args['temps_init'],
            'etat_init':args['etat_init'],
            'points_barr': args['points_barr'],
            'temps_barr':args['temps_barr'],
            'etat_barr':args['etat_barr'],
            'points_barr2': args['points_barr2'],
            'temps_barr2':args['temps_barr2'],
            'etat_barr2':args['etat_barr2'],
            'hc':args['hc'],
            'serie':args['serie'],
            'id_epreuve': args['id_epreuve']
            }
        print part
        tt = db.session.query(Participant).filter_by(id_participant=id).update({"num_depart":args['num_depart'],\
            "nom_monture":args['nom_monture'],"nom_cavalier":args['nom_cavalier']\
            ,"points_init":args['points_init'],"temps_init":args['temps_init'],"etat_init":args['etat_init']\
            ,"points_barr":args['points_barr'],"temps_barr":args['temps_barr'],"etat_barr":args['etat_barr']\
            ,"points_barr2":args['points_barr2'],"temps_barr2":args['temps_barr2'],"etat_barr2":args['etat_barr2'],\
            "hc":args['hc'],"serie":args['serie'],"id_epreuve":args['id_epreuve']})

        if tt == 0:
            abort(404)
        db.session.commit()
        return {'participant':marshal(part, participant_fields)}

    def delete(self,id):
        tt= db.session.query(Participant).filter_by(id_participant=id).delete()
        if tt == 0:
            abort(404)
        db.session.commit()
        return { 'result': True }

    def options(self):
        return {'Allow' : 'GET,PUT,DELETE' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'GET,PUT,DELETE' }

from bareme import Baremes

class BaremesList(Resource):
    def get(self):
        return {'baremes': Baremes.getBaremes()}

class Bareme(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('epreuve_id',type=int,location='json')
        super(Bareme, self).__init__()

    def get(self):
        currentCode = db.session.query(Epreuve).filter(Epreuve.id_epreuve == app.config["CURRENT_EPREUVE_ID"])\
            .first()
        if currentCode==None:
            abort(404)
        currentCode = currentCode.bareme_code
        a = Baremes.doBaremes(currentCode,app.config["CURRENT_EPREUVE_ID"])
        return {'participants': map(lambda t: marshal(t, participant_fields_rang), a)}

    def post(self):
        args = self.reqparse.parse_args()
        currentCode = db.session.query(Epreuve).filter(Epreuve.id_epreuve == args['epreuve_id'])\
            .first()
        if currentCode==None:
            abort(404)
        currentCode = currentCode.bareme_code
        a = Baremes.doBaremes(currentCode,args['epreuve_id'])
        return {'participants': map(lambda t: marshal(t, participant_fields_rang), a)}
    def options(self):
        return {'Allow' : 'GET,POST' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'GET,POST' }



class SetEpreuve(Resource):
    def __init__(self):
        super(SetEpreuve,self).__init__()

    def get(self,id):
        app.config['CURRENT_EPREUVE_ID'] = id
        tt = epreuve = db.session.query(Epreuve).filter_by(id_epreuve=id).first()
        print tt
        if tt == None:
            abort(404)
        epr = {
                'id':epreuve.id_epreuve,
                'nom':epreuve.nom,
                'bareme_code':epreuve.bareme_code,
                'temps_accorde':epreuve.temps_accorde,
                'nb_serie':epreuve.nb_serie
            }
        return {'epreuve':marshal(epr,epreuve_fields)}

class CurrentEpreuve(Resource):
    def __init__(self):
        super(CurrentEpreuve,self).__init__()

    def get(self):
        id = app.config['CURRENT_EPREUVE_ID']
        print id
        tt = epreuve = db.session.query(Epreuve).filter_by(id_epreuve=id).first()
        if tt == None:
            abort(404)
        epr = {
                'id':epreuve.id_epreuve,
                'nom':epreuve.nom,
                'bareme_code':epreuve.bareme_code,
                'temps_accorde':epreuve.temps_accorde,
                'nb_serie':epreuve.nb_serie
            }
        return {'epreuve':marshal(epr,epreuve_fields)}

api.add_resource(Config, app.config['REST_PATH']+'config', endpoint='config')
api.add_resource(Compet,app.config['REST_PATH']+'new_compet',endpoint='compet')
api.add_resource(EpreuveList,app.config['REST_PATH']+'epreuves',endpoint='epreuves')
api.add_resource(EpreuveSingle,app.config['REST_PATH']+'epreuve/<int:id>',endpoint='epreuve')
api.add_resource(ParticipantList,app.config['REST_PATH']+'participants/<int:id_epreuve>',endpoint='participants')
api.add_resource(ParticipantSingle,app.config['REST_PATH']+'participant/<int:id>',endpoint='participant')
api.add_resource(BaremesList,app.config['REST_PATH']+'baremes',endpoint='baremes')
api.add_resource(Bareme,app.config['REST_PATH']+'bareme',endpoint='bareme')
api.add_resource(SetEpreuve,app.config['REST_PATH']+'setepreuve/<int:id>',endpoint='set_epreuve')
api.add_resource(CurrentEpreuve,app.config['REST_PATH']+'currentepreuve',endpoint='current_epreuve')
