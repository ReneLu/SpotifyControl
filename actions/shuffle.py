# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger as log

class ShuffleAction(ActionBase):

    backend = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend

    def on_tick(self) -> None:
        if not self.backend.is_authed():
            #log.info("Spotify is not authenticated")
            self.set_media(media_path="")
            self.set_top_label("Spotify")
            self.set_center_label("Not")
            self.set_bottom_label("Authed")
        else:
            #log.info("Spotify is authenticated")
            if self.backend.get_shuffle_mode() == True:
                #log.info("Shuffle mode is ON")
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-100.png")
                self.set_top_label("")
                self.set_center_label("")
                self.set_bottom_label("")
            elif self.backend.get_shuffle_mode() == False:
                #log.info("Shuffle mode is OFF")
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-off-100.png")
                self.set_top_label("")
                self.set_center_label("")
                self.set_bottom_label("")
            else:
                #log.info("Shuffle mode is None")
                self.set_top_label("Shuffle")
                self.set_center_label("No Music")
                self.set_bottom_label("Playing")
                icon_path = ""
            self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        log.info("Toggle Shuffle mode")
        if self.backend.is_authed():
            if self.backend.get_shuffle_mode():
                log.info("Shuffle mode to Off")
                self.backend.shuffle(False)
            else:
                log.info("Shuffle mode to On")
                self.backend.shuffle(True)
