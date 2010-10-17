import gst
import logging
import datetime
from pithos.pandora import *


class GstHandler:

    def __init__(self):
        self.player = gst.element_factory_make("playbin2", "player")
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.onMessage)

        self.time_format = gst.Format(gst.FORMAT_TIME)
        self.currentSong = None
        self.playlist = None
        self.playing = False
        self.station = None

    def playStation(self, station):
        if not self.station or station.id != self.station.id:
            self.station = station
            self.playlist = Playlist(station)
            self.nextSong()

    def nextSong(self):
        logging.info('Changing songs')
        prev = self.playlist.currentSong
        self.stop()
        self.currentSong = self.playlist.getNextSong()
        if not self.currentSong.is_still_valid():
            return self.nextSong()
        if self.currentSong.tired or self.currentSong.rating == RATE_BAN:
            return self.nextSong()
        self.player.set_property("uri", self.currentSong.audioUrl)
        self.play()

    def getCurrentSong(self):
        if self.currentSong:
            songDict = self.currentSong.getDict()
            songDict['duration'] = self.getDuration()
            songDict['position'] = self.getPosition()
            return songDict
        else:
            return None

    def play(self):
        if not self.playing:
            logging.info('Starting to play ' + self.currentSong.title)
            self.playing = True
            self.player.set_state(gst.STATE_PLAYING)

    def stop(self):
        prev = self.currentSong
        if prev and prev.start_time:
            prev.finished = True
            try:
                prev.duration = self.getDuration()
                prev.position = self.getPosition()
            except gst.QueryError:
                prev.duration = prev.position = None

        self.playing = False
        self.player.set_state(gst.STATE_NULL)

    def getDuration(self):
        try:
            return self.player.query_duration(self.time_format, None)[0] / 1000000000
        except gst.QueryError:
            return 0

    def getPosition(self):
        try:
            return self.player.query_position(self.time_format, None)[0] / 1000000000
        except gst.QueryError:
            return 0

    def onMessage(self, bus, message):
        t = message.type
        logging.debug('Received message ' + str(t))
        if t == gst.MESSAGE_EOS:
            self.nextSong()
        elif message.type == gst.MESSAGE_BUFFERING:
            percent = message.parse_buffering()
            if percent < 100:
                self.player.set_state(gst.STATE_PAUSED)
            elif self.playing:
                self.player.set_state(gst.STATE_PLAYING)
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            logging.error("Gstreamer error: %s, %s" % (err, debug))
            self.gstreamer_error = str(err)
            self.gstreamer_errorcount_1 += 1
            self.nextSong()

