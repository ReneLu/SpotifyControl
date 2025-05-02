# StreamController Spotify Control Plugin

> [!NOTE]
> This plugin only works with a spotify premium account. Not with a free spotify account.
> Also an internetconnection is required.

> [!WARNING]
> Rigth now the plugin performs a lot of calls to the webapi. It can happen that the Calls are too
> much and the app gets blocked from accessing the webapi. That can cause a crash of the streamcontroller.

## What can you do with this Plugin?

With this Plugin you can control any Spotify that is connected to your account.
You can control the client that is running on your system while gaming or you can also control a music box in your Network.

### What actions are available by now
- Play / Pause
- Next / Previous Track
- Repeat playlist / single track / No Repeat
- Shuffle On / Off
- Volume Up / Down / Mute

In most of the action settings you can also choose a target device that is currently active. The default device is the currently active device.

## Initial Setup

- Create a Spotify Developer Application at the [spotify developer page](https://developer.spotify.com/dashboard).
    - Login with your spotify Account.
- Plugin Information
    - App name
        - A speaking name. (e.g. StreamControl Plugin)
    - App description
        - Description of the App
    - Website
        - https://github.com/ReneLu/SpotifyControl
    - Redirect URIs
        - http://127.0.0.1:8080
        - If the Port 8080 is already in use on your system use another port. Change the port in the Plugin Settings too.
    - APIs used
        - Web API

- In StreamController go to the general Plugin Settings.
- In the Client ID field fill in the Client ID of the created spotify app.
- If the Port 8080 is already in use on your system use the other port you specified in the app redirect URI.
- Click on the validate button.
- Your Webbrowser wil show the spotify Login Page. Login with your Spotify Premium Account.
- On the next page click on agree to allow your created app to access your spotify data.
- You will be redirected to a simple page that says that you can close the tab and continue in StreamController.
- If the authentication was successfull the text above the validate buttonm should show "Authenticated successfully"



This plugin uses the Python Module [spotipy](https://spotipy.readthedocs.io/en/2.25.1/#license)

All Icons created by [icons8](https://icons8.com)
