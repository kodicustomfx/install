"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import json
import urllib2
from urllib2 import HTTPError
import urllib
import socket
import ssl
import time
import kodi
import log_utils
from db_utils import DB_Connection
from constants import TRAKT_SECTIONS
from constants import TEMP_ERRORS
from constants import SECTIONS

class TraktError(Exception):
    pass

class TraktNotFoundError(Exception):
    pass

class TransientTraktError(Exception):
    pass

BASE_URL = 'api-v2launch.trakt.tv'
V2_API_KEY = 'eb41e95243d8c95152ed72a1fc0394c93cb785cb33aed609fdde1a07454584b4'
CLIENT_SECRET = '96611f3e712a37bd8d3cac9316c4643e0e5fd0a0c02b4eaf4bba8fd57024c72e'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
RESULTS_LIMIT = 10
HIDDEN_SIZE = 100

class Trakt_API():
    def __init__(self, token=None, use_https=False, list_size=RESULTS_LIMIT, timeout=5):
        self.token = token
        self.protocol = 'https://' if use_https else 'http://'
        self.timeout = None if timeout == 0 else timeout
        self.list_size = list_size

    def get_token(self, pin=None):
        url = '/oauth/token'
        data = {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'redirect_uri': REDIRECT_URI}
        if pin:
            data['code'] = pin
            data['grant_type'] = 'authorization_code'
        else:
            refresh_token = kodi.get_setting('trakt_refresh_token')
            if refresh_token:
                data['refresh_token'] = refresh_token
                data['grant_type'] = 'refresh_token'
            else:
                raise TraktError('Can not refresh trakt token. Trakt reauthorizion required.')
            
        return self.__call_trakt(url, data=data, auth=False, cached=False)
    
    def show_list(self, slug, section, username=None, auth=True, cached=True):
        if not username:
            username = 'me'
            cache_limit = 0  # don't cache user's own lists at all
            cached = False
        else:
            cache_limit = 1  # cache other user's list for one hour

        url = '/users/%s/lists/%s/items' % (username, slug)
        params = {'extended': 'full,images'}
        list_data = self.__call_trakt(url, params=params, auth=auth, cache_limit=cache_limit, cached=cached)
        return [item[item['type']] for item in list_data if item['type'] == TRAKT_SECTIONS[section][:-1]]

    def show_watchlist(self, section):
        url = '/users/me/watchlist/%s' % (TRAKT_SECTIONS[section])
        params = {'extended': 'full,images'}
        response = self.__call_trakt(url, params=params, cache_limit=0)
        return [item[TRAKT_SECTIONS[section][:-1]] for item in response]

    def get_list_header(self, slug, username=None, auth=True):
        if not username: username = 'me'
        url = '/users/%s/lists/%s' % (username, slug)
        return self.__call_trakt(url, auth=auth)

    def get_lists(self, username=None):
        if not username: username = 'me'
        url = '/users/%s/lists' % (username)
        return self.__call_trakt(url, cache_limit=0)

    def get_liked_lists(self, cached=True):
        url = '/users/likes/lists'
        return self.__call_trakt(url, cache_limit=4, cached=cached)

    def add_to_list(self, section, slug, items):
        return self.__manage_list('add', section, slug, items)

    def add_to_collection(self, section, item):
        return self.__manage_collection('add', section, item)

    def remove_from_collection(self, section, item):
        return self.__manage_collection('remove', section, item)

    def set_watched(self, section, item, season='', episode='', watched=True):
        url = '/sync/history'
        if not watched: url = url + '/remove'
        data = self.__make_media_list(section, item, season, episode)
        return self.__call_trakt(url, data=data, cache_limit=0)

    def remove_from_list(self, section, slug, items):
        return self.__manage_list('remove', section, slug, items)

    def add_to_watchlist(self, section, items):
        return self.__manage_watchlist('add', section, items)

    def remove_from_watchlist(self, section, items):
        return self.__manage_watchlist('remove', section, items)

    def get_trending(self, section, page=None):
        url = '/%s/trending' % (TRAKT_SECTIONS[section])
        params = {'extended': 'full,images', 'limit': self.list_size}
        if page: params['page'] = page
        response = self.__call_trakt(url, params=params)
        return [item[TRAKT_SECTIONS[section][:-1]] for item in response]

    def get_popular(self, section, page=None):
        url = '/%s/popular' % (TRAKT_SECTIONS[section])
        params = {'extended': 'full,images', 'limit': self.list_size}
        if page: params['page'] = page
        return self.__call_trakt(url, params=params)

    def get_recent(self, section, date, page=None):
        url = '/%s/updates/%s' % (TRAKT_SECTIONS[section], date)
        params = {'extended': 'full,images', 'limit': self.list_size}
        if page: params['page'] = page
        response = self.__call_trakt(url, params=params)
        return [item[TRAKT_SECTIONS[section][:-1]] for item in response]

    def get_most_played(self, section, period, page=None):
        return self.__get_most('played', section, period, page)
    
    def get_most_watched(self, section, period, page=None):
        return self.__get_most('watched', section, period, page)
    
    def get_most_collected(self, section, period, page=None):
        return self.__get_most('collected', section, period, page)
    
    def __get_most(self, category, section, period, page):
        url = '/%s/%s/%s' % (TRAKT_SECTIONS[section], category, period)
        params = {'extended': 'full,images', 'limit': self.list_size}
        if page: params['page'] = page
        response = self.__call_trakt(url, params=params)
        return [item[TRAKT_SECTIONS[section][:-1]] for item in response]
    
    def get_genres(self, section):
        url = '/genres/%s' % (TRAKT_SECTIONS[section])
        return self.__call_trakt(url, cache_limit=7 * 24)

    def get_recommendations(self, section):
        url = '/recommendations/%s' % (TRAKT_SECTIONS[section])
        params = {'extended': 'full,images', 'limit': self.list_size}
        return self.__call_trakt(url, params=params)

#     def get_friends_activity(self, section, include_episodes=False):
#         if section == SECTIONS.TV:
#             types='show'
#             if include_episodes:
#                 types += ',episode'
#         elif section == SECTIONS.MOVIES:
#             types='movie'
#
#         url='/activity/friends.json/%s/%s' % (API_KEY, types)
#         return self.__call_trakt(url)
#
    def get_premieres(self, start_date=None, cached=True):
        url = '/calendars/all/shows/premieres'
        if start_date: url += '/%s' % (start_date)
        params = {'extended': 'full,images', 'auth': False}
        return self.__call_trakt(url, params=params, auth=False, cache_limit=24, cached=cached)

    def get_calendar(self, start_date=None, cached=True):
        url = '/calendars/all/shows'
        if start_date: url += '/%s' % (start_date)
        params = {'extended': 'full,images', 'auth': False}
        return self.__call_trakt(url, params=params, auth=False, cache_limit=24, cached=cached)

    def get_my_calendar(self, start_date=None, cached=True):
        url = '/calendars/my/shows'
        if start_date: url += '/%s' % (start_date)
        params = {'extended': 'full,images', 'auth': True}
        return self.__call_trakt(url, params=params, auth=True, cache_limit=24, cached=cached)

    def get_seasons(self, show_id):
        url = '/shows/%s/seasons' % (show_id)
        params = {'extended': 'full,images'}
        return self.__call_trakt(url, params=params, cache_limit=12)

    def get_episodes(self, show_id, season):
        url = '/shows/%s/seasons/%s' % (show_id, season)
        params = {'extended': 'full,images'}
        return self.__call_trakt(url, params=params, cache_limit=1)

    def get_show_details(self, show_id):
        url = '/shows/%s' % (show_id)
        params = {'extended': 'full,images'}
        return self.__call_trakt(url, params=params, cache_limit=24 * 7)

    def get_episode_details(self, show_id, season, episode):
        url = '/shows/%s/seasons/%s/episodes/%s' % (show_id, season, episode)
        params = {'extended': 'full,images'}
        return self.__call_trakt(url, params=params, cache_limit=8)

    def get_movie_details(self, show_id):
        url = '/movies/%s' % (show_id)
        params = {'extended': 'full,images'}
        return self.__call_trakt(url, params=params, cache_limit=8)

    def get_people(self, section, show_id, full=False):
        url = '/%s/%s/people' % (TRAKT_SECTIONS[section], show_id)
        params = {'extended': 'full,images'} if full else None
        try:
            return self.__call_trakt(url, params=params, cache_limit=24 * 30)
        except TraktNotFoundError:
            return {}

    def search(self, section, query, page=None):
        url = '/search'
        params = {'type': TRAKT_SECTIONS[section][:-1], 'query': query, 'limit': self.list_size}
        if page: params['page'] = page
        # params.update({'extended': 'full,images'})
        response = self.__call_trakt(url, params=params)
        return [item[TRAKT_SECTIONS[section][:-1]] for item in response]

    def get_collection(self, section, full=True, cached=True):
        url = '/users/me/collection/%s' % (TRAKT_SECTIONS[section])
        params = {'extended': 'full,images'} if full else None
        response = self.__call_trakt(url, params=params, cached=cached)
        result = []
        for item in response:
            element = item[TRAKT_SECTIONS[section][:-1]]
            if section == SECTIONS.TV:
                element['seasons'] = item['seasons']
            result.append(element)
        return result

    def get_watched(self, section, full=False, cached=True):
        url = '/sync/watched/%s' % (TRAKT_SECTIONS[section])
        params = {'extended': 'full,images'} if full else None
        return self.__call_trakt(url, params=params, cached=cached)

    def get_show_progress(self, show_id, full=False, hidden=False, specials=False, cached=True):
        url = '/shows/%s/progress/watched' % (show_id)
        params = {}
        if full: params['extended'] = 'full,images'
        if hidden: params['hidden'] = 'true'
        if specials: params['specials'] = 'true'
            
        return self.__call_trakt(url, params=params, cached=cached)

    def get_hidden_progress(self, cached=True):
        url = '/users/hidden/progress_watched'
        params = {'type': 'show', 'limit': HIDDEN_SIZE, 'page': 1}
        length = -1
        result = []
        while length != 0 or length == HIDDEN_SIZE:
            hidden = self.__call_trakt(url, params=params, cached=cached)
            length = len(hidden)
            result += hidden
            params['page'] += 1
        return result
    
    def get_user_profile(self, username=None, cached=True):
        if username is None: username = 'me'
        url = '/users/%s' % (username)
        return self.__call_trakt(url, cached=cached)
        
    def get_bookmarks(self):
        url = '/sync/playback'
        return self.__call_trakt(url, cached=False)

    def get_bookmark(self, show_id, season, episode):
        response = self.get_bookmarks()
        for bookmark in response:
            if not season or not episode:
                if bookmark['type'] == 'movie' and show_id == bookmark['movie']['ids']['trakt']:
                    return bookmark['progress']
            else:
                # log_utils.log('Resume: %s, %s, %s, %s' % (bookmark, show_id, season, episode), xbmc.LOGDEBUG)
                if bookmark['type'] == 'episode' and show_id == bookmark['show']['ids']['trakt'] and bookmark['episode']['season'] == int(season) and bookmark['episode']['number'] == int(episode):
                    return bookmark['progress']

    def rate(self, section, item, rating, season='', episode=''):
        url = '/sync/ratings'
        data = self.__make_media_list(section, item, season, episode)

        if rating is None:
            url = url + '/remove'
        else:
            # method only allows ratings one item at a time, so set rating on first item of each in list
            if season and episode:
                data[TRAKT_SECTIONS[section]][0]['seasons'][0]['episodes'][0].update({'rating': int(rating)})
            elif season:
                data[TRAKT_SECTIONS[section]][0]['seasons'][0].update({'rating': int(rating)})
            else:
                data[TRAKT_SECTIONS[section]][0].update({'rating': int(rating)})

        self.__call_trakt(url, data=data, cache_limit=0)

    def __manage_list(self, action, section, slug, items):
        url = '/users/me/lists/%s/items' % (slug)
        if action == 'remove': url = url + '/remove'
        if not isinstance(items, (list, tuple)): items = [items]
        data = self.__make_media_list_from_list(section, items)
        return self.__call_trakt(url, data=data, cache_limit=0)

    def __manage_watchlist(self, action, section, items):
        url = '/sync/watchlist'
        if action == 'remove': url = url + '/remove'
        if not isinstance(items, (list, tuple)): items = [items]
        data = self.__make_media_list_from_list(section, items)
        return self.__call_trakt(url, data=data, cache_limit=0)

    def __manage_collection(self, action, section, item):
        url = '/sync/collection'
        if action == 'remove': url = url + '/remove'
        data = self.__make_media_list(section, item)
        return self.__call_trakt(url, data=data, cache_limit=0)

    def __make_media_list(self, section, item, season='', episode=''):
        ids = {'ids': item}
        if section == SECTIONS.MOVIES:
            data = {'movies': [ids]}
        else:
            data = {'shows': [ids]}
            if season:
                data['shows'][0]['seasons'] = [{'number': int(season)}]
                if episode:
                    data['shows'][0]['seasons'][0]['episodes'] = [{'number':int(episode)}]
        return data

    def __make_media_list_from_list(self, section, items):
        data = {TRAKT_SECTIONS[section]: []}
        for item in items:
            ids = {'ids': item}
            data[TRAKT_SECTIONS[section]].append(ids)
        return data

    def __call_trakt(self, url, data=None, params=None, auth=True, cache_limit=.25, cached=True):
        if not cached: cache_limit = 0
        db_cache_limit = cache_limit if cache_limit > 8 else 8
        json_data = json.dumps(data) if data else None
        headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': 2}
        url = '%s%s%s' % (self.protocol, BASE_URL, url)
        if params: url = url + '?' + urllib.urlencode(params)

        db_connection = DB_Connection()
        created, cached_result = db_connection.get_cached_url(url, db_cache_limit)
        if cached_result and (time.time() - created) < (60 * 60 * cache_limit):
            result = cached_result
            log_utils.log('Returning cached result for: %s' % (url), log_utils.LOGDEBUG)
        else:
            auth_retry = False
            while True:
                try:
                    if auth: headers.update({'Authorization': 'Bearer %s' % (self.token)})
                    log_utils.log('Trakt Call: %s, header: %s, data: %s' % (url, headers, data), log_utils.LOGDEBUG)
                    request = urllib2.Request(url, data=json_data, headers=headers)
                    f = urllib2.urlopen(request, timeout=self.timeout)
                    result = ''
                    while True:
                        data = f.read()
                        if not data: break
                        result += data

                    db_connection.cache_url(url, result)
                    break
                except (ssl.SSLError, socket.timeout)  as e:
                    if cached_result:
                        result = cached_result
                        log_utils.log('Temporary Trakt Error (%s). Using Cached Page Instead.' % (str(e)), log_utils.LOGWARNING)
                    else:
                        raise TransientTraktError('Temporary Trakt Error: ' + str(e))
                except urllib2.URLError as e:
                    if isinstance(e, urllib2.HTTPError):
                        if e.code in TEMP_ERRORS:
                            if cached_result:
                                result = cached_result
                                log_utils.log('Temporary Trakt Error (%s). Using Cached Page Instead.' % (str(e)), log_utils.LOGWARNING)
                                break
                            else:
                                raise TransientTraktError('Temporary Trakt Error: ' + str(e))
                        elif e.code == 401 or e.code == 405:
                            if auth_retry or url.endswith('/token'):
                                self.token = None
                                kodi.set_setting('trakt_oauth_token', '')
                                kodi.set_setting('trakt_refresh_token', '')
                                raise TraktError('Trakt Call Authentication Failed (%s)' % (e.code))
                            else:
                                result = self.get_token()
                                self.token = result['access_token']
                                kodi.set_setting('trakt_oauth_token', result['access_token'])
                                kodi.set_setting('trakt_refresh_token', result['refresh_token'])
                                auth_retry = True
                        elif e.code == 404:
                            raise TraktNotFoundError()
                        else:
                            raise
                    elif isinstance(e.reason, socket.timeout) or isinstance(e.reason, ssl.SSLError):
                        if cached_result:
                            result = cached_result
                            log_utils.log('Temporary Trakt Error (%s). Using Cached Page Instead' % (str(e)), log_utils.LOGWARNING)
                            break
                        else:
                            raise TransientTraktError('Temporary Trakt Error: ' + str(e))
                    else:
                        raise TraktError('Trakt Error: ' + str(e))
                except:
                    raise

        response = json.loads(result)

        if 'status' in response and response['status'] == 'failure':
            if 'message' in response: raise TraktError(response['message'])
            if 'error' in response: raise TraktError(response['error'])
            else: raise TraktError()
        else:
            # log_utils.log('Trakt Response: %s' % (response), xbmc.LOGDEBUG)
            return response
