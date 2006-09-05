import _inotify as inotify
import errno
import fcntl
import os
import termios

def _join(a, b):
    if a:
        if a[-1] == '/':
            return a + b
        return a + '/' + b
    return b

class Event(object):
    __slots__ = (
        'path',
        'raw',
        )

    def __init__(self, raw, path):
        self.raw = raw
        self.path = path

    def fullpath(self):
        if self.raw.name:
            return _join(self.path, self.raw.name)
        return self.path

    def __getattr__(self, key):
        return getattr(self.raw, key)
    
    def __repr__(self):
        r = repr(self.raw)
        return 'Event(path=' + repr(self.path) + ', ' + r[r.find('(')+1:]

class BasicWatcher(object):
    __slots__ = (
        'fd',
        '_paths',
        '_wds',
        )

    def __init__(self):
        self.fd = inotify.init()
        self._paths = {}
        self._wds = {}

    def fileno(self):
        return self.fd

    def add(self, path, mask):
        path = os.path.normpath(path)
        wd = inotify.add_watch(self.fd, path, mask)
        self._paths[path] = wd, mask
        self._wds[wd] = path, mask
        return wd

    def remove(self, wd):
        inotify.remove_watch(self.fd, wd)
        self._remove(wd)

    def _remove(self, wd):
        path_mask = self._wds.pop(wd, None)
        if path_mask is not None:
            self._paths.pop(path_mask[0])

    def path(self, path):
        return self._paths.get(path)

    def wd(self, wd):
        return self._wds.get(wd)
        
    def read(self, bufsize=None):
        events = []
        for evt in inotify.read(self.fd, bufsize):
            events.append(Event(evt, self._wds[evt.wd][0]))
            if evt.mask & inotify.IN_IGNORED:
                self._remove(evt.wd)
            elif evt.mask & inotify.IN_UNMOUNT:
                self.close()
        return events

    def close(self):
        os.close(self.fd)
        self.fd = None
        self._paths.clear()
        self._wds.clear()

    def __len__(self):
        return len(self._paths)

    def __iter__(self):
        for path, (wd, mask) in self._paths.iteritems():
            yield path, wd, mask

    def __del__(self):
        if self.fd is not None:
            os.close(self.fd)


class AutoWatcher(BasicWatcher):
    __slots__ = (
        'auto_add',
        )

    def __init__(self):
        super(AutoWatcher, self).__init__()

    _auto_add_ignored_errors = errno.ENOENT, errno.EPERM, errno.ENOTDIR
    _dir_mask = inotify.IN_ISDIR | inotify.IN_CREATE

    def read(self, bufsize=None):
        events = super(AutoWatcher, self).read(bufsize)
        for evt in events:
            if evt.mask & self._dir_mask == self._dir_mask:
                try:
                    parentmask = self._wds[evt.wd][1]
                    self.add(evt.fullpath(), parentmask | inotify.IN_ONLYDIR)
                except OSError, err:
                    if err.errno not in self._auto_add_ignored_errors:
                        raise
        return events


class Threshold(object):
    __slots__ = (
        'fd',
        'threshold',
        '_iocbuf',
        )

    def __init__(self, fd, threshold=1024):
        self.fd = fd
        self.threshold = threshold
        self._iocbuf = array.array(1)

    def __call__(self):
        readable = fcntl.ioctl(self.fd, termios.FIONREAD, self._iocbuf, True)
        return readable >= threshold
