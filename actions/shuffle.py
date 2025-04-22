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

    def on_ready(self) -> None:
        if self.backend.is_authed():
            if self.backend.get_shuffle_mode():
                log.info("Shuffle mode is ON")
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-100.png")
            else:
                log.info("Shuffle mode is OFF")
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-off-100.png")
            self.set_media(media_path=icon_path, size=0.75)
        else:
            log.info("Spotify is not authenticated")
            self.set_center_label("Not Authenticated")

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        log.info("Toggle Shuffle mode")
        if self.backend.is_authed():
            self.backend.shuffle(not self.get_shuffle_mode())
        else:
            log.info("Spotify is not authenticated")
            self.set_center_label("Not Authenticated")
