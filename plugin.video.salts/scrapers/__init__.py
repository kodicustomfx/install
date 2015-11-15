__all__ = ['scraper', 'local_scraper', 'pw_scraper', 'uflix_scraper', 'watchseries_scraper', 'movie25_scraper', 'merdb_scraper', '2movies_scraper', 'icefilms_scraper',
           'movieshd_scraper', 'yifytv_scraper', 'viooz_scraper', 'filmstreaming_scraper', 'myvideolinks_scraper', 'filmikz_scraper', 'clickplay_scraper', 'nitertv_scraper',
           'iwatch_scraper', 'ororotv_scraper', 'view47_scraper', 'vidics_scraper', 'oneclickwatch_scraper', 'istreamhd_scraper', 'losmovies_scraper', 'movie4k_scraper',
           'noobroom_scraper', 'solar_scraper', 'vkbox_scraper', 'directdl_scraper', 'movietv_scraper', 'moviesonline7_scraper', 'streamallthis_scraper', 'afdah_scraper',
           'streamtv_scraper', 'moviestorm_scraper', 'wmo_scraper', 'zumvo_scraper', 'wso_scraper', 'tvrelease_scraper', 'hdmz_scraper', 'ch131_scraper', 'watchfree_scraper',
           'pftv_scraper', 'flixanity_scraper', 'cmz_scraper', 'movienight_scraper', 'gvcenter_scraper', 'alluc_scraper', 'afdahorg_scraper', 'xmovies8_scraper',
           'yifystreaming_scraper', 'mintmovies_scraper', 'playbox_scraper', 'shush_proxy', 'mvsnap_scraper', 'pubfilm_scraper', 'pctf_scraper', 'rlssource_scraper',
           'couchtunerv1_scraper', 'couchtunerv2_scraper', 'tunemovie_scraper', 'watch8now_scraper', 'megabox_scraper', 'dizilab_scraper', 'beinmovie_scraper',
           'dizimag_scraper', 'ayyex_scraper']

import re
import os
import xbmcaddon
import xbmc
import datetime
import time
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from . import scraper  # just to avoid editor warning
from . import *

class ScraperVideo:
    def __init__(self, video_type, title, year, trakt_id, season='', episode='', ep_title='', ep_airdate=''):
        assert(video_type in (VIDEO_TYPES.__dict__[k] for k in VIDEO_TYPES.__dict__ if not k.startswith('__')))
        self.video_type = video_type
        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.ep_title = ep_title
        self.trakt_id = trakt_id
        self.ep_airdate = None
        if ep_airdate:
            try: self.ep_airdate = datetime.datetime.strptime(ep_airdate, "%Y-%m-%d").date()
            except (TypeError, ImportError): self.ep_airdate = datetime.date(*(time.strptime(ep_airdate, '%Y-%m-%d')[0:3]))

    def __str__(self):
        return '|%s|%s|%s|%s|%s|%s|%s|' % (self.video_type, self.title, self.year, self.season, self.episode, self.ep_title, self.ep_airdate)

def update_xml(xml, new_settings, cat_count):
    new_settings.insert(0, '<category label="Scrapers %s">' % (cat_count))
    new_settings.append('    </category>')
    new_str = '\n'.join(new_settings)
    match = re.search('(<category label="Scrapers %s">.*?</category>)' % (cat_count), xml, re.DOTALL | re.I)
    if match:
        old_settings = match.group(1)
        if old_settings != new_settings:
            xml = xml.replace(old_settings, new_str)
    else:
        log_utils.log('Unable to match category: %s' % (cat_count), xbmc.LOGWARNING)
    return xml

def update_settings():
    path = xbmcaddon.Addon().getAddonInfo('path')
    full_path = os.path.join(path, 'resources', 'settings.xml')
    try:
        with open(full_path, 'r') as f:
            xml = f.read()
    except:
        raise

    new_settings = []
    cat_count = 1
    old_xml = xml
    classes = scraper.Scraper.__class__.__subclasses__(scraper.Scraper)
    for cls in sorted(classes, key=lambda x: x.get_name().upper()):
        new_settings += cls.get_settings()

        if len(new_settings) > 90:
            xml = update_xml(xml, new_settings, cat_count)
            new_settings = []
            cat_count += 1

    if new_settings:
        xml = update_xml(xml, new_settings, cat_count)

    if xml != old_xml:
        try:
            with open(full_path, 'w') as f:
                f.write(xml)
        except:
            raise
    else:
        log_utils.log('No Settings Update Needed', xbmc.LOGDEBUG)

update_settings()
