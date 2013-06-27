#!/usr/bin/env python

import setuptools
import sysconfig

platform = sysconfig.get_platform()

if not platform.startswith('linux'):
    raise Exception('inotify is linux-specific, and does not work on %s' %
                    platform)

setuptools.setup(
    name='python-inotify',
    version='0.5',
    description='Interface to Linux inotify subsystem',
    author="Bryan O'Sullivan",
    author_email='bos@serpentine.com',
    license='LGPL',
    platforms='Linux',
    packages=['inotify'],
    url='http://www.serpentine.com/',
    ext_modules=[setuptools.extension.Extension('inotify._inotify',
                                                ['inotify/_inotify.c'])],
    setup_requires=['nose>=1.3.0'],
    tests_require=['mock>=1.0.1'],
    test_suite='nose.collector',
    )
