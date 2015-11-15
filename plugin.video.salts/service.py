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
import xbmc
import xbmcaddon
import xbmcgui
from salts_lib import log_utils
from salts_lib import utils
from salts_lib.constants import MODES
from salts_lib.db_utils import DB_Connection

MAX_ERRORS = 10

kodi = xbmcaddon.Addon(id='plugin.video.salts')
log_utils.log('Service: Installed Version: %s' % (kodi.getAddonInfo('version')))

db_connection = DB_Connection()
if kodi.getSetting('use_remote_db') == 'false' or kodi.getSetting('enable_upgrade') == 'true':
    db_connection.init_database()

class Service(xbmc.Player):
    def __init__(self, *args, **kwargs):
        log_utils.log('Service: starting...')
        xbmc.Player.__init__(self, *args, **kwargs)
        self.win = xbmcgui.Window(10000)
        self.reset()

    def reset(self):
        log_utils.log('Service: Resetting...')
        self.win.clearProperty('salts.playing')
        self.win.clearProperty('salts.playing.trakt_id')
        self.win.clearProperty('salts.playing.season')
        self.win.clearProperty('salts.playing.episode')
        self.win.clearProperty('salts.playing.srt')
        self.win.clearProperty('salts.playing.resume')
        self.tracked = False
        self._totalTime = 999999
        self.trakt_id = None
        self.season = None
        self.episode = None
        self._lastPos = 0

    def onPlayBackStarted(self):
        log_utils.log('Service: Playback started')
        playing = self.win.getProperty('salts.playing') == 'True'
        self.trakt_id = self.win.getProperty('salts.playing.trakt_id')
        self.season = self.win.getProperty('salts.playing.season')
        self.episode = self.win.getProperty('salts.playing.episode')
        srt_path = self.win.getProperty('salts.playing.srt')
        resume_point = self.win.getProperty('salts.playing.trakt_resume')
        if playing:   # Playback is ours
            log_utils.log('Service: tracking progress...')
            self.tracked = True
            if srt_path:
                log_utils.log('Service: Enabling subtitles: %s' % (srt_path))
                self.setSubtitles(srt_path)
            else:
                self.showSubtitles(False)

        self._totalTime = 0
        while self._totalTime == 0:
            try:
                self._totalTime = self.getTotalTime()
            except RuntimeError:
                self._totalTime = 0
                break
            xbmc.sleep(1000)

        if resume_point:
            resume_time = float(resume_point) * self._totalTime / 100
            log_utils.log("Resume Percent: %s, Resume Time: %s Total Time: %s" % (resume_point, resume_time, self._totalTime), log_utils.LOGDEBUG)
            self.seekTime(resume_time)

    def onPlayBackStopped(self):
        log_utils.log('Service: Playback Stopped')
        if self.tracked:
            playedTime = float(self._lastPos)
            try: percent_played = int((playedTime / self._totalTime) * 100)
            except: percent_played = 0  # guard div by zero
            pTime = utils.format_time(playedTime)
            tTime = utils.format_time(self._totalTime)
            log_utils.log('Service: Played %s of %s total = %s%%' % (pTime, tTime, percent_played), log_utils.LOGDEBUG)
            if playedTime == 0 and self._totalTime == 999999:
                log_utils.log('XBMC silently failed to start playback', log_utils.LOGWARNING)
            elif playedTime >= 5:
                log_utils.log('Service: Setting bookmark on |%s|%s|%s| to %s seconds' % (self.trakt_id, self.season, self.episode, playedTime), log_utils.LOGDEBUG)
                db_connection.set_bookmark(self.trakt_id, playedTime, self.season, self.episode)
                if percent_played >= 75:
                    if xbmc.getCondVisibility('System.HasAddon(script.trakt)'):
                        run = 'RunScript(script.trakt, action=sync, silent=True)'
                        xbmc.executebuiltin(run)
            self.reset()

    def onPlayBackEnded(self):
        log_utils.log('Service: Playback completed')
        self.onPlayBackStopped()

monitor = Service()
utils.do_startup_task(MODES.UPDATE_SUBS)

errors = 0
while not xbmc.abortRequested:
    try:
        isPlaying = monitor.isPlaying()
        utils.do_scheduled_task(MODES.UPDATE_SUBS, isPlaying)
        if monitor.tracked and monitor.isPlayingVideo():
            monitor._lastPos = monitor.getTime()
    except Exception as e:
        errors += 1
        if errors >= MAX_ERRORS:
            log_utils.log('Service: Error (%s) received..(%s/%s)...Ending Service...' % (e, errors, MAX_ERRORS), log_utils.LOGERROR)
            break
        else:
            log_utils.log('Service: Error (%s) received..(%s/%s)...Continuing Service...' % (e, errors, MAX_ERRORS), log_utils.LOGERROR)
    else:
        errors = 0

    xbmc.sleep(1000)
log_utils.log('Service: shutting down...')
