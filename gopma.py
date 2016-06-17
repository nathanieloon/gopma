# Google Play Music Assistant // GOPMA
# Version:  0.1.0
# Author:   Nathaniel Oon

# Imports
from gmusicapi import Mobileclient
import getpass
import time
import os
import sys
import ConfigParser
import argparse
import logging
import cPickle as pickle

# Global vars
PLAYLIST_PREFIX = '[GOPMA] '
AGGREGATE_PLAYLIST_NAME = PLAYLIST_PREFIX + 'Group Playlist'
SHARED_PLAYLIST_NAME = PLAYLIST_PREFIX + 'Shared Playlist'
TODAY = PLAYLIST_PREFIX + 'Fresh'
YESTERDAY = PLAYLIST_PREFIX + 'Slightly Stale'
GENRE_PLAYLISTS = {'ALTERNATIVE_INDIE': 'Indie/Alt',
                   'DANCE_ELECTRONIC': 'Electronica',
                   'HIP_HOP_RAP': 'Hip-hop',
                   'R_B_SOUL': 'R&B/Soul',
                   'POP': 'Pop',
                   'ROCK': 'Rock',
                   'SOUNDTRACKS_CAST_ALBUMS': 'Soundtracks',
                   'VOCAL_EASY_LISTENING': 'Easy Listening',
                   'WORLD': 'World',
                   'CLASSICAL': 'Classical',
                   'COMEDY_SPOKEN_WORD_OTHER': 'Comedy/Spoken',
                   'COUNTRY': 'Country',
                   'REGGAE_SKA': 'Reggae',
                   'JAZZ': 'Jazz',
                   'METAL': 'Metal',
                   'BLUES': 'Blues',
                   'HOLIDAY': 'Holiday',
                   'FOLK': 'Folk',
                   'CHRISTIAN_GOSPEL': 'Gospel',
                   'CHILDREN_MUSIC': 'Kid Music'
                   }
ROOT_GENRE_FILE = 'root_genres.data'
CHILD_GENRE_FILE = 'child_genres.data'


class Gopma():
    def __init__(self, action=None):
        print "Initialising GOPMA."
        config = ConfigParser.ConfigParser()
        config.read('config.ini')

        email = config.get('login', 'email')
        password = config.get('login', 'password')
        try:
            auth_token = config.get('login', 'auth_token')
        except:
            auth_token = False
            print "No auth token could be found"

        print "Logging into Google Play Music as", email
        if not auth_token:
            self.api = Mobileclient()
            login = self.api.login(email, password, Mobileclient.FROM_MAC_ADDRESS)

            with open('config.ini', 'w+') as f:
                config.set('login', 'auth_token', self.api.session._authtoken)
                config.write(f)
                f.close()
                print "Saved auth token for later."
        else:
            print "Found an auth token, trying it."
            self.api = Mobileclient()
            self.api.session._authtoken = auth_token
            self.api.session.is_authenticated = True
            login = True

        if not login:
            print "<< Couldn't login. >>"
            sys.exit()
        else:
            print "Successfully logged in as", email

        if action != 'reset_genres':
            print "Loading data."
            self.playlists = self.api.get_all_playlists()
            self.content = self.api.get_all_user_playlist_contents()
            self.root_genres, self.child_genres = self.load_genres()
            print "Data successfully loaded."

    def create_or_retrieve_playlists(self, playlists):
        """ Helper function to create or retrieve playlist IDs for a given agg_lists

            Input: List of playlist names
            Output: Dict of playlist names and IDs
        """
        if type(playlists) is not list:
            print "Stop passing non-lists to this function."
            sys.exit()

        agg_lists = [p for p in self.content
                     if p.get('type') == 'USER_GENERATED' and p.get('name') in playlists]

        # Get all playlist IDs
        agg_playlists = {}
        existing_playlists = [playlist['name'] for playlist in agg_lists]
        for name in playlists:
            if name not in existing_playlists:
                print "Playlist not found, creating", name
                agg_playlists[name] = self.api.create_playlist(name)
                self.api.edit_playlist(agg_playlists[name], public=True)
            else:
                print "Playlist found", name + ", retrieving ID."
                playlist_id = [p['id'] for p in agg_lists
                               if p.get('name') == name][0]
                agg_playlists[name] = playlist_id
                # self.api.edit_playlist(agg_playlists[name], public=True)

        return agg_playlists

    def load_genres(self, reset=False):
        """ Load all genres
        """
        # Get the root genres
        if os.path.isfile(ROOT_GENRE_FILE):
            print "Found a root genres file."
            if reset:
                root_genres = self.api.get_genres()

                with open(ROOT_GENRE_FILE, 'w') as fp:
                    pickle.dump(root_genres, fp)
                print "Root genres have been reset."
            else:
                with open(ROOT_GENRE_FILE) as fp:
                    root_genres = pickle.load(fp)
        else:
            print "Couldn't find a root genres file, retrieving data."
            root_genres = self.api.get_genres()

            with open(ROOT_GENRE_FILE, 'w') as fp:
                pickle.dump(root_genres, fp)

            print "Root genres file created."

        # Get the child genres
        if os.path.isfile(CHILD_GENRE_FILE):
            print "Found a child genres file."
            if reset:
                child_genres = {}

                for genre in root_genres:
                    children = self.api.get_genres(genre['id'])
                    child_names = []
                    for child in children:
                        child_names.append(child['name'])
                    child_genres[genre['id']] = child_names

                with open(CHILD_GENRE_FILE, 'w') as fp:
                    pickle.dump(child_genres, fp)
                print "Child genres have been reset."
            else:
                with open(CHILD_GENRE_FILE) as fp:
                    child_genres = pickle.load(fp)
        else:
            print "Couldn't find a child genres file, retrieving data."
            child_genres = {}

            for genre in root_genres:
                children = self.api.get_genres(genre['id'])
                child_names = []
                for child in children:
                    child_names.append(child['name'])
                child_genres[genre['id']] = child_names

            with open(CHILD_GENRE_FILE, 'w') as fp:
                pickle.dump(child_genres, fp)
            print "Child genres file created."

        return root_genres, child_genres

    def delete_empty_playlists(self):
        """ Delete ALL empty playlists. Be careful with this.
        """
        playlists = self.content
        for playlist in playlists:
            if len(playlist['tracks']) == 0 and playlist['name'] != AGGREGATE_PLAYLIST_NAME:
                self.api.delete_playlist(playlist['id'])
                print "Deleted", playlist['name']

    def create_playlists(self):
        """ Create all needed playlists
        """
        print "Creating/updating playlists."
        self.create_or_retrieve_playlists([AGGREGATE_PLAYLIST_NAME,
                                           SHARED_PLAYLIST_NAME])
        self.create_or_retrieve_playlists([PLAYLIST_PREFIX+genre for genre in GENRE_PLAYLISTS.values()])

    def get_playlist_urls(self):
        """ Get all gopma playlist URLS
        """
        urls = {}
        for playlist in self.playlists:
            if PLAYLIST_PREFIX in playlist['name'] and playlist['type'] == 'USER_GENERATED':
                urls[playlist['name']] = "https://play.google.com/music/playlist/"+playlist['shareToken']
        return urls

    def get_playlist_id(self, name):
        """ Get the playlist ID for a given playlist name
        """
        playlist = [p for p in self.playlists
                    if p.get('name') == name][0]
        return playlist['id']

    def get_share_token(self, playlist_id):
        """ Get the share token for a given playlist ID
        """
        playlist = [p for p in self.playlists
                    if p.get('id') == playlist_id]
        return playlist[0]['shareToken']

    def get_playlist_tracks(self, playlist_id):
        """ Get the tracks for a specified playlist id
        """
        return [p for p in self.content
                if p.get('id') == playlist_id][0]['tracks']

    def get_parent_genre_id(self, genre_name):
        """ Get the parent id for a given genre name
        """
        # Check the root genres first
        for genre in self.root_genres:
            if genre_name == genre['name']:
                return genre['id']

        # Check children genres
        for gid, genres in self.child_genres.items():
            for genre in genres:
                if genre == genre_name:
                    return gid

    def wipe_all_playlists(self):
        """ Wipe all Gopma playlists
        """
        for playlist in self.playlists:
            if PLAYLIST_PREFIX in playlist['name'] and SHARED_PLAYLIST_NAME not in playlist['name']:
                print "Wiping playlist: ", playlist['name']
                self.wipe_playlist(playlist['id'])

    def wipe_playlist(self, playlist_id):
        """ Wipe a given playlist
        """
        playlist_tracks = self.get_playlist_tracks(playlist_id)
        song_ids = [track['id'] for track in playlist_tracks]
        self.api.remove_entries_from_playlist(song_ids)

    def reset_daily_playlists(self):
        """ Reset the daily playlists
        """
        # Get playlists
        agg_playlists = self.create_or_retrieve_playlists([TODAY, YESTERDAY])
        yest_id = agg_playlists[YESTERDAY]
        today_id = agg_playlists[TODAY]

        # Wipe yesterday
        print "Wiping yesterday's playlist."
        self.wipe_playlist(yest_id)

        # Copy today to yesterday
        print "Copying", TODAY, "to", YESTERDAY
        today_tracks = self.get_playlist_tracks(today_id)
        self.api.add_songs_to_playlist(yest_id, [t['trackId'] for t in today_tracks])

        # Wipe today
        print "Wiping today's playlist."
        self.wipe_playlist(today_id)

    def update_group_playlist(self):
        """ Update the big group aggregate and the daily playlist with any new shared songs
        """
        # Get the aggregate playlist songs
        agg_token = self.get_share_token(self.get_playlist_id(AGGREGATE_PLAYLIST_NAME))
        agg_playlists = [p for p in self.playlists
                         if p.get('type') == 'USER_GENERATED' and p.get('shareToken') == agg_token]
        agg_id = agg_playlists[0]['id']

        # Get tracks
        agg_tracks = self.api.get_shared_playlist_contents(agg_token)
        agg_tracks_ids = [track['trackId'] for track in agg_tracks]
        print "Updating group playlists."

        # Get the playlists we want to update with
        shared_lists = [p for p in self.playlists
                        if p.get('name') == SHARED_PLAYLIST_NAME]

        for playlist in shared_lists:
            shared_tracks = self.api.get_shared_playlist_contents(playlist['shareToken'])
            print "\nRetrieving from", playlist['name'], "by", playlist['ownerName'] + ":"

            # Add songs to aggregate playlist
            if len(shared_tracks) == 0:
                print "<< Playlist is empty. >>"
            else:
                no_new = True
                for track in shared_tracks:
                    if track['trackId'] not in agg_tracks_ids:
                        # Add to giant aggregate playlist
                        self.api.add_songs_to_playlist(agg_id, track['trackId'])
                        # Add to daily playlist
                        self.api.add_songs_to_playlist(self.get_playlist_id(TODAY), track['trackId'])
                        # Add to genre relevant playlist
                        self.api.add_songs_to_playlist(self.get_playlist_id(PLAYLIST_PREFIX+GENRE_PLAYLISTS[self.get_parent_genre_id(track['track']['genre'])]), track['trackId'])
                        title = track['track']['title'].encode('ascii', 'ignore')
                        artist = track['track']['artist'].encode('ascii', 'ignore')
                        print "+", title, "by", artist, "has been added."
                        no_new = False
                if no_new:
                    print "<< There are no new tracks to be added from this playlist. >>"

        print "Finished updating group playlists."

if __name__ == "__main__":
    # Args parsing
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--delete", help="Delete all empty playlists.", action='store_true')
    group.add_argument("-w", "--wipe", help="Wipe all GOPMA playlists.", action='store_true')
    group.add_argument("-c", "--create", help="Create all necessary playlists.", action='store_true')
    group.add_argument("-u", "--update", help="Update group playlists.", action='store_true')
    group.add_argument("-r", "--reset", help="Reset the daily playlists.", action='store_true')
    group.add_argument("-g", "--genre_update", help="Reset the genre files.", action='store_true')
    group.add_argument("-l", "--list", help="Return a list of all the GOPMA share urls.", action='store_true')

    args = parser.parse_args()

    # Only initialise the connection if we need it
    if args.delete or args.wipe or args.create or args.update or args.reset or args.list:
        gopma = Gopma()

    if args.delete:
        # Delete empty playlists
        gopma.delete_empty_playlists()

    if args.wipe:
        # Wipe all playlists
        gopma.wipe_all_playlists()

    if args.create:
        # Create genre playlists
        gopma.create_playlists()

    if args.update:
        # Update the group aggregate playlist
        gopma.update_group_playlist()

    if args.reset:
        # Update daily playlists
        gopma.reset_daily_playlists()

    if args.genre_update:
        gopma = Gopma('reset_genres')
        # Reset/update the genre files
        gopma.load_genres(reset=True)

    if args.list:
        urls = gopma.get_playlist_urls()
        for name, url in urls.items():
            print name, url
