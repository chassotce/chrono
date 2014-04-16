from app import app,pluginloader
__author__ = 'chassotce'

print('youyou')
for i in pluginloader.getPlugins():
    print("Loading plugin " + i["name"])
    plugin = pluginloader.loadPlugin(i)
    plugin.run()

if __name__ == '__main__':
    app.run(debug=True)