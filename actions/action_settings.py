from typing import Any

from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager.ActionBase import ActionBase

# Import python modules
import os
from enum import Enum
import json
from PIL import Image

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from loguru import logger as log

class TextOptions(Enum):
    NONE = "none"
    TRACK_NAME = "track_name"
    ARTIST_NAME = "artist_name"
    ALBUM_NAME = "album_name"
    DEVICE_NAME = "device_name"
    VOLUME = "volume"
    DURATION = "duration"
    ELA_TIME = "elapsed_time"
    REM_TIME = "remaining_time"

class Texts(Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"

VAR_APP_PATH = os.path.join(os.path.expanduser("~"), ".var", "app", "com.core447.StreamController")
DATA_PATH = os.path.join(VAR_APP_PATH, "data")

class ActionSettings(ActionBase):

    text_settings = {
        TextOptions.NONE: "",
        TextOptions.TRACK_NAME: "",
        TextOptions.ARTIST_NAME: "",
        TextOptions.ALBUM_NAME: "",
        TextOptions.DEVICE_NAME: "",
        TextOptions.VOLUME: "",
        TextOptions.DURATION: "",
        TextOptions.ELA_TIME: "",
        TextOptions.REM_TIME: ""
    }

    backend = None

    settings_path: str = ""

    def __init__(self, actionName: str, backend: Any) -> None:
        self.actionName = actionName
        self.backend = backend

        self.text_settings = {
            TextOptions.NONE: "None",
            TextOptions.TRACK_NAME: "Track Name",
            TextOptions.ARTIST_NAME: "Artist Name",
            TextOptions.ALBUM_NAME: "Album Name",
            TextOptions.DEVICE_NAME: "Device Name",
            TextOptions.VOLUME: "Volume",
            TextOptions.DURATION: "Duration",
            TextOptions.ELA_TIME: "Elapsed Time",
            TextOptions.REM_TIME: "Remaining Time"
        }

        self.settings_path = os.path.join(DATA_PATH, "settings", "plugins", "com_ReneLu_spotifyControl", "actionSettings.json")

    def get_settings(self):
        """
        Retrieves the settings from the settings file.

        Returns:
            dict: The settings stored in the settings file. If the settings file does not exist, an empty dictionary is returned.
        """
        if not os.path.exists(self.settings_path):
            return {}
        with open(self.settings_path, "r") as f:
            settings = json.load(f)

            if settings.get("file-version") == "2.0":
                # Is newest version, return settings
                return settings.get("settings", {})

            else:
                # Is the old format, convert it
                new_settings = {
                    "file-version": "2.0",
                    "settings": settings
                }
                with open(self.settings_path, "w") as f:
                    json.dump(new_settings, f, indent=4)

                return settings

    def set_settings(self, settings):
        """
        Saves the provided settings to the settings file.

        Args:
            settings (dict): The settings to be saved.

        Returns:
            None
        """
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)

        if not os.path.isfile(self.settings_path):
            with open(self.settings_path, "w") as f:
                json.dump({}, f)

        with open(self.settings_path, "r+") as f:
            content = json.load(f)

            new_content = content.copy()

            if content.get("file-version") == "2.0":
                new_content["settings"] = settings
            else:
                new_content = {
                    "file-version": "2.0",
                    "settings": settings
                }

            f.seek(0)
            json.dump(new_content, f, indent=4)
            f.truncate()

    def get_config_rows(self) -> list:
        rows = []

        # Create Device Selector Element
        self.devices_model = Gtk.ListStore.new([str, str])
        self.devices_select = ComboRow(model=self.devices_model,
                                        title="Select Device")

        self.device_selector_renderer = Gtk.CellRendererText()
        self.devices_select.combo_box.pack_start(self.device_selector_renderer, True)
        self.devices_select.combo_box.add_attribute(self.device_selector_renderer, "text", 0)

        self.devices_select.combo_box.connect("changed", self.on_device_select)
        rows.append(self.devices_select)

        # Create Top Row Text Selector Element
        self.Top_Text_model = Gtk.ListStore.new([str, str])
        self.Top_Text_select = ComboRow(model=self.Top_Text_model,
                                        title="Select Top Text")

        self.Top_Text_renderer = Gtk.CellRendererText()
        self.Top_Text_select.combo_box.pack_start(self.Top_Text_renderer, True)
        self.Top_Text_select.combo_box.add_attribute(self.Top_Text_renderer, "text", 0)

        self.Top_Text_select.combo_box.connect("changed", self.on_top_text_select)
        rows.append(self.Top_Text_select)

        # Create Middle Row Text Selector Element
        self.Middle_Text_model = Gtk.ListStore.new([str, str])
        self.Middle_Text_select = ComboRow(model=self.Middle_Text_model,
                                        title="Select Middle Text")

        self.Middle_Text_renderer = Gtk.CellRendererText()
        self.Middle_Text_select.combo_box.pack_start(self.Middle_Text_renderer, True)
        self.Middle_Text_select.combo_box.add_attribute(self.Middle_Text_renderer, "text", 0)

        self.Middle_Text_select.combo_box.connect("changed", self.on_middle_text_select)
        rows.append(self.Middle_Text_select)

        # Create Bottom Row Text Selector Element
        self.Bottom_Text_model = Gtk.ListStore.new([str, str])
        self.Bottom_Text_select = ComboRow(model=self.Bottom_Text_model,
                                        title="Select Bottom Text")

        self.Bottom_Text_renderer = Gtk.CellRendererText()
        self.Bottom_Text_select.combo_box.pack_start(self.Bottom_Text_renderer, True)
        self.Bottom_Text_select.combo_box.add_attribute(self.Bottom_Text_renderer, "text", 0)

        self.Bottom_Text_select.combo_box.connect("changed", self.on_bottom_text_select)
        rows.append(self.Bottom_Text_select)

        # Create Album Cover Toggle
        self.album_cover_toggle = Adw.SwitchRow(title="Show Album Cover")
        self.album_cover_toggle.connect("notify::active", self.on_toggle_album_cover)
        rows.append(self.album_cover_toggle)

        # Create Icon Toggle
        self.icon_toggle = Adw.SwitchRow(title="Show Icon")
        self.icon_toggle.connect("notify::active", self.on_toggle_icon)
        rows.append(self.icon_toggle)

        self.set_settings_defaults()
        self.update_device_selector()
        self.update_top_text_selector()
        self.update_middle_text_selector()
        self.update_bottom_text_selector()
        self.update_album_cover_toggle()
        self.update_icon_toggle()

        return rows

    def get_show_icon_element(self):
        """
        Get the show icon toggle element for the config menu

        Returns:
            Adw.SwitchRow: The show icon toggle element
        """
        return self.icon_toggle

    def set_settings_defaults(self):
        """
        Set the default settings for the action
        """

        settings = self.get_settings()
        # Set defaults for device selection
        if "device_name_" + self.actionName not in settings:
            settings["device_name_" + self.actionName] = self.text_settings[TextOptions.NONE]
        if "device_id_" + self.actionName not in settings:
            settings["device_id_" + self.actionName] = self.text_settings[TextOptions.NONE]

        # Set defaults for top text selection
        if "top_text_" + self.actionName not in settings:
            settings["top_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

        # Set defaults for middle text selection
        if "middle_text_" + self.actionName not in settings:
            settings["middle_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

        # Set defaults for bottom text selection
        if "bottom_text_" + self.actionName not in settings:
            settings["bottom_text_" + self.actionName] = self.text_settings[TextOptions.NONE]

        # Set defaults for album cover toggle
        if "show_album_cover_" + self.actionName not in settings:
            settings["show_album_cover_" + self.actionName] = False
        if "show_icon_" + self.actionName not in settings:
            settings["show_icon_" + self.actionName] = True

        self.set_settings(settings)

    def update_device_selector(self):
        """
        Update the device selector with the available devices
        """

        settings = self.get_settings()

        # Clear the model and add the currently active device
        self.devices_model.append(["Currently Active", None])
        self.avail_devices = self.backend.get_devices()
        for device in self.avail_devices:
            self.devices_model.append([device["name"], device["id"]])

        # Set index of combo box to last selected device
        # If the device is not in the list, set it to 0 and set settings to the first device
        self.devices_select.combo_box.set_active(self.get_index_of_id(settings["device_id_" + self.actionName]))

    def update_top_text_selector(self):
        """
        Update the top text selector with the available options
        """

        settings = self.get_settings()

        # Clear the model and add the options
        self.Top_Text_model.clear()
        for option in TextOptions:
            self.Top_Text_model.append([self.text_settings[option], option.value])

        # Set index of combo box to last selected option
        if settings["top_text_" + self.actionName] is not None:
            position = 0
            for elem in self.Top_Text_model:
                if elem[1] == settings["top_text_" + self.actionName]:
                    self.Top_Text_select.combo_box.set_active(position)
                    return
                position += 1

        # If no valid option found select the first one and set it in the settings
        self.Top_Text_select.combo_box.set_active(0)
        settings["top_text_" + self.actionName] = self.text_settings[TextOptions.NONE]
        self.set_settings(settings)

    def update_middle_text_selector(self):
        """
        Update the middle text selector with the available options
        """

        settings = self.get_settings()

        # Clear the model and add the options
        self.Middle_Text_model.clear()
        for option in TextOptions:
            self.Middle_Text_model.append([self.text_settings[option], option.value])

        # Set index of combo box to last selected option
        if settings["middle_text_" + self.actionName] is not None:
            position = 0
            for elem in self.Middle_Text_model:
                if elem[1] == settings["middle_text_" + self.actionName]:
                    self.Middle_Text_select.combo_box.set_active(position)
                    return
                position += 1

        # If no valid option found select the first one and set it in the settings
        self.Middle_Text_select.combo_box.set_active(0)
        settings["middle_text_" + self.actionName] = self.text_settings[TextOptions.NONE]
        self.set_settings(settings)

    def update_bottom_text_selector(self):
        """
        Update the bottom text selector with the available options
        """

        settings = self.get_settings()

        # Clear the model and add the options
        self.Bottom_Text_model.clear()
        for option in TextOptions:
            self.Bottom_Text_model.append([self.text_settings[option], option.value])

        # Set index of combo box to last selected option
        if settings["bottom_text_" + self.actionName] is not None:
            position = 0
            for elem in self.Bottom_Text_model:
                if elem[1] == settings["bottom_text_" + self.actionName]:
                    self.Bottom_Text_select.combo_box.set_active(position)
                    return
                position += 1

        # If no valid option found select the first one and set it in the settings
        self.Bottom_Text_select.combo_box.set_active(0)
        settings["bottom_text_" + self.actionName] = self.text_settings[TextOptions.NONE]
        self.set_settings(settings)

    def update_album_cover_toggle(self):
        """
        Update the album cover toggle with the current setting
        """

        settings = self.get_settings()

        if "show_album_cover_" + self.actionName in settings:
            self.album_cover_toggle.set_active(settings["show_album_cover_" + self.actionName])
        else:
            self.album_cover_toggle.set_active(False)
            settings["show_album_cover_" + self.actionName] = False
            self.set_settings(settings)

    def update_icon_toggle(self):
        """
        Update the icon toggle with the current setting
        """

        settings = self.get_settings()

        if "show_icon_" + self.actionName in settings:
            self.icon_toggle.set_active(settings["show_icon_" + self.actionName])
        else:
            self.icon_toggle.set_active(True)
            settings["show_icon_" + self.actionName] = True
            self.set_settings(settings)

    def on_device_select(self, combo_box, *args):
        """
        Called when the user selects a device from the combo box
        """
        settings = self.get_settings()
        settings["device_name_" + self.actionName] = self.devices_model[combo_box.get_active()][0]
        settings["device_id_" + self.actionName] = self.devices_model[combo_box.get_active()][1]
        self.set_settings(settings)


    def on_top_text_select(self, combo_box, *args):
        """
        Called when the user selects a top text option from the combo box
        """
        settings = self.get_settings()
        settings["top_text_" + self.actionName] = self.Top_Text_model[combo_box.get_active()][1]
        self.set_settings(settings)


    def on_middle_text_select(self, combo_box, *args):
        """
        Called when the user selects a middle text option from the combo box
        """
        settings = self.get_settings()
        settings["middle_text_" + self.actionName] = self.Middle_Text_model[combo_box.get_active()][1]
        self.set_settings(settings)


    def on_bottom_text_select(self, combo_box, *args):
        """
        Called when the user selects a bottom text option from the combo box
        """
        settings = self.get_settings()
        settings["bottom_text_" + self.actionName] = self.Bottom_Text_model[combo_box.get_active()][1]
        self.set_settings(settings)

    def on_toggle_album_cover(self, switch, *args):
        settings = self.get_settings()
        settings["show_album_cover_" + self.actionName] = switch.get_active()
        self.set_settings(settings)

    def on_toggle_icon(self, switch, *args):
        settings = self.get_settings()
        settings["show_icon_" + self.actionName] = switch.get_active()
        self.set_settings(settings)

    def get_device_id_from_name(self, name: str) -> str:
        """
        Get the device id from the device name
        """
        for device in self.avail_devices:
            if device["name"] == name:
                return device["id"]
        return ""

    def get_index_of_id(self, device_id: str) -> int:
        """
        Get the index of the device id within the combo box
        """
        position = 0
        if device_id is None or device_id == TextOptions.NONE.value or device_id == "" or device_id == "None":
            return 0

        if len(self.devices_model) == 0:
            return 0

        for elem in self.devices_model:
            if elem[1] == device_id:
                return position
            position += 1
        return position

    def get_text(self, text_type: Texts) -> str:
        self.backend.set_action_active(True)
        settings = self.get_settings()

        if settings is None:
            log.error("Settings is None, returning empty string")
            return ""

        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.NONE.value or \
           settings[text_type.value + "_text_" + self.actionName] == "" or \
           settings[text_type.value + "_text_" + self.actionName] == "None":
            return ""
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.DEVICE_NAME.value:
            return self.backend.get_active_device_name()
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.TRACK_NAME.value:
            track = self.backend.get_current_track_info()
            if track is not None and "name" in track:
                return track["name"]
            else:
                return ""
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.ARTIST_NAME.value:
            track = self.backend.get_current_track_info()
            if track is not None and "artists" in track and len(track["artists"]) > 0:
                artists_names = ""
                for artist in track["artists"]:
                    artists_names += artist + ", "
                return artists_names.rstrip(", ")
            else:
                return ""
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.ALBUM_NAME.value:
            track = self.backend.get_current_track_info()
            if track is not None and "album" in track:
                return track["album"]
            else:
                return ""
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.VOLUME.value:
            volume = self.backend.get_volume()
            if volume is not None:
                return str(volume) + "%"
            else:
                return ""
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.DURATION.value:
            duration = self.backend.get_duration_ms()
            if duration is not None:
                hours = self.get_hour_from_ms(duration)
                minutes = self.get_minute_from_ms(duration)
                seconds = self.get_second_from_ms(duration)
                if hours > 0:
                    return f"{hours:02}:{minutes:02}:{seconds:02}"
                elif minutes > 0:
                    return f"{minutes:02}:{seconds:02}"
                else:
                    return f"00:{seconds:02}"
            else:
                return ""
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.ELA_TIME.value:
            elapsed = self.backend.get_elapsed_ms()
            duration = self.backend.get_duration_ms()
            if elapsed is not None and duration is not None:
                hours_duration = self.get_hour_from_ms(duration)
                hours = self.get_hour_from_ms(elapsed)
                minutes = self.get_minute_from_ms(elapsed)
                seconds = self.get_second_from_ms(elapsed)
                if hours_duration > 0:
                    return f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    return f"{minutes:02}:{seconds:02}"
            else:
                return ""
        if settings[text_type.value + "_text_" + self.actionName] == TextOptions.REM_TIME.value:
            remaining = self.backend.get_remaining_ms()
            duration = self.backend.get_duration_ms()
            if remaining is not None and duration is not None:
                hours_duration = self.get_hour_from_ms(duration)
                hours = self.get_hour_from_ms(remaining)
                minutes = self.get_minute_from_ms(remaining)
                seconds = self.get_second_from_ms(remaining)
                if hours_duration > 0:
                    return f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    return f"{minutes:02}:{seconds:02}"
            else:
                return ""

        log.error("Text option " + text_type.value + "_text_" + self.actionName + " is unknown, returning empty string")
        log.error("Setting: " + str(settings[text_type.value + "_text_" + self.actionName]))
        return ""

    def get_hour_from_ms(self, ms: int) -> int:
        return int(ms / (1000 * 60 * 60))

    def get_minute_from_ms(self, ms: int) -> int:
        return int((ms % (1000 * 60 * 60)) / (1000 * 60))

    def get_second_from_ms(self, ms: int) -> int:
        return int((ms % (1000 * 60)) / 1000)

    def get_media(self, icon_path: str = "", icon_scale: float = 0.75) -> Image.Image:
        settings = self.get_settings()
        if settings["show_album_cover_" + self.actionName] == True:     # Album Cover should be shown
            album_cover_path = self.backend.get_album_cover_path()      # Get Album Cover Path
            if album_cover_path == "":                                  # Check if Album Cover Path is valid
                return None
            album_cover_image = Image.open(album_cover_path)            # Open Album Cover as PIL Image
            if album_cover_image is None:                               # Check if Album Cover was opened successfully
                return None
            if icon_path == "" or settings["show_icon_" + self.actionName] == False:    # If no Icon should be shown, return Album Cover
                return album_cover_image
            icon = Image.open(icon_path)                                # Open Icon as PIL Image
            icon = icon.resize((int(icon.width * icon_scale), int(icon.height * icon_scale)))
            if icon is not None:                                        # Check if Icon was opened successfully
                return self.apply_background(background=album_cover_image, icon=icon) # Apply Icon to Album Cover
        elif settings["show_icon_" + self.actionName] == True and icon_path != "":          # Only Icon should be shown
            icon = Image.open(icon_path)                                # Open Icon as PIL Image
            icon = icon.resize((int(icon.width * icon_scale), int(icon.height * icon_scale)))
            return icon

        return None

    def apply_background(self, icon:Image.Image = None, background:Image.Image = None, valign: float = 0, halign: float = 0) -> Image.Image:

        if background is None or icon is None:
            return None

        background = background.resize((icon.width, icon.height))

        left_margin = int((background.width - icon.width) * (halign + 1) / 2)
        top_margin = int((background.height - icon.height) * (valign + 1) / 2)

        background.paste(icon, (left_margin, top_margin), icon)

        return background