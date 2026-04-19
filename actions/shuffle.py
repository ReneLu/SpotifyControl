# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase

# Import action_settings.py from the same folder
from .action_settings import ActionSettings, Texts

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from loguru import logger as log

class ShuffleAction(ActionBase):

    actionName = "shuffle"
    backend = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend
        self.has_configuration = True
        self.actionName = self.actionName + "_" + str(self.input_ident.json_identifier) + "_" + self.page.get_name().replace(" ", "_")
        self.actionSettings = ActionSettings(self.actionName, self.backend)
        self.Texts = Texts

        self.has_configuration = True

    def on_ready(self) -> None:
        self.actionSettings.set_settings_defaults()
        self.on_tick()

    def on_ready(self) -> None:
        self.on_tick()

    def on_tick(self) -> None:
        if self.backend is None:
            log.error("Spotify backend is not available")
            return
        if not self.backend.is_authed():
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-spotify-no-auth-100.png")
            self.set_media(media_path=icon_path, size=0.75)
        else:
            self.set_top_label(self.actionSettings.get_text(self.Texts.TOP))
            self.set_center_label(self.actionSettings.get_text(self.Texts.MIDDLE))
            self.set_bottom_label(self.actionSettings.get_text(self.Texts.BOTTOM))

            icon_path = ""
            shuffle_mode = self.backend.get_shuffle_mode()
            if shuffle_mode == True:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-100.png")
            elif shuffle_mode == False:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-off-100.png")
            else:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-shuffle-no-music-100.png")

            btn_img = self.actionSettings.get_media(self.deck_controller.deck.key_image_format()["size"], icon_path=icon_path)
            if btn_img is not None:
                self.set_media(image=btn_img)
            else:
                self.set_media(None)

    def on_key_down(self) -> None:
        # Toggle shuffle mode
        if self.backend.is_authed():
            shuffle_mode = self.backend.get_shuffle_mode()
            if shuffle_mode == True:
                self.backend.shuffle(False)
            else:
                self.backend.shuffle(True)

    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            return self.actionSettings.get_config_rows()
        else:
            self.not_authed_label = Gtk.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
            return [self.not_authed_label]

    def on_page_rename(self, old_name, new_name):
        if old_name == self.page.get_name():
            old_action_name = self.actionName
            self.actionName = self.actionNameStart + "_" + str(self.input_ident.json_identifier) + "_" + new_name.replace(" ", "_")
            self.actionSettings.rename_setting(old_action_name, self.actionName)

    def on_remove(self) -> None:
        self.actionSettings.remove_setting(self.actionName)