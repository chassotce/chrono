from app import app,pluginloader
__author__ = 'chassotce'

print('youyou')
plugins = pluginloader.getPlugins()
for i in plugins:
    print("Loading plugin " + i["name"])
    #print i["info"]
    print i
    plugin = pluginloader.loadPlugin(i)
    plugin.run()
    print i['name']
    #print(plugin.code())

print plugins
a = next((element for element in plugins if element['name'] == 'AAvecCrono'),None)
#print a[0]
#a= a[0]
print a
if a!=None:
    b = pluginloader.loadPlugin(a)
    b.run()

if __name__ == '__main__':
    app.run(debug=True)