__author__ = 'chassotce'
DATABASE_NAME = 'db.sqlite'
DATABASE_LOCATION = 'app/'+DATABASE_NAME
SQLALCHEMY_DATABASE_URI= 'sqlite:///'+DATABASE_NAME
SQLALCHEMY_COMMIT_ON_TEARDOWN= True
CONFIG_FILE = 'app/config.json'
BACKUP_DIR = 'app'
REST_PATH = '/course/api/v1.0/'