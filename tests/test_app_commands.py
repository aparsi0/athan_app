# -*- coding: utf-8 -*-
"""The dashboard -> daemon command channel.

The dashboard window is a separate process, so its Play buttons cannot touch
the daemon's player. They leave a file; the daemon consumes it. What matters
here is that a command fires exactly once, that a stale one never fires at all,
and that a corrupt file cannot wedge the watcher thread.

Run: python3 tests/test_app_commands.py
"""

import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Redirect the channel at a temp dir: this must never touch ~/.athan_app and
# leave a command behind for a real running daemon to act on.
_tmp = tempfile.mkdtemp()
import utils.app_paths as app_paths                       # noqa: E402
app_paths.get_config_dir = lambda: Path(_tmp)

from core import app_commands                             # noqa: E402

fails = []
def check(label, got, want):
    print(('  ok   ' if got == want else '  FAIL ') + label)
    if got != want:
        print('        got %r want %r' % (got, want)); fails.append(label)

check('nothing pending at rest', app_commands.pending(), False)
check('take() on nothing is empty', app_commands.take(), {})
app_commands.send('play_recital', reciter_id='refat', index=3)
check('a sent command is pending', app_commands.pending(), True)
cmd = app_commands.take()
check('action survives', cmd.get('action'), 'play_recital')
check('fields survive', (cmd.get('reciter_id'), cmd.get('index')), ('refat', 3))
check('taking consumes it', app_commands.pending(), False)
check('a consumed command cannot replay', app_commands.take(), {})

app_commands.send('stop_quran')
check('last write wins (not a queue)', True, True)
app_commands.send('play_mushaf', reciter_id='husr-warsh')
check('only the newest survives', app_commands.take().get('action'), 'play_mushaf')

# a stale command must not fire audio minutes later
p = app_commands.command_path()
p.write_text('{"action":"play_recital","index":0,"at":%f}' % (time.time() - 120))
check('a stale command is dropped', app_commands.take(), {})
check('and the stale file is gone', app_commands.pending(), False)

p.write_text('not json at all')
check('garbage is survivable', app_commands.take(), {})
check('garbage is cleaned up', app_commands.pending(), False)

print()
print('FAILED %d' % len(fails) if fails else 'ALL PASS')
sys.exit(1 if fails else 0)
