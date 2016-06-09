# GOPMA

GOPMA - The Google Play Music Assistant

For aggregating group playlists. Built on the unofficial [Google Music API](https://github.com/simon-weber/gmusicapi).


## Installation

1. Install [Google Music API](https://github.com/simon-weber/gmusicapi) with ``` pip install gmusicapi ```
2. Generate an application specific password for your Google account [here](https://security.google.com/settings/security/apppasswords).
3. Create a ```config.ini``` file in the same directory as ```gopma.py```. It should include:
```
[login]
email=example@gmail.com
password=application_password_here
```
At this point you should be good to go!

## Getting started
I haven't actually tested this from scratch yet. What SHOULD happen is the following:

1. Run GOPMA with the ```--create``` argument. This should create a whole heap of playlists (genres, the daily playlists, and the giant aggregate)
2. Get your friends to make playlists named "[GOPMA] Shared Playlist" (this is configurable in the global settings). 
3. Get them to make those playlists public, have them share the link with you, and then you subscribe to them.
4. Run GOPMA with the ```--update``` argument.
5. If everything looks like it's working, set it up as a cronjob on your server.

## Usage
```
usage: gopma.py [-h] [-d | -w | -c | -u | -r | -g | -l]

optional arguments:
  -h, --help          show this help message and exit
  -d, --delete        Delete all empty playlists.
  -w, --wipe          Wipe all GOPMA playlists.
  -c, --create        Create all necessary playlists.
  -u, --update        Update group playlists.
  -r, --reset         Reset the daily playlists.
  -g, --genre_update  Reset the genre files.
  -l, --list          Return a list of all the GOPMA share urls.
```
