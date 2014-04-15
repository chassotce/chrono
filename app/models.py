__author__ = 'chassotce'
from app import db,api,app
from flask_restful import Resource, marshal, abort,reqparse,fields
import json
from json import load
from flask import jsonify
import sqlitebck,sqlite3,datetime

class Epreuve(db.Model):
    __tablename_ = 'epreuve'
    id_epreuve = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(32),unique=True)
    bareme_code = db.Column(db.Integer)
    temps_accorde = db.Column(db.Integer)
    nb_serie = db.Column(db.Integer)

class Participant(db.Model):
    __tablename__ = 'participant'
    id_participant = db.Column(db.Integer, primary_key=True)
    num_depart = db.Column(db.Integer,index=True)
    nom_monture = db.Column(db.String(32))
    nom_cavalier = db.Column(db.String(32))
    points_init = db.Column(db.Integer,index=True)
    temps_init = db.Column(db.Time())
    points_barr = db.Column(db.Integer,index=True)
    temps_barr = db.Column(db.Time())
    points_barr2 = db.Column(db.Integer,index=True)
    temps_barr2 = db.Column(db.Time())
    hc = db.Column(db.Boolean())
    etat = db.Column(db.Enum("undef", "elimine", "abandon"))
    serie = db.Column(db.Integer)
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
            data['tmp_charge_chrono'] = args['tmp_charge_chrono']
            data['tmp_aff_temps'] = args['tmp_aff_temps']
            data['tmp_aff_class'] = args['tmp_aff_class']
            configfile.seek(0)
            json.dump(data, configfile, indent=4)
            configfile.truncate()
        configfile.close()
        return {'config':marshal(data, config_fields)}

    def options(self):
        return {'Allow' : 'GET,PUT' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'PUT,GET' }

class Compet(Resource):
    def get(self):
        print app.config['DATABASE_NAME']
        conn = sqlite3.connect(app.config['DATABASE_LOCATION'])
        backupname = app.config['BACKUP_DIR']+'/'+datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
        conn2 = sqlite3.connect(backupname)
        sqlitebck.copy(conn, conn2)
        conn.close()
        conn2.close()
        db.create_all()
        return {'success':'true'}

    def options(self):
        return {'Allow' : 'GET' }, 200,{ 'Access-Control-Allow-Origin': '*','Access-Control-Allow-Methods' : 'GET' }

epreuve_fields = {
    'nom': fields.String,
    'bareme_code': fields.Integer,
    'temps_accorde': fields.Integer,
    'nb_serie': fields.Integer,
    'uri': fields.Url('epreuve')
}

epreuves = []

class EpreuveList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('nom', type = str, location = 'json')
        self.reqparse.add_argument('bareme_code', type = int, location = 'json')
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

api.add_resource(Config, '/course/api/v1.0/config', endpoint='config')
api.add_resource(Compet,'/course/api/v1.0/new_compet',endpoint='compet')
api.add_resource(EpreuveList,'/course/api/v1.0/epreuves',endpoint='epreuves')
api.add_resource(EpreuveSingle,'/course/api/v1.0/epreuves/<int:id>',endpoint='epreuve')