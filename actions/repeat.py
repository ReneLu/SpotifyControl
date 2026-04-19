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

class RepeatAction(ActionBase):

    actionNameStart = "repeat"
    actionName = "repeat"
    backend = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend
        self.has_configuration = True
        self.actionName = self.actionName + "_" + str(self.input_ident.json_identifier) + "_" + self.page.get_name().replace(" ", "_")
        self.actionSettings = ActionSettings(self.actionName, self.backend)
        self.Texts = Texts

    def on_ready(self) -> None:
        self.actionSettings.set_settings_defaults()
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
            repeat_state = self.backend.get_current_repeat_state()
            if repeat_state == "off":
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-off-100.png")
            elif repeat_state == "context":
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-100.png")
            elif repeat_state == "track":
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-1-100.png")
            else:
                icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-repeat-no-music-100.png")

            btn_img = self.actionSettings.get_media(self.deck_controller.deck.key_image_format()["size"], icon_path=icon_path)
            if btn_img is not None:
                self.set_media(image=btn_img)
            else:
                self.set_media(None)

    def on_key_down(self) -> None:
        if self.backend.is_authed():
            repeat_state = self.backend.get_current_repeat_state()
            settings = self.actionSettings.get_settings()
            selected_device = settings["device_id_" + self.actionName]
            if repeat_state == "off":
                self.backend.repeat("context", selected_device)
            elif repeat_state == "context":
                self.backend.repeat("track", selected_device)
            elif repeat_state == "track":
                self.backend.repeat("off", selected_device)

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