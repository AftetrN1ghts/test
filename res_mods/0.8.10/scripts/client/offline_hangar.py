import BigWorld
import cPickle
import time
import copy
from debug_utils import LOG_DEBUG, LOG_CURRENT_EXCEPTION

_patched = False


class FakeBase(object):
    """Absorbs all method calls to the server-side base entity."""

    def __getattr__(self, name):
        def noop(*args, **kwargs):
            LOG_DEBUG('offline_hangar FakeBase: ignored call to base.%s' % name)
        return noop


def _patch_personality():
    from PlayerEvents import g_playerEvents
    from gui.shared import personality

    g_playerEvents.onAccountShowGUI -= personality.onAccountShowGUI

    def offline_onAccountShowGUI(ctx):
        LOG_DEBUG('offline_hangar: onAccountShowGUI called')
        try:
            from gui.LobbyContext import g_lobbyContext
            from gui.shared.utils.HangarSpace import g_hangarSpace
            from CurrentVehicle import g_currentVehicle
            from gui.WindowsManager import g_windowsManager
            from gui.Scaleform.Waiting import Waiting
            from gui.shared.events import ShowViewEvent
            import SoundGroups
            import MusicController

            g_lobbyContext.onAccountShowGUI(ctx)

            try:
                MusicController.g_musicController.play(MusicController.MUSIC_EVENT_LOBBY)
                MusicController.g_musicController.play(MusicController.AMBIENT_EVENT_LOBBY)
            except Exception:
                LOG_CURRENT_EXCEPTION()

            if g_hangarSpace.inited:
                g_hangarSpace.refreshSpace(False)
            else:
                g_hangarSpace.init(False)

            try:
                g_currentVehicle.init()
            except Exception:
                LOG_DEBUG('offline_hangar: g_currentVehicle.init() failed (expected without inventory)')

            app = g_windowsManager.window
            if app is not None:
                cursorMgr = getattr(app, 'cursorMgr', None)
                if cursorMgr is not None:
                    cursorMgr.attachCursor(True)
                else:
                    from gui.Scaleform.managers.Cursor import Cursor
                    Cursor.setAutoShow(True)
                app.fireEvent(ShowViewEvent(ShowViewEvent.SHOW_LOBBY, g_lobbyContext.getGuiCtx()))
            else:
                LOG_DEBUG('offline_hangar: window is None, cannot show lobby')

            try:
                SoundGroups.g_instance.enableLobbySounds(True)
            except Exception:
                pass

            Waiting.hide('enter')
        except Exception:
            LOG_CURRENT_EXCEPTION()

    g_playerEvents.onAccountShowGUI += offline_onAccountShowGUI


def _patch_connection_manager():
    from ConnectionManager import connectionManager, CONNECTION_STATUS
    connectionManager._ConnectionManager__connectionStatus = CONNECTION_STATUS.connected


def _patch_account_base():
    """Monkey-patch Account.__init__ to install FakeBase."""
    import Account
    _orig_init = Account.PlayerAccount.__init__

    def patched_init(self):
        _orig_init(self)
        if not hasattr(self, 'base') or self.base is None:
            try:
                self.base = FakeBase()
            except Exception:
                LOG_DEBUG('offline_hangar: could not set self.base')

    Account.PlayerAccount.__init__ = patched_init


def _trigger_show_gui():
    try:
        player = BigWorld.player()
        if player is None:
            LOG_DEBUG('offline_hangar: player not ready, retrying...')
            BigWorld.callback(1.0, _trigger_show_gui)
            return
        ctx = cPickle.dumps({
            'databaseID': 1,
            'serverUTC': time.time(),
            'isInRandomQueue': False,
            'isInTutorialQueue': False,
            'isLongDisconnectedFromCenter': False,
        })
        LOG_DEBUG('offline_hangar: calling showGUI')
        player.showGUI(ctx)
    except Exception:
        LOG_CURRENT_EXCEPTION()


def enter():
    global _patched
    if _patched:
        return
    _patched = True

    LOG_DEBUG('offline_hangar: starting offline hangar mode')
    try:
        _patch_connection_manager()
        _patch_personality()
        _patch_account_base()

        from OfflineMapCreator import g_offlineMapCreator
        g_offlineMapCreator.SetActive(True)

        spaceId = BigWorld.createSpace()

        props = {
            'name': 'Player',
            'serverSettings': {
                'voipDomain': '',
                'file_server': {},
                'roaming': [],
            },
        }

        entityId = BigWorld.createEntity('Account', spaceId, 0,
                                         (0.0, 0.0, 0.0),
                                         (0.0, 0.0, 0.0),
                                         props)

        BigWorld.player(BigWorld.entities[entityId])

        BigWorld.callback(2.0, _trigger_show_gui)

        LOG_DEBUG('offline_hangar: entity created, waiting for showGUI trigger')
    except Exception:
        LOG_CURRENT_EXCEPTION()
