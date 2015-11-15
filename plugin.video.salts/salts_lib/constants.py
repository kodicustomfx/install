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
def __enum(**enums):
    return type('Enum', (), enums)

MODES = __enum(MAIN='main', BROWSE='browse', TRENDING='trending', RECOMMEND='recommend', FRIENDS='friends', CAL='calendar', MY_CAL='my_calendar', MY_LISTS='lists',
           SEARCH='search', SEASONS='seasons', EPISODES='episodes', GET_SOURCES='get_sources', MANAGE_SUBS='manage_subs', GET_LIST='get_list', SET_URL_MANUAL='set_url_manual',
           SET_URL_SEARCH='set_url_search', SHOW_FAVORITES='browse_favorites', SHOW_WATCHLIST='browse_watchlist', PREMIERES='premiere_calendar', SHOW_LIST='show_list',
           OTHER_LISTS='other_lists', ADD_OTHER_LIST='add_other_list', PICK_SUB_LIST='pick_sub_list', PICK_FAV_LIST='pick_fav_list', UPDATE_SUBS='update_subs', CLEAN_SUBS='clean_subs',
           SET_SUB_LIST='set_sub_list', SET_FAV_LIST='set_fav_list', REM_FROM_LIST='rem_from_list', ADD_TO_LIST='add_to_list', ADD_TO_LIBRARY='add_to_library', SCRAPERS='scrapers',
           TOGGLE_SCRAPER='toggle_scraper', RESET_DB='reset_db', FLUSH_CACHE='flush_cache', RESOLVE_SOURCE='resolve_source', SEARCH_RESULTS='search_results',
           MOVE_SCRAPER = 'scraper_move', FRIENDS_EPISODE = 'friends_episode', EDIT_TVSHOW_ID = 'edit_id', SELECT_SOURCE = 'select_source', SHOW_COLLECTION = 'show_collection',
           SHOW_PROGRESS='show_progress', PLAY_TRAILER='play_trailer', RENAME_LIST='rename_list', EXPORT_DB='export_db', IMPORT_DB='import_db', COPY_LIST='copy_list',
           REMOVE_LIST='remove_list', ADD_TO_COLL='add_to_collection', TOGGLE_WATCHED='toggle_watched', RATE='rate', FORCE_REFRESH='force_refresh', TOGGLE_TITLE='toggle_title',
           RES_SETTINGS='resolver_settings', ADDON_SETTINGS='addon_settings', TOGGLE_ALL='toggle_all', MOVE_TO='move_to', REM_FROM_COLL='rem_from_collection',
           URL_EXISTS='url_exists', RECENT_SEARCH='recent_search', SAVED_SEARCHES='saved_searches', SAVE_SEARCH='save_search', DELETE_SEARCH='delete_search', SET_VIEW='set_view',
           SETTINGS='settings', SHOW_VIEWS='show_views', BROWSE_VIEW='browse_view', BROWSE_URLS='browse_urls', DELETE_URL='delete_url', DOWNLOAD_SOURCE='download_source',
           DIRECT_DOWNLOAD='direct_download', POPULAR='popular', RECENT='recent', DELETE_RECENT='delete_recent', CLEAR_RECENT='clear_recent', GET_PIN='get_pin',
           AUTO_CONF='auto_config', CLEAR_SAVED='clear_saved', RESET_BASE_URL='reset_base_url', TOGGLE_TO_MENU='toggle_to_menu', LIKED_LISTS='liked_lists', MOSTS='mosts',
           PLAYED='played', WATCHED='watched', COLLECTED='collected')
SECTIONS = __enum(TV='TV', MOVIES='Movies')
VIDEO_TYPES = __enum(TVSHOW='TV Show', MOVIE='Movie', EPISODE='Episode', SEASON='Season')
CONTENT_TYPES = __enum(TVSHOWS='tvshows', MOVIES='movies', SEASONS='seasons', EPISODES='episodes')
TRAKT_SECTIONS = {SECTIONS.TV: 'shows', SECTIONS.MOVIES: 'movies'}
TRAKT_SORT = __enum(TITLE='title', ACTIVITY='activity', MOST_COMPLETED='most-completed', LEAST_COMPLETED='least-completed', RECENTLY_AIRED='recently-aired', PREVIOUSLY_AIRED='previously-aired')
SORT_MAP = [TRAKT_SORT.ACTIVITY, TRAKT_SORT.TITLE, TRAKT_SORT.MOST_COMPLETED, TRAKT_SORT.LEAST_COMPLETED, TRAKT_SORT.RECENTLY_AIRED, TRAKT_SORT.PREVIOUSLY_AIRED]
QUALITIES = __enum(LOW='Low', MEDIUM='Medium', HIGH='High', HD720='HD720', HD1080='HD1080')
DIRS = __enum(UP='up', DOWN='down')
WATCHLIST_SLUG = 'watchlist_slug'
COLLECTION_SLUG = 'collection_slug'
USER_AGENT = "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko"
SEARCH_HISTORY = 10
DEFAULT_EXT = '.mpg'
CHUNK_SIZE = 512 * 1024
PROGRESS = __enum(OFF=0, WINDOW=1, BACKGROUND=2)

# sort keys need to be defined such that "best" have highest values
# unknown (i.e. None) is always worst
SORT_KEYS = {}
SORT_KEYS['quality'] = {None: 0, QUALITIES.LOW: 1, QUALITIES.MEDIUM: 2, QUALITIES.HIGH: 3, QUALITIES.HD720: 4, QUALITIES.HD1080: 5}
SORT_LIST = ['none', 'source', 'quality', 'views', 'rating', 'direct']
SORT_SIGNS = {'0': -1, '1': 1}  # 0 = Best to Worst; 1 = Worst to Best

HOURS_LIST = {}
HOURS_LIST[MODES.UPDATE_SUBS] = [.5, 1] + range(2, 25)
LONG_AGO = '1970-01-01 23:59:00.000000'
TEMP_ERRORS = [500, 502, 503, 504, 520, 521, 522, 524]
SRT_SOURCE = 'addic7ed'
DISABLE_SETTINGS = __enum(OFF='0', PROMPT='1', ON='2')

BLOG_Q_MAP = {}
BLOG_Q_MAP[QUALITIES.LOW] = [' CAM ', ' TS ', ' R6 ']
BLOG_Q_MAP[QUALITIES.MEDIUM] = ['-XVID', '-MP4']
BLOG_Q_MAP[QUALITIES.HIGH] = ['HDRIP', 'DVDRIP', 'BRRIP', 'BDRIP', '480P']
BLOG_Q_MAP[QUALITIES.HD720] = ['720']
BLOG_Q_MAP[QUALITIES.HD1080] = ['1080']

HOST_Q = {}
HOST_Q[QUALITIES.LOW] = ['youwatch', 'allmyvideos', 'played.to', 'gorillavid']
HOST_Q[QUALITIES.MEDIUM] = ['primeshare', 'exashare', 'bestreams', 'flashx', 'vidto', 'vodlocker', 'thevideo', 'vidzi', 'vidbull', 'realvid', 'nosvideo', 'daclips', 'sharerepo', 'zalaa']
HOST_Q[QUALITIES.HIGH] = ['vidspot', 'mrfile', 'divxstage', 'streamcloud', 'mooshare', 'novamov', 'mail.ru', 'videomega']
HOST_Q[QUALITIES.HD720] = ['thefile', 'sharesix', 'filenuke', 'vidxden', 'movshare', 'nowvideo', 'vidbux']
HOST_Q[QUALITIES.HD1080] = ['hugefiles', '180upload', 'mightyupload']

Q_ORDER = {QUALITIES.LOW: 1, QUALITIES.MEDIUM: 2, QUALITIES.HIGH: 3, QUALITIES.HD720: 4, QUALITIES.HD1080: 5}

IMG_SIZES = ['full', 'medium', 'thumb']
