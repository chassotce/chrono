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
    def multikeysort(items, columns):
        from operator import itemgetter
        comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]
        def comparer(left, right):
            for fn, mult in comparers:
                result = cmp(fn(left), fn(right))
                if result:
                    return mult * result
            else:
                return 0
        return sorted(items, cmp=comparer)

    @staticmethod
    def getBaremes():
        return getAllBaremes()

    @staticmethod
    def doBaremes(code):
        a = next((element for element in pluginloader.getPlugins() if element['name'] == code),None)
        print a
        z = {}
        if a !=None:
            plugin = pluginloader.loadPlugin(a)
            z = plugin.classement(app.config['CURRENT_EPREUVE_ID'])
        return z