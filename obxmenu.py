# Copyright 2012 Ben Longbons
# Licensed under the GNU GPL, version 3 or later

from __future__ import print_function

import sys
import os

import xdg.Menu

def help(exe):
    print('Usage: %s {--pipe|--static} [--write] [--reconfigure]' % exe)
    print('Use --pipe for a dynamic menu, or --static for a static one')
    print('Use --write to write to ~/.config/openbox/menu.xml')
    print('Use --reconfigure to update a running instance of openbox')
    print('Note that --pipe --write is different than --pipe')
    print('')
    print('If you just want it to work, do:')
    print('%s --pipe --write --reconfigure' % exe)

def main(argv):
    exe = argv[0]
    args = argv[1:]

    if '--help' in args:
        help(exe)
        sys.exit()

    static = '--static' in args
    pipe = '--pipe' in args
    write = '--write' in args
    reconfigure = '--reconfigure' in args

    config_file = os.path.expanduser('~/.config/openbox/menu.xml')

    if write:
        # does not change stdout for subprocess
        sys.stdout = open(config_file, 'w')

    if static:
        if pipe:
            exit('Must specify only one of --static and --pipe')
        generate_static()
    elif pipe:
        if write:
            generate_pipe_instructions()
        else:
            generate_pipe_contents()
    else:
        if not reconfigure:
            exit('Must specify one of --static and --pipe')
    if reconfigure:
        os.execvp('openbox', ['openbox', '--reconfigure'])

def generate_static():
    print('<?xml version="1.0" encoding="UTF-8"?>')
    print('<openbox_menu xmlns="http://openbox.org/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://openbox.org/">')
    print('    <menu id="root-menu" label="obxmenu">')
    generate_menu(xdg.Menu.parse(), 2)
    print('    </menu>')
    print('</openbox_menu>')

def generate_pipe_instructions():
    print('<?xml version="1.0" encoding="UTF-8"?>')
    print('<openbox_menu xmlns="http://openbox.org/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://openbox.org/">')
    print('    <menu id="root-menu" label="obxmenu" execute="obxmenu --pipe" />')
    print('</openbox_menu>')

def generate_pipe_contents():
    print('<openbox_pipe_menu>')
    generate_menu(xdg.Menu.parse(), 1)
    print('</openbox_pipe_menu>')

def generate_menu(menu, level):
    for entry in menu.Entries:
        if isinstance(entry, xdg.Menu.Menu):
            print('    ' * level + str(entry))
            generate_menu(entry, level+1)
        elif isinstance(entry, xdg.Menu.MenuEntry):
            print('    ' * level + str(entry))
        else:
            print('____' * level + str(entry))
