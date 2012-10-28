# Copyright 2012 Ben Longbons
# Licensed under the GNU GPL, version 3 or later

from __future__ import print_function

import sys
import os
import shlex
import traceback
import pipes

import xdg.Menu

# http://standards.freedesktop.org/menu-spec/menu-spec-latest.html
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html

class InvalidXdgExecEror(Exception):
    pass

def xdg_exec_split(line, name, icon, desktop_file, RESERVED=' \t\n"\'\\><~|&;$*?#()`', BACKSLASH='"`$\\'):
    line = line.strip()
    ll = len(line)
    s = ''
    i = 0
    while i < ll:
        c = line[i]
        if c < ' ' or c > '~':
            raise InvalidXdgExecEror('not ascii')
        elif c == ' ':
            if s: # allow multiple adjacent spaces
                yield s
                s = ''
        elif c == '"':
            # currently allowing quotes in places other than begin and end,
            # is this correct?
            i += 1
            while line[i] != '"':
                c = line[i]
                if c == '\\':
                    i += 1
                    c = line[i]
                    if c not in BACKSLASH:
                        raise InvalidXdgExecEror('backslash: ' + c)
                elif c in BACKSLASH:
                    raise InvalidXdgExecEror('no backslash: ' + c)
                s += c
                i += 1
            i += 1
        elif c in RESERVED:
            raise InvalidXdgExecEror('reserved character: ' + c)
        elif c == '%':
            f = line[i+1]
            if f == '%':
                s += '%'
            elif f == 'F' or f == 'U':
                if s or (i+1 < ll and line[i+1] != ' '):
                    raise InvalidXdgExecEror('%F or %U not own argument')
            elif f in 'fudDnNvm':
                pass # file, url, and deprecated arguments just get removed
            elif f == 'i':
                if s:
                    # only place I raise that is not mentioned in the spec
                    raise InvalidXdgExecEror('don\'t know how to handle %i not in own argument')
                if icon:
                    yield '--icon'
                    yield icon
            elif f == 'c':
                s += name
            elif f == 'k':
                # desktop_file can be empty, should I do this?
                # if not s and not desktop_file and (i+1 == ll or line[i+1] == ' '):
                #     yield ''
                s += desktop_file
            else:
                raise InvalidXdgExecEror('field code: ' + line[i+1])
        else:
            s += c
        i += 1
    yield s

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

def menu2str(entry):
    return '%s: inline? %s, Show? %s, Visible? %s' % (
            entry.Name,
            entry.Layout.inline,
            entry.Show,
            entry.Visible,
    )
def entry2str(entry):
    return '%s: Show? %s, Categories: %s' % (
        entry.DesktopEntry,
        entry.Show,
        entry.Categories,
    )

def generate_menu(menu, level):
    for entry in menu.Entries:
        if isinstance(entry, xdg.Menu.Menu):
            # TODO: handle these?
            # inline = entry.Layout.inline == 'true'
            # icon = entry.getIcon() # just name, not path
            # print('    ' * level + '<menu id="%s" icon="%s" label="%s">' % (entry.Name, icon, entry.Name))
            print('    ' * level + '<menu id="%s" label="%s">' % (entry.Name, entry.Name))
            generate_menu(entry, level+1)
            print('    ' * level + '</menu>')
        elif isinstance(entry, xdg.Menu.MenuEntry):
            de = entry.DesktopEntry
            exec_ = de.getExec()
            name = str(de)
            assert name
            icon = de.getIcon()
            desktop_file = de.filename

            try:
                ex = list(xdg_exec_split(exec_, name, icon, desktop_file))
            except Exception as e:
                print('    ' * level + '<separator label=": %s has invalid Exec"/>' % str(de))
                print('    ' * level + '<!-- Exec=%s -->' % exec_)
                print('    ' * level + '<!-- caught %r -->' % e)
                # traceback.print_exc()
            else:
                if de.getTerminal():
                    ex = ['xterm', '-e'] + ex
                exs = ' '.join(pipes.quote(el) for el in ex)
                print('    ' * level + '<item label="%s" icon="%s"><action name="Execute"><execute>%s</execute></action></item>' % (str(de), icon, exs))
        else:
            print('    ' * level + '<!-- Unknown entry type: ' + str(type(entry)) + ': ' + str(entry))
