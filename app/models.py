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
    points_init = db.Column(db.Integer,index=True)
    temps_init = db.Column(db.Integer)
    points_barr = db.Column(db.Integer,index=True)
    temps_barr = db.Column(db.Integer)
    points_barr2 = db.Column(db.Integer,index=True)
    temps_barr2 = db.Column(db.Integer)
    hc = db.Column(db.Boolean())
    etat = db.Column(db.Enum("undef", "elimine", "abandon"),name='etat')
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
    'tmp_aff_class': fields.Integer
}

class Config(Resource):
    #decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tmp_charge_chrono', type = int, location = 'json')
        self.reqparse.add_argument('tmp_aff_temps', type = int, location = 'json')
        self.reqparse.add_argument('tmp_aff_class', type = int, location = 'json')
        super(Config, self).__init__()

    def get(self):
        with open(app.config['CONFIG_FILE']) as file:
            result = load(file)
        file.close()
        return {'config':marshal(result, config_fields)}

    def put(self):
        args = self.reqparse.parse_args()
        with open(app.config['CONFIG_FILE'], "r+") as configfile:
            data = load(configfile)
            app.config['TMP_CHARGE_CHRONO'] = data['tmp_charge_chrono'] = args['tmp_charge_chrono']
            app.config['TMP_AFF_TEMPS'] = data['tmp_aff_temps'] = args['tmp_aff_temps']
            app.config['TMP_AFF_CLASSEMENT'] = data['tmp_aff_class'] = args['tmp_aff_class']
            configfile.seek(0)
            json.dump(data, configfile, indent=4)
            configfile.truncate()
        configfile.close()
        return {'config':marshal(data, config_fields)}

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
        db.create_all()
        return {'success':'true'}

    def options(self):
        return {'Allow' : 'GET' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'GET' }

epreuve_fields = {
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
        self.reqparse.add_argument('bareme_code', type = int, location = 'json')
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
        db.session.commit()
        return { 'result': True }

    def options(self):
        return {'Allow' : 'GET,PUT' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'PUT,GET' }

participant_fields = {
    'num_depart': fields.Integer,
    'nom_monture': fields.String,
    'nom_cavalier': fields.String,
    'points_init': fields.Integer,
    'temps_init':fields.Integer,
    'points_barr': fields.Integer,
    'temps_barr':fields.Integer,
    'points_barr2': fields.Integer,
    'temps_barr2':fields.Integer,
    'hc':fields.Boolean,
    'etat':fields.String,
    'serie':fields.Integer,
    'id_epreuve': fields.Integer,
    'uri': fields.Url('participant')
}

participant_fields_rang = {
    'rang':fields.Integer,
    'cl':fields.Boolean,
    'num_depart': fields.Integer,
    'nom_monture': fields.String,
    'nom_cavalier': fields.String,
    'points_init': fields.Integer,
    'temps_init':fields.Integer,
    'points_barr': fields.Integer,
    'temps_barr':fields.Integer,
    'points_barr2': fields.Integer,
    'temps_barr2':fields.Integer,
    'hc':fields.Boolean,
    'etat':fields.String,
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
        self.reqparse.add_argument('points_init', type = int, location = 'json')
        self.reqparse.add_argument('temps_init', type = int, location = 'json')
        self.reqparse.add_argument('points_barr', type = int, location = 'json')
        self.reqparse.add_argument('temps_barr', type = int, location = 'json')
        self.reqparse.add_argument('points_barr2', type = int, location = 'json')
        self.reqparse.add_argument('temps_barr2', type = int, location = 'json')
        self.reqparse.add_argument('hc', type =bool, location = 'json')
        self.reqparse.add_argument('etat', type =str, location = 'json')
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
                'points_barr': pa.points_barr,
                'temps_barr':pa.temps_barr,
                'points_barr2': pa.points_barr2,
                'temps_barr2':pa.temps_barr2,
                'hc':pa.hc,
                'etat':pa.etat,
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
            ,points_init=args['points_init'],temps_init=args['temps_init'],points_barr=args['points_barr'],temps_barr=args['temps_barr']\
            ,points_barr2=args['points_barr2'],temps_barr2=args['temps_barr2'],hc=args['hc'],etat=args['etat'],serie=args['serie']\
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
                'points_barr': pa.points_barr,
                'temps_barr':pa.temps_barr,
                'points_barr2': pa.points_barr2,
                'temps_barr2':pa.temps_barr2,
                'hc':pa.hc,
                'etat':pa.etat,
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
        self.reqparse.add_argument('points_init', type = int, location = 'json')
        self.reqparse.add_argument('temps_init', type = int, location = 'json')
        self.reqparse.add_argument('points_barr', type = int, location = 'json')
        self.reqparse.add_argument('temps_barr', type = int, location = 'json')
        self.reqparse.add_argument('points_barr2', type = int, location = 'json')
        self.reqparse.add_argument('temps_barr2', type = int, location = 'json')
        self.reqparse.add_argument('hc', type =bool, location = 'json')
        self.reqparse.add_argument('etat', type =str, location = 'json')
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
            'points_barr': pa.points_barr,
            'temps_barr':pa.temps_barr,
            'points_barr2': pa.points_barr2,
            'temps_barr2':pa.temps_barr2,
            'hc':pa.hc,
            'etat':pa.etat,
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
            'points_barr': args['points_barr'],
            'temps_barr':args['temps_barr'],
            'points_barr2': args['points_barr2'],
            'temps_barr2':args['temps_barr2'],
            'hc':args['hc'],
            'etat':args['etat'],
            'serie':args['serie'],
            'id_epreuve': args['id_epreuve']
            }
        print part
        tt = db.session.query(Participant).filter_by(id_epreuve=id).update({"num_depart":args['num_depart'],"nom_monture":args['nom_monture'],"nom_cavalier":args['nom_cavalier']\
            ,"points_init":args['points_init'],"temps_init":args['temps_init'],"points_barr":args['points_barr'],"temps_barr":args['temps_barr']\
            ,"points_barr2":args['points_barr2'],"temps_barr2":args['temps_barr2'],"hc":args['hc'],"etat":args['etat'],"serie":args['serie']\
            ,"id_epreuve":args['id_epreuve']})

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
        self.reqparse.add_argument('code',type=str,location='json')
        super(Bareme, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        a = Baremes.doBaremes(args['code'])
        return {'participants': map(lambda t: marshal(t, participant_fields_rang), a)}

api.add_resource(Config, app.config['REST_PATH']+'config', endpoint='config')
api.add_resource(Compet,app.config['REST_PATH']+'new_compet',endpoint='compet')
api.add_resource(EpreuveList,app.config['REST_PATH']+'epreuves',endpoint='epreuves')
api.add_resource(EpreuveSingle,app.config['REST_PATH']+'epreuves/<int:id>',endpoint='epreuve')
api.add_resource(ParticipantList,app.config['REST_PATH']+'participants/<int:id_epreuve>',endpoint='participants')
api.add_resource(ParticipantSingle,app.config['REST_PATH']+'participant/<int:id>',endpoint='participant')
api.add_resource(BaremesList,app.config['REST_PATH']+'baremes',endpoint='baremes')
api.add_resource(Bareme,app.config['REST_PATH']+'bareme',endpoint='bareme')