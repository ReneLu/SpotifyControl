from gi.repository import Gtk, Adw
import gi

from loguru import logger as log

from src.backend.PluginManager import PluginBase

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

KEY_CLIENT_ID = "client_id"
KEY_PORT_REDIRECT_URI = "port_redirect_uri"


class PluginSettings:
    _status_label: Gtk.Label
    _client_id: Adw.EntryRow
    _port: Adw.SpinRow
    _auth_button: Gtk.Button

    def __init__(self, plugin_base: PluginBase):
        self._plugin_base = plugin_base
        log.debug("Initialize Settings")
        settings = self._plugin_base.get_settings()
        client_id = settings.get(KEY_CLIENT_ID, "")
        port = settings.get(KEY_PORT_REDIRECT_URI, "")

        self._plugin_base.backend.reauthenticate(client_id, port)

    def get_settings_area(self) -> Adw.PreferencesGroup:

        log.debug("Creating settings area")

        self._status_label = Gtk.Label(label=self._plugin_base.lm.get(
                "actions.base.credentials.failed"), css_classes=["spotify-controller-red"])
        # Create client id, secret and redirect uri entry rows
        self._client_id = Adw.EntryRow(
            title=self._plugin_base.lm.get("actions.base.client_id"))
        self._port = Adw.SpinRow.new_with_range(1024, 65535, 1)
        self._port.set_title(self._plugin_base.lm.get("actions.base.port"))
        self._port.set_subtitle(self._plugin_base.lm.get("actions.base.port_default"))
        self._port.set_value(8080)

        # Create validate button
        self._auth_button = Gtk.Button(
            label=self._plugin_base.lm.get("actions.base.validate"))
        self._auth_button.set_margin_top(10)
        self._auth_button.set_margin_bottom(10)

        # Connect signals
        self._client_id.connect("notify::text", self._on_change_client_id)
        self._port.connect("changed", self._on_change_port)
        self._auth_button.connect("clicked", self._on_auth_clicked)

        # Create info
        gh_link_label = self._plugin_base.lm.get("actions.info.link.label")
        gh_link_text = self._plugin_base.lm.get("actions.info.link.text")
        gh_label = Gtk.Label(
            use_markup=True, label=f"{gh_link_label} <a href=\"https://github.com/ReneLu/SpotifyControl\">{gh_link_text}</a>")

        self._load_settings()
        self._enable_auth()

        if not self._plugin_base.backend.is_authed():
            self._status_label = Gtk.Label(label=self._plugin_base.lm.get(
                "actions.base.credentials.failed"), css_classes=["spotify-controller-red"])
        else:
            self._status_label = Gtk.Label(label=self._plugin_base.lm.get(
                "actions.base.credentials.authenticated"), css_classes=["spotify-controller-green"])

        pref_group = Adw.PreferencesGroup()
        pref_group.set_title(self._plugin_base.lm.get(
            "actions.base.credentials.title"))
        pref_group.add(self._status_label)
        pref_group.add(self._client_id)
        pref_group.add(self._port)
        pref_group.add(self._auth_button)
        pref_group.add(gh_label)
        return pref_group

    def _load_settings(self):
        settings = self._plugin_base.get_settings()
        client_id = settings.get(KEY_CLIENT_ID, "")
        port = settings.get(KEY_PORT_REDIRECT_URI, "")

        self._client_id.set_text(client_id)
        self._port.set_value(int(port))

    def _update_status(self, message: str, is_error: bool):
        style = "spotify-controller-red" if is_error else "spotify-controller-green"
        self._status_label.set_text(message)
        self._status_label.set_css_classes([style])

    def _update_settings(self, key: str, value: str):
        settings = self._plugin_base.get_settings()
        settings[key] = value
        self._plugin_base.set_settings(settings)

    def _on_change_client_id(self, entry, _):
        val = entry.get_text().strip()
        self._update_settings(KEY_CLIENT_ID, val)
        self._enable_auth()

    def _on_change_port(self, entry):
        val = entry.get_value()
        self._update_settings(KEY_PORT_REDIRECT_URI, val)
        self._enable_auth()

    def _on_auth_clicked(self, _):
        if not self._plugin_base.backend:
            self._update_status("Failed to load backend", True)
            return
        settings = self._plugin_base.get_settings()
        client_id = settings.get(KEY_CLIENT_ID)
        port = settings.get(KEY_PORT_REDIRECT_URI)
        self._plugin_base.auth_callback_fn = self._on_auth_completed
        if not self._plugin_base.backend.update_client_credentials(client_id, port):
            self._update_status(self._plugin_base.lm.get(
                "actions.base.credentials.missing_client_info"), True)
            return
        if not self._plugin_base.backend.is_authed():
            self._update_status(self._plugin_base.lm.get(
                "actions.base.credentials.failed"), True)
        else:
            self._update_status(self._plugin_base.lm.get(
                "actions.base.credentials.authenticated"), False)

    def _enable_auth(self):
        settings = self._plugin_base.get_settings()
        client_id = settings.get(KEY_CLIENT_ID, "")
        self._auth_button.set_sensitive(len(client_id) > 0)

    def _on_auth_completed(self, success: bool, message: str = ""):
        self._enable_auth()
        if not message:
            lm_key = "authenticated" if success else "failed"
            message = self._plugin_base.lm.get(
                f"actions.base.credentials.{lm_key}")
        self._update_status(message, not success)
