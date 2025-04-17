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

    def __init__(self):
        super().__init__()
        log.debug("Initialize SpotifyControlBackend")
        # Get the username from terminal
        username = "killerawft"
        scope = 'user-read-private user-read-playback-state user-modify-playback-state'
        # Erase cache and prompt for user permission
        try:
            token = util.prompt_for_user_token(username, scope) # add scope
        except (AttributeError, JSONDecodeError):
            os.remove(f".cache-{username}")
            token = util.prompt_for_user_token(username, scope) # add scope

        log.debug("Token created")
        # Create our spotify object with permissions
        self.spotifyObject = spotipy.Spotify(auth=token)
        log.debug("SpotifyControlBackend started")

    def get_spotify_object(self):
        """
        Get the spotify object
        """
        return self.spotifyObject

    def get_active_device_id(self):
        """
        Get the active device ID
        """
        devices = self.spotifyObject.devices()
        devices = devices['devices']
        for item in devices:
            if item['is_active']:
                deviceID = item['id']
                log.debug("Current active device " + str(item['name'] +
                          " with ID " + str(self.deviceID)))
                return deviceID
        return None

    def get_devices(self):
        """
        Get all devices
        """
        deviceList = self.spotifyObject.devices()
        deviceList = deviceList['devices']
        log.debug("Devices: " + str(deviceList))

        return deviceList

backend = SpotifyControlBackend()
log.debug("SpotifyControlBackend initialized")
