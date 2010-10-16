import GstHandler
from pithos.pandora import *

class GlobalsManager:
    pandoraObj = Pandora()
    player = GstHandler.GstHandler()

    def getPandoraObj(self):
        return self.pandoraObj

    def resetPandoraObj(self):
        self.pandoraObj = Pandora()

    def getPlayer(self):
        return self.player

    getPandoraObj = classmethod(getPandoraObj)
    resetPandoraObj = classmethod(resetPandoraObj)
    getPlayer = classmethod(getPlayer)
