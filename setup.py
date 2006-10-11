#!/usr/bin/env python

import distutils.core
import distutils.util

platform = distutils.util.get_platform()

if not platform.startswith('linux'):
    raise Exception('inotify is linux-specific, and does not work on %s' %
                    platform)

distutils.core.setup(
    name='python-inotify',
    version='0.5',
    description='Interface to Linux inotify subsystem',
    author="Bryan O'Sullivan",
    author_email='bos@serpentine.com',
    license='LGPL',
    platforms='Linux',
    packages=['inotify'],
    url='http://www.serpentine.com/',
    ext_modules=[distutils.core.Extension('inotify._inotify',
                                          ['inotify/_inotify.c'])],
    )
