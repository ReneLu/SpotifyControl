from streamcontroller_plugin_tools import BackendBase

import os
import sys
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import spotipy.util as util
from json.decoder import JSONDecodeError
from loguru import logger as log

class SpotifyControlBackend(BackendBase):

    spotifyObject = None
    is_authed = False

    # User Credetials
    client_id = None
    client_secret = None
    client_uri = None
    username = None

    def __init__(self):
        super().__init__()
        log.info("Initialize SpotifyControlBackend")

    def get_spotify_object(self):
        """
        Get the spotify object
        """
        return self.spotifyObject

    def get_active_device_id(self):
        """
        Get the active device ID
        """
        for item in self.get_devices():
            if item['is_active']:
                deviceID = item['id']
                log.info("Current active device " + str(item['name'] +
                          " with ID " + str(self.deviceID)))
                return deviceID
        return None

    def get_devices(self):
        """
        Get all devices
        """
        deviceList = self.spotifyObject.devices()
        deviceList = deviceList['devices']
        log.info("Devices: " + str(deviceList))

        return deviceList

    def update_client_credentials(self, client_id: str, client_secret: str, client_uri: str = "", username: str = ""):
        if None in (client_id, client_secret, client_uri, username) or "" in (client_id, client_secret, client_uri, username):
            self.frontend.on_auth_callback(
                False, "actions.base.credentials.missing_client_info")
            return
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_uri = client_uri
        self.username = username
        self.setup_client()

    def setup_client(self):
        """
        Setup the client
        """
        scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
        self.spotifyObject = spotipy.Spotify(
            auth_manager=SpotifyOAuth(client_id=self.client_id,
                                      client_secret=self.client_secret,
                                      redirect_uri=self.client_uri,
                                      scope=scope))
        self.is_authed = True
        log.info("SpotifyControlBackend setup complete")

    def is_authed(self) -> bool:
        """
        Check if the user is authenticated
        """
        return self.is_authed

backend = SpotifyControlBackend()
log.info("SpotifyControlBackend initialized")
