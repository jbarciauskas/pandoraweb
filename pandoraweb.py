import web
import logging
import logging.config
import gobject, glib
import threading
import json
import datetime

from web import form
from pithos.pandora import PandoraError
from pithos.pandora import Pandora
from GlobalsManager import GlobalsManager

logging.config.fileConfig("logging.conf")

render = web.template.render('templates/')
urls = (
        '/', 'index',
        '/status', 'status',
        '/login', 'login',
        '/play/(.*)', 'play',
        '/skip', 'skip',
        '/logout', 'logout',
        )
app = web.application(urls, globals())

def redirectWhenNotLoggedIn():
    if not GlobalsManager.getPandoraObj().stations and not web.ctx.path == '/login' and not web.ctx.path == 'favicon.ico':
        raise web.seeother('/login')

app.add_processor(web.loadhook(redirectWhenNotLoggedIn))

LoginForm = form.Form(
        form.Textbox("username", form.notnull),
        form.Password('password', form.notnull),
        form.Button('Login'))

class login:
    def GET(self):
        loginForm = LoginForm()
        return render.loginTemplate(loginForm)

    def POST(self):
        loginForm = LoginForm()
        if not loginForm.validates():
            return self.onBadLogin(loginForm)
        else:
            try:
                GlobalsManager.getPandoraObj().connect(loginForm.d.username, loginForm.d.password)
                raise web.seeother('/')
            except PandoraError:
                self.onBadLogin(loginForm)

    def onBadLogin(self, loginForm):
        return render.loginTemplate(loginForm);

class index:
    def GET(self):
        raise web.seeother('/play/')

class status:
    def GET(self):
        return json.dumps(GlobalsManager.getPlayer().getCurrentSong())

class play:
    def GET(self, stationId):
        if stationId:
            GlobalsManager.getPlayer().playStation(GlobalsManager.getPandoraObj().get_station_by_id(stationId))

        return render.nowPlaying(GlobalsManager.getPandoraObj().stations, GlobalsManager.getPlayer().getCurrentSong())

class skip:
    def GET(self):
        GlobalsManager.getPlayer().nextSong()
        raise web.seeother('/play/')

class logout:
    def GET(self):
        GlobalsManager.getPlayer().stop()
        GlobalsManager.resetPandoraObj()
        raise web.seeother('/login')

if __name__=="__main__":
    web.internalerror = web.debugerror
    gobject.threads_init()
    loop = glib.MainLoop()
    dbusThread = threading.Thread(target=loop.run)
    dbusThread.daemon = True
    dbusThread.start()
    app.run()
