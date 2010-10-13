import web
import logging
import gst
from web import form
from pithos.pandora import *
render = web.template.render('templates/')

urls = (
        '/', 'index',
        '/play/(.*)', 'play',
        '/skip', 'skip',
        )
app = web.application(urls, globals())
app.pandoraObj = Pandora()
app.player = None

LoginForm = form.Form(
        form.Textbox("username"),
        form.Password('password'),
        form.Button('Login'))

class index:
    def GET(self):
        if app.pandoraObj.stations:
            return render.stationList(app.pandoraObj.stations)
        else:
            loginForm = LoginForm()
            return render.loginTemplate(loginForm)

    def POST(self):
        loginForm = LoginForm()
        if not loginForm.validates():
            return self.onBadLogin(loginForm)
        else:
            try:
                app.pandoraObj = Pandora()
                app.pandoraObj.connect(loginForm.d.username, loginForm.d.password)
                return render.stationList(app.pandoraObj.stations)
            except PandoraError:
                self.onBadLogin(loginForm)

    def onBadLogin(self, loginForm):
        return render.loginTemplate(loginForm);

class play:
    def GET(self, stationId):
        if not app.player:
            app.player = GstHandler()
        app.player.playStation(app.pandoraObj.get_station_by_id(stationId))
        return render.nowPlaying(app.pandoraObj.stations, app.player.currentSong())

class skip:
    def GET(self):
        app.player.nextSong()
        return render.nowPlaying(app.pandoraObj.stations, app.player.currentSong())

class GstHandler:
    def __init__(self):
        self.player = gst.element_factory_make("playbin", "player")
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.onMessage)

        self.time_format = gst.Format(gst.FORMAT_TIME)
        self.bufferPercent = None
        self.currentSongIndex = 0
        self.playing = False
        self.station = None
        self.playcount = 0

    def playStation(self, station):
        if not self.station or station.id != self.station.id:
            self.station = station
            self.playlist = station.get_playlist()
            self.nextSong()

    def currentSong(self):
        if self.currentSongIndex is not None:
            testvar = self.playlist
            return self.playlist[self.currentSongIndex]
        return None

    def startSong(self, song_index):
        prev = self.currentSong()
        self.stop()
        self.currentSongIndex = song_index
        if not self.currentSong().is_still_valid():
            self.currentSong().message = "Playlist expired"
            return self.nextSong()
        if self.currentSong().tired or self.currentSong().rating == RATE_BAN:
            return self.nextSong()
        logging.info("Starting song: index = %i"%(song_index))
        self.buffer_percent = 100
        self.player.set_property("uri", self.currentSong().audioUrl)
        self.play()
        self.playcount += 1

    def nextSong(self):
        if self.checkForEndOfPlaylist():
            self.startSong(0)
        else:
            self.startSong(self.currentSongIndex + 1)

    def checkForEndOfPlaylist(self):
        songs_remaining = len(self.playlist) - self.currentSongIndex
        if not self.currentSong() or songs_remaining <= 0:
            self.playlist = self.station.get_playlist()
            return True
        return False

    def play(self):
        if not self.playing:
            self.playing = True
            self.player.set_state(gst.STATE_PLAYING)

    def stop(self):
        prev = self.currentSong()
        if prev and prev.start_time:
            prev.finished = True
            try:
                prev.duration = self.player.query_duration(self.time_format, None)[0] / 1000000000
                prev.position = self.player.query_position(self.time_format, None)[0] / 1000000000
            except gst.QueryError:
                prev.duration = prev.position = None

        self.playing = False
        self.player.set_state(gst.STATE_NULL)

    def onMessage(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.nextSong()
        elif message.type == gst.MESSAGE_BUFFERING:
            percent = message.parse_buffering()
            self.buffer_percent = percent
            if percent < 100:
                self.player.set_state(gst.STATE_PAUSED)
            elif self.playing:
                self.player.set_state(gst.STATE_PLAYING)
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            logging.error("Gstreamer error: %s, %s" % (err, debug))
            self.currentSong().message = "Error: "+str(err)
            self.gstreamer_error = str(err)
            self.gstreamer_errorcount_1 += 1
            self.nextSong()

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
