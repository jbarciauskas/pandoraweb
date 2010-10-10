import web
from web import form
from pithos.pandora import *
render = web.template.render('templates/')

urls = ('/', 'index')
app = web.application(urls, globals())
app.pandoraObj = None

LoginForm = form.Form(
    form.Textbox("username"),
    form.Password('password'),
    form.Button('Login'))

class index:
    def GET(self):
        loginForm = LoginForm()
        # make sure you create a copy of the form by calling it (line above)
        # Otherwise changes will appear globally
        return render.loginTemplate(loginForm)

    def POST(self): 
        loginForm = LoginForm() 
        if not loginForm.validates(): 
            return onBadLogin(loginForm)
        else:
            try:
                pandoraObj = Pandora()
                pandoraObj.connect(loginForm.d.username, loginForm.d.password)
                return render.stationList(pandoraObj.stations)
            except PandoraError:
                onBadLogin(loginForm)

    def onBadLogin(self, loginForm):
        return render.loginTemplate(loginForm);

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
