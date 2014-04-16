import imp
import os

PluginFolder = "app/baremes"
MainModule = "__init__"

def getPlugins():
    plugins = []
    possibleplugins = os.listdir(PluginFolder)
    print possibleplugins
    for i in possibleplugins:
        location = os.path.join(PluginFolder, i)
        #print location
        #print i
        #print os.path.isdir(location)
        if not os.path.isdir(location) or not MainModule + ".py" in os.listdir(location):
            continue
        info = imp.find_module(MainModule, [location])
        #print info
        plugins.append({"name": i, "info": info})
        #print plugins
        l =  imp.load_module(MainModule,*info)
        #print l.code()
    return plugins

def loadPlugin(plugin):
    return imp.load_module(MainModule, *plugin["info"])