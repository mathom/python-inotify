'''High-level interfaces to the Linux inotify subsystem.

The inotify subsystem provides an efficient mechanism for file status
monitoring and change notification.

The BasicWatcher class hides the low-level details of the inotify
interface, and provides a Pythonic wrapper around it.  It generates
events that provide somewhat more information than raw inotify makes
available.

The AutoWatcher class is more useful, as it automatically watches
newly-created directories on your behalf.'''

import _inotify as inotify
import array
import errno
import fcntl
import os
import termios


class Event(object):
    '''Derived inotify event class.

    The following fields are available:

        path: path of the directory in which the event occurred

        name: name of the directory entry to which the event occurred
        (may be None)

        fullpath: complete path at which the event occurred

        wd: watch descriptor that triggered this event

        mask: event mask'''

    __slots__ = (
        'cookie',
        'fullpath',
        'mask',
        'name',
        'path',
        'raw',
        'wd',
        )

    def __init__(self, raw, path):
        self.path = path
        self.raw = raw
        if raw.name:
            self.fullpath = path + '/' + raw.name
        else:
            self.fullpath = path

        self.wd = raw.wd
        self.mask = raw.mask
        self.cookie = raw.cookie
        self.name = raw.name
    
    def __repr__(self):
        r = repr(self.raw)
        return 'Event(path=' + repr(self.path) + ', ' + r[r.find('(')+1:]


class BasicWatcher(object):
    '''Provide a Pythonic interface to the low-level inotify API.

    Also adds derived information to events that is not available
    through the normal inotify API, such as directory names.'''

    __slots__ = (
        'fd',
        '_paths',
        '_wds',
        )

    def __init__(self):
        '''Create a new inotify instance.'''

        self.fd = inotify.init()
        self._paths = {}
        self._wds = {}

    def fileno(self):
        '''Return the file descriptor this watcher uses.

        Useful for passing to select and poll.'''

        return self.fd

    def add(self, path, mask):
        '''Add or modify a watch.

        Return the watch descriptor added or modified.'''

        path = os.path.normpath(path)
        wd = inotify.add_watch(self.fd, path, mask)
        self._paths[path] = wd, mask
        self._wds[wd] = path, mask
        return wd

    def remove(self, wd):
        '''Remove the given watch.'''

        inotify.remove_watch(self.fd, wd)
        self._remove(wd)

    def _remove(self, wd):
        path_mask = self._wds.pop(wd, None)
        if path_mask is not None:
            self._paths.pop(path_mask[0])

    def path(self, path):
        '''Return a (watch descriptor, event mask) pair for the given path.
        
        If the path is not being watched, return None.'''

        return self._paths.get(path)

    def wd(self, wd):
        '''Return a (path, event mask) pair for the given watch descriptor.

        If the watch descriptor is not valid or not associated with
        this watcher, return None.'''

        return self._wds.get(wd)
        
    def read(self, bufsize=None):
        '''Read a list of queued inotify events.

        If bufsize is zero, only return those events that can be read
        immediately without blocking.  Otherwise, block until events are
        available.'''

        events = []
        for evt in inotify.read(self.fd, bufsize):
            events.append(Event(evt, self._wds[evt.wd][0]))
            if evt.mask & inotify.IN_IGNORED:
                self._remove(evt.wd)
            elif evt.mask & inotify.IN_UNMOUNT:
                self.close()
        return events

    def close(self):
        '''Shut down this watcher.

        All subsequent method calls are likely to raise exceptions.'''

        os.close(self.fd)
        self.fd = None
        self._paths = None
        self._wds = None

    def __len__(self):
        '''Return the number of active watches.'''

        return len(self._paths)

    def __iter__(self):
        '''Yield a (path, watch descriptor, vent mask) tuple for each entry.'''

        for path, (wd, mask) in self._paths.iteritems():
            yield path, wd, mask

    def __del__(self):
        if self.fd is not None:
            os.close(self.fd)

    ignored_errors = [errno.ENOENT, errno.EPERM, errno.ENOTDIR]

    def additer(self, path, mask, onerror=None):
        '''Add or modify watches over path and its subdirectories.

        Yield each added or modified watch descriptor.

        To ensure that this method runs to completion, you must
        iterate over all of its results, even if you do not care what
        they are.  For example:

            for wd in w.walk(path, mask):
                pass

        By default, errors are ignored.  If optional arg "onerror" is
        specified, it should be a function; it will be called with one
        argument, an OSError instance.  It can report the error to
        continue with the walk, or raise the exception to abort the
        walk.'''

        # Add the IN_ONLYDIR flag to the event mask, to avoid a possible
        # race when adding a subdirectory.  In the time between the
        # event being queued by the kernel and us processing it, the
        # directory may have been deleted, or replaced with a different
        # kind of entry with the same name.

        submask = mask | inotify.IN_ONLYDIR

        for root, dirs, names in os.walk(path, topdown=False, onerror=onerror):
            for d in dirs:
                try:
                    yield self.add(root + '/' + d, submask)
                except OSError, err:
                    if onerror and err.errno not in self.ignored_errors:
                        onerror(err)
        yield self.add(path, mask)


class AutoWatcher(BasicWatcher):
    '''Watcher class that automatically watches newly created directories.'''

    __slots__ = (
        'addfilter',
        )

    def __init__(self, addfilter=None):
        '''Create a new inotify instance.

        This instance will automatically watch newly created
        directories.

        If the optional addfilter parameter is not None, it must be a
        callable that takes one parameter.  It will be called each time
        a directory is about to be automatically watched.  If it returns
        True, the directory will be watched if it still exists,
        otherwise, it will beb skipped.'''

        super(AutoWatcher, self).__init__()
        self.addfilter = addfilter

    _dir_create_mask = inotify.IN_ISDIR | inotify.IN_CREATE

    def read(self, bufsize=None):
        events = super(AutoWatcher, self).read(bufsize)
        for evt in events:
            if evt.mask & self._dir_create_mask == self._dir_create_mask:
                if self.addfilter is None or self.addfilter(evt):
                    parentmask = self._wds[evt.wd][1]
                    # See note about race avoidance via IN_ONLYDIR above.
                    mask = parentmask | inotify.IN_ONLYDIR
                    try:
                        self.add(evt.fullpath, mask)
                    except OSError, err:
                        if err.errno not in self.ignored_errors:
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
        self._iocbuf = array.array('i', [0])

    def readable(self):
        fcntl.ioctl(self.fd, termios.FIONREAD, self._iocbuf, True)
        return self._iocbuf[0]

    def __call__(self):
        return self.readable() >= self.threshold
