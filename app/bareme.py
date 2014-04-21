from app.models import participant_fields_rang,marshal
from app import app

__author__ = 'chassotce'
import pluginloader

baremes = []
def getAllBaremes():
    baremes = []
    l = pluginloader.getPlugins()
    for b in l:
        p = pluginloader.loadPlugin(b)
        baremes.append({'code': b["name"],'desc':p.getDesc()})
    return baremes

class Baremes:
    @staticmethod
    def getBaremes():
        return getAllBaremes()

    @staticmethod
    def doBaremes(code):
        a = next((element for element in pluginloader.getPlugins() if element['name'] == code),None)
        z = {}
        if a !=None:
            plugin = pluginloader.loadPlugin(a)
            z = plugin.classement(app.config['CURRENT_EPREUVE_ID'])
        return z