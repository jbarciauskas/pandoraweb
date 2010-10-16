import web
import logging
from web import form
from pithos.pandora import PandoraError
from pithos.pandora import Pandora
from GlobalsManager import GlobalsManager

render = web.template.render('templates/')
urls = (
        '/', 'index',
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
        return render.stationList(GlobalsManager.getPandoraObj().stations)

class play:
    def GET(self, stationId):
        GlobalsManager.getPlayer().playStation(GlobalsManager.getPandoraObj().get_station_by_id(stationId))
        return render.nowPlaying(GlobalsManager.getPandoraObj().stations, GlobalsManager.getPlayer().currentSong())

class skip:
    def GET(self):
        GlobalsManager.getPlayer().nextSong()
        return render.nowPlaying(GlobalsManager.getPandoraObj().stations, GlobalsManager.getPlayer().currentSong())

class logout:
    def GET(self):
        GlobalsManager.getPlayer().stop()
        GlobalsManager.resetPandoraObj()
        raise web.seeother('/login')

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
