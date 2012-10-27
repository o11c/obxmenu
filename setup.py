#!/usr/bin/env python
from distutils.core import setup

setup(
        name='obxmenu',
        version='0',
        description='A pipe-menu generator for the OpenBox Window Manager',
        author='Ben Longbons',
        author_email='b.r.longbons@gmail.com',
        url='https://github.com/o11c/obxmenu',
        py_modules=['obxmenu'],
        requires=['pyxdg'],
        scripts=['obxmenu'],
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        ]
)
