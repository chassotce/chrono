from app import app
__author__ = 'chassotce'
from werkzeug.contrib.fixers import ProxyFix



app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    app.run()