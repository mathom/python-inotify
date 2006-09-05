'''Low-level interface to the Linux inotify subsystem.

The inotify subsystem provides an efficient mechanism for file status
monitoring and change notification.

This package provides the low-level inotify system call interface and
associated constants and helper functions.

For a higher-level interface that remains highly efficient, use the
inotify.watcher package.'''

from _inotify import *

procfs_path = '/proc/sys/fs/inotify'

def _read_procfs_value(name):
    def read_value():
        try:
            return int(open(procfs_path + '/' + name).read())
        except OSError, err:
            return None

    read_value.__doc__ = '''Return the value of the %s setting from /proc.

    If inotify is not enabled on this system, return None.''' % name

    return read_value

max_queued_events = _read_procfs_value('max_queued_events')
max_user_instances = _read_procfs_value('max_user_instances')
max_user_watches = _read_procfs_value('max_user_watches')
