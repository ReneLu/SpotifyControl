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

    spotifyObject = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self) -> None:
        self.spotifyObject = self.plugin_base.backend.get_spotify_object()
        if self.get_shuffle_mode():
            log.debug("Shuffle mode is ON")
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-100.png")
        else:
            log.debug("Shuffle mode is OFF")
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-off-100.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        if self.get_shuffle_mode():
            log.debug("Shuffle mode is ON")
            self.spotifyObject.shuffle(False)
        else:
            log.debug("Shuffle mode is OFF")
            self.spotifyObject.shuffle(True)

    def get_shuffle_mode(self) -> bool:
        """
        Get the current shuffle mode
        """
        curPlayback = self.spotifyObject.current_playback()
        return curPlayback['shuffle_state']