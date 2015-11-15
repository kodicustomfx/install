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
import scraper
import re
import urlparse
import xbmcaddon
import time
from salts_lib.trans_utils import i18n
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

BASE_URL = 'http://watchseries-online.ch'

class WSO_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))
        self.max_pages = int(xbmcaddon.Addon().getSetting('%s-max_pages' % (self.get_name())))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'wso.ch'

    def resolve_link(self, link):
        url = urlparse.urljoin(self.base_url, link)
        html = self._http_get(url, cache_limit=.5)
        match = re.search('href=(?:\'|")([^"\']+)(?:"|\')>Click Here to Play', html)
        if match:
            return match.group(1)
        else:
            return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)

            pattern = 'class="[^"]*tdhost".*?href="([^"]+)">([^<]+)'
            for match in re.finditer(pattern, html, re.DOTALL):
                stream_url, host = match.groups()
                hoster = {'multi-part': False, 'host': host.lower(), 'class': self, 'url': stream_url, 'quality': self._get_quality(video, host, QUALITIES.HIGH), 'views': None, 'rating': None, 'direct': False}
                hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return super(WSO_Scraper, self)._default_get_url(video)

    @classmethod
    def get_settings(cls):
        settings = super(WSO_Scraper, cls).get_settings()
        name = cls.get_name()
        settings.append('         <setting id="%s-max_pages" type="slider" range="1,50" option="int" label="     %s" default="1" visible="eq(-6,true)"/>' % (name, i18n('max_pages')))
        return settings

    def search(self, video_type, title, year):
        url = urlparse.urljoin(self.base_url, '/index')
        html = self._http_get(url, cache_limit=24)

        results = []
        for list_match in re.finditer('class="ddmcc"(.*?)</div>', html, re.DOTALL):
            list_frag = list_match.group(1)
            norm_title = self._normalize_title(title)
            pattern = 'href="([^"]+)">([^<]+)'
            for match in re.finditer(pattern, list_frag):
                url, match_title = match.groups('')
                if norm_title in self._normalize_title(match_title):
                    result = {'url': url.replace(self.base_url, ''), 'title': match_title, 'year': ''}
                    results.append(result)

        return results

    def _get_episode_url(self, show_url, video):
        episode_pattern = '<h2>\s*<a\s+href="([^"]+)[^>]+title="[^"]+[Ss]%02d[Ee]%02d[ "]' % (int(video.season), int(video.episode))
        title_pattern = ''
        airdate_pattern = '<h2>\s*<a\s+href="([^"]+)[^>]+title="[^"]+{year} {p_month} {p_day}[ \)"]'

        for page in xrange(1, self.max_pages + 1):
            url = show_url
            if page > 1: url += '%s/page/%s' % (show_url, page)
            # if page is blank, don't continue getting pages
            url = urlparse.urljoin(self.base_url, url)
            html = self._http_get(url, cache_limit=2)
            if not html:
                return

            ep_url = super(WSO_Scraper, self)._default_get_episode_url(url, video, episode_pattern, title_pattern, airdate_pattern)
            if ep_url is not None:
                return ep_url

    def _http_get(self, url, data=None, cache_limit=8):
        return super(WSO_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)
