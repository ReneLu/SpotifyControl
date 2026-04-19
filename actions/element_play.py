# Import StreamController modules
from enum import Enum

import settings
from src.backend.PluginManager.ActionBase import ActionBase

# Import action_settings.py from the same folder
from .action_settings import ActionSettings, TextOptions, Texts

# Import python modules
import os

# Import gtk modules - used for the config rows
import globals as gl
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.Signals import Signals
from GtkHelper.GtkHelper import ComboRow

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger as log

class ElementNameRows(Enum):
    NONE = "None"
    TOP = "Top"
    MIDDLE = "Middle"
    BOTTOM = "Bottom"

class ElementPlayAction(ActionBase):

    actionNameStart = "element_play"
    actionName = ""
    backend = None

    element_name_row_texts = {
        ElementNameRows.NONE: "None",
        ElementNameRows.TOP: "Top",
        ElementNameRows.MIDDLE: "Middle",
        ElementNameRows.BOTTOM: "Bottom"
    }

    uri_info: dict[str, str] = { "uri":"", "type": "", "id": "" }
    element_cover_path = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend
        self.has_configuration = True
        self.actionName = self.actionNameStart + "_" + str(self.input_ident.json_identifier) + "_" + self.page.get_name().replace(" ", "_")
        self.actionSettings = ActionSettings(self.actionName, self.backend)
        self.Texts = Texts

        self.connect(signal=Signals.PageRename, callback=self.on_page_rename)

    def on_ready(self) -> None:
        settings = self.actionSettings.get_settings()
        if "element_url_" + self.actionName in settings and settings["element_url_" + self.actionName] != "":
            url = settings["element_url_" + self.actionName]
            uri_info = self.backend.get_uri_from_url(url)
            if self.is_uri_valid_type(uri_info):
                self.uri_info = uri_info
            else:
                log.error(f"Invalid Spotify URL in settings: {url}")
                self.uri_info = { "uri":"", "type": "", "id": "" }

        self.actionSettings.set_settings_defaults()
        self.set_settings_defaults()
        self.on_tick()

    def on_tick(self) -> None:
        if self.backend is None:
            log.error("Spotify backend is not available")
            return
        if not self.backend.is_authed():
            icon_path = os.path.join(self.plugin_base.PATH, "assets", "icons8-spotify-no-auth-100.png")
            self.set_media(media_path=icon_path, size=0.75)
        else:
            settings = self.actionSettings.get_settings()
            if "element_name_" + self.actionName in settings and settings["element_name_" + self.actionName] != "":
                if settings["element_name_row_" + self.actionName] == ElementNameRows.TOP.value and settings["element_name_" + self.actionName] != "":
                    self.set_top_label(settings["element_name_" + self.actionName])
                else:
                    self.set_top_label(self.actionSettings.get_text(self.Texts.TOP))

                if settings["element_name_row_" + self.actionName] == ElementNameRows.MIDDLE.value and settings["element_name_" + self.actionName] != "":
                    self.set_center_label(settings["element_name_" + self.actionName])
                else:
                    self.set_center_label(self.actionSettings.get_text(self.Texts.MIDDLE))

                if settings["element_name_row_" + self.actionName] == ElementNameRows.BOTTOM.value and settings["element_name_" + self.actionName] != "":
                    self.set_bottom_label(settings["element_name_" + self.actionName])
                else:
                    self.set_bottom_label(self.actionSettings.get_text(self.Texts.BOTTOM))

            else:
                self.set_top_label(self.actionSettings.get_text(self.Texts.TOP))
                self.set_center_label(self.actionSettings.get_text(self.Texts.MIDDLE))
                self.set_bottom_label(self.actionSettings.get_text(self.Texts.BOTTOM))

            self.element_cover_path = self.backend.get_element_cover_path(self.uri_info["id"], self.uri_info["type"])
            if self.element_cover_path != "":
                self.set_media(media_path=self.element_cover_path)
            else:
                self.set_media(None)

    def on_key_down(self) -> None:
        # Start playback on the selected device when nothing is currently playing
        if self.backend.is_authed():
            settings = self.actionSettings.get_settings()
            selected_device = settings["device_id_" + self.actionName]

            if self.uri_info["uri"] is None:
                log.error(f"Invalid Spotify URI: {self.uri_info}")
                return
            self.backend.play(selected_device, context_uri=self.uri_info["uri"])

    def get_config_rows(self) -> list:
        if self.backend.is_authed():
            rows = self.actionSettings.get_config_rows()
            rows.remove(self.actionSettings.get_show_icon_element()) # Remove the show icon row from the config, since it doesn't make sense for the element play action
            rows.remove(self.actionSettings.get_show_album_cover_element()) # Remove the show album cover row from the config, since it doesn't make sense for the element play action

            # Add text input for the Spotify element URL
            self.element_url = Adw.EntryRow(title=self.plugin_base.lm.get("actions.element_play.config.element_url"),
                                            input_purpose=Gtk.InputPurpose.URL)
            self.element_url.connect("notify::text", self.on_element_url_changed)

            rows.append(self.element_url)

            # Create Element Name Row Selector Element
            self.element_row_model = Gtk.ListStore.new([str, str])
            self.element_row_select = ComboRow(model=self.element_row_model,
                                            title="Show Name on Row")

            self.element_row_renderer = Gtk.CellRendererText()
            self.element_row_select.combo_box.pack_start(self.element_row_renderer, True)
            self.element_row_select.combo_box.add_attribute(self.element_row_renderer, "text", 0)

            self.element_row_select.combo_box.connect("changed", self.on_element_row_select)
            rows.append(self.element_row_select)

            # Set settings defaults
            self.set_settings_defaults()

            # Update the text input with the current setting value
            settings = self.actionSettings.get_settings()
            self.element_url.set_text(settings["element_url_" + self.actionName])
            self.actionSettings.set_settings(settings)

            self.update_element_text_row_selector()

            return rows
        else:
            self.not_authed_label = Gtk.Label(label=self.plugin_base.lm.get("actions.base.not-authed"))
            return [self.not_authed_label]

    def set_settings_defaults(self):
        settings = self.actionSettings.get_settings()
        if "element_url_" + self.actionName not in settings:
            settings["element_url_" + self.actionName] = ""
        if "element_name_row_" + self.actionName not in settings:
            settings["element_name_row_" + self.actionName] = ElementNameRows.NONE.value
        if "element_name_" + self.actionName not in settings:
            settings["element_name_" + self.actionName] = ""
        self.actionSettings.set_settings(settings)

    def update_element_text_row_selector(self):
        """
        Update the element text row selector with the available options
        """

        settings = self.actionSettings.get_settings()

        # Clear the model and add the options
        self.element_row_model.clear()
        for option in ElementNameRows:
            self.element_row_model.append([self.element_name_row_texts[option], option.value])

        # Set index of combo box to last selected option
        if settings["element_name_row_" + self.actionName] is not None:
            position = 0
            for elem in self.element_row_model:
                if elem[1] == settings["element_name_row_" + self.actionName]:
                    self.element_row_select.combo_box.set_active(position)
                    return
                position += 1

        # If no valid option found select the first one and set it in the settings
        self.element_row_select.combo_box.set_active(0)
        settings["element_name_row_" + self.actionName] = self.element_name_row_texts[ElementNameRows.NONE]
        self.actionSettings.set_settings(settings)

    def on_element_url_changed(self, entry, text) -> None:
        url = entry.get_text()
        settings = self.actionSettings.get_settings()

        if url != "":
            # Remove old cover from cache
            self.backend.remove_element_cover_from_cache(self.uri_info["id"])
            uri_info = self.backend.get_uri_from_url(url)
            if not self.is_uri_valid_type(uri_info):
                log.error(f"Invalid Spotify URL: {url}")
                settings["element_url_" + self.actionName] = ""
                self.actionSettings.set_settings(settings)
                entry.set_text("")
                return
            self.uri_info = uri_info

            self.element_cover_path = self.backend.get_element_cover_path(self.uri_info["id"], self.uri_info["type"])
            if self.element_cover_path != "":
                self.set_media(media_path=self.element_cover_path)
            else:
                self.set_media(None)

            element_name = self.backend.get_element_name(self.uri_info["id"], self.uri_info["type"])

            settings["element_name_" + self.actionName] = element_name
            settings["element_url_" + self.actionName] = url
        else:
            self.uri_info = { "uri":"", "type": "", "id": "" }
            settings["element_url_" + self.actionName] = ""
            settings["element_name_" + self.actionName] = ""

        self.actionSettings.set_settings(settings)

    def is_uri_valid_type(self, uri_info: dict[str, str]) -> bool:
        if uri_info["uri"] is None or uri_info["type"] is None or uri_info["id"] is None or \
           (uri_info["type"] != "album" and uri_info["type"] != "playlist" and uri_info["type"] != "artist"):
            return False
        return True

    def on_element_row_select(self, combo):
        settings = self.actionSettings.get_settings()
        settings["element_name_row_" + self.actionName] = self.element_row_model[combo.get_active()][1]
        self.actionSettings.set_settings(settings)

    def on_page_rename(self, old_name, new_name):
        if old_name == self.page.get_name():
            old_action_name = self.actionName
            self.actionName = self.actionNameStart + "_" + str(self.input_ident.json_identifier) + "_" + new_name.replace(" ", "_")
            self.actionSettings.rename_setting(old_action_name, self.actionName)

    def on_remove(self) -> None:
        self.backend.remove_element_cover_from_cache(self.uri_info["id"])
        self.actionSettings.remove_setting(self.actionName)