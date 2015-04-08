#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import os.path
import pytest
import stat
import subprocess
import sys

if sys.version_info.major == 2:
    from StringIO import StringIO
else:
    from io import StringIO

import pyf.options
import pyf.filetype


class Cmd(object):
    def __init__(self, cmd, chdir='', indir='', stdin=None, stdout=None, stderr=None, exitcode=0):
        self.cmd = cmd
        self.chdir = chdir
        self.indir = indir
        # set and rewind stdin
        self.stdin = stdin
        if stdin:
            self.stdin = StringIO()
            for f in stdin:
                self.stdin.write(f + '\n')
            self.stdin.seek(0)
        self.stdout = stdout
        if stdout:
            if chdir:
                self.stdout = []
                for o in stdout:
                    self.stdout.append(os.path.join(chdir, o))
            elif indir:
                self.stdout = []
                for o in stdout:
                    self.stdout.append(os.path.join(indir, o))
        self.stderr = stderr
        self.exitcode = exitcode

    def __str__(self):
        return self.cmd

    def argv(self):
        args = []
        if self.chdir:
            args.extend(['-d', self.chdir])
        args.extend(self.cmd.split())
        return args

    def cmdline(self):
        args = ['pyf']
        args.extend(self.argv())
        return args

    def run(self):
        rval = Cmd(self.cmd)
        argv = self.argv()
        stdout = StringIO()
        stderr = StringIO()
        rval.exitcode = pyf.pyf.main(argv, stdin=self.stdin, stdout=stdout, stderr=stderr)
        stdout_value = stdout.getvalue()
        stderr_value = stderr.getvalue()
        if stdout_value:
            rval.stdout = stdout_value.strip().split('\n')
        if stderr_value:
            rval.stderr = stderr_value.strip().split('\n')
        stdout.close()
        stderr.close()
        if self.stdin:
            self.stdin.close()
        return rval

    def run_as_process(self):
        rval = Cmd(self.cmd)
        try:
            cmd = self.cmdline()
            os.environ['COVERAGE_PROCESS_START'] = '1'
            env = os.environ.copy()
            env['COVERAGE_FILE'] = '.coverage.%s' % (self.cmd.replace('/', '-').replace(' ', '-'))
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        except Exception as e:
            pytest.fail(msg='Cmd: run: exception running %s: %s' % (cmd, e))
        else:
            stdout, stderr = p.communicate()
            if stdout:
                rval.stdout = stdout.decode().strip().split('\n')
            if stderr:
                rval.stderr = stderr.decode().strip().split('\n')
            rval.exitcode = p.wait()
        return rval


some_bad_option = '--some-bad-option'
pyf_usage_string_expanded = 'usage: %s' % (pyf.options.usage_string % {'prog': pyf.options.program_name})
some_bad_option_error_msg = '%(prog)s: error: unrecognized arguments: %(option)s' % {'prog': pyf.options.program_name, 'option': some_bad_option}

bad_regex = '*\.txt$'

cmds = [
    Cmd('one', chdir='tests/data/simple', stdout=['01.txt', '02.txt', '03.txt']),
    
    Cmd('-l -d tests/data/simple one', stdout=[
        '1: tests/data/simple/01.txt',
        '1: tests/data/simple/02.txt',
        '1: tests/data/simple/03.txt']),
    Cmd('-p -s -l -d tests/data/simple one', stdout=[
        '1: one',
        '1: one',
        '1: one']),
    Cmd('-p -s -d tests/data/simple one', stdout=[
        'one',
        'one',
        'one']),
    Cmd('two', chdir='tests/data/simple', stdout=['02.txt', '03.txt']),
    Cmd('three', chdir='tests/data/simple', stdout=['03.txt']),
    Cmd('-v three', chdir='tests/data/simple', stdout=['01.txt', '02.txt']),
    Cmd('-i OnE', chdir='tests/data/simple', stdout=['01.txt', '02.txt', '03.txt']),
    Cmd('-e t.r.e', chdir='tests/data/simple', stdout=['03.txt']),
    Cmd('four', chdir='tests/data/simple', exitcode=1),
    Cmd('one --debug --debug-log=debug.log', chdir='tests/data/simple', stdout=['01.txt', '02.txt', '03.txt']),
    Cmd('one txt', chdir='tests/data/simple', stdout=['01.txt', '02.txt', '03.txt']),
    Cmd('-d tests/data/simple one txt', indir='tests/data/simple', stdout=['01.txt', '02.txt', '03.txt']),
    Cmd('-d tests/data -n simple', stdout=['tests/data/simple']),
    Cmd('-d tests/data a-deeply-nested-file', stdout=['tests/data/dir01/dir02/dir03/dir04/a-deeply-nested-file']),
    Cmd('three txt tests/data/simple', indir='tests/data/simple', stdout=['03.txt']),
    Cmd('', stderr=[pyf.options.no_pattern_error_message], exitcode=2),

    # printing matches
    Cmd('-p one', chdir='tests/data/simple', stdout=['01.txt: one', '02.txt: one', '03.txt: one']),
    Cmd('-d tests/data/simple -l -p one', stdout=['1: tests/data/simple/01.txt: one', '1: tests/data/simple/02.txt: one', '1: tests/data/simple/03.txt: one']),
    Cmd('-d tests/data/simple -l one', stdout=['1: tests/data/simple/01.txt', '1: tests/data/simple/02.txt', '1: tests/data/simple/03.txt']),

    # running a command
    Cmd('-d tests/data/simple -r basename one'),

    # bad regex
    Cmd('-e %s' % bad_regex, stderr=[pyf.options.regex_compile_error_message % {'type': 'search-pattern', 'regex': bad_regex}], exitcode=2),
    Cmd('-n %s' % bad_regex, stderr=[pyf.options.regex_compile_error_message % {'type': 'filename-pattern', 'regex': bad_regex}], exitcode=2),
    Cmd('--skip-dirs-pattern %s one' % bad_regex, stderr=[pyf.options.regex_compile_error_message % {'type': 'skip-dirs-pattern', 'regex': bad_regex}], exitcode=2),
    Cmd('--skip-files-pattern %s one' % bad_regex, stderr=[pyf.options.regex_compile_error_message % {'type': 'skip-files-pattern', 'regex': bad_regex}], exitcode=2),

    # file access
    Cmd('-d tests/inaccessible-files one',
        stdout=['tests/inaccessible-files/readable-file.txt'],
        stderr=[
            'File is not readable: tests/inaccessible-files/01.txt',
            'Broken symlink: tests/inaccessible-files/dangling-symlink',
            'Directory is not readable: tests/inaccessible-files/unreadable-directory'
        ],
        exitcode=0),
    Cmd('-A -d tests/inaccessible-files one', stdout=['tests/inaccessible-files/readable-file.txt'], exitcode=0),
    Cmd('-f some-non-existent-file one', stderr=['File does not exist: some-non-existent-file'], exitcode=1),

    # specify files to search
    Cmd('-f tests/data/simple/01.txt one', stdout=['tests/data/simple/01.txt']),
    Cmd('-f tests/data/simple/02.txt one', stdout=['tests/data/simple/02.txt']),
    Cmd('-f tests/data/simple/01.txt two', exitcode=1),
    Cmd('-f - one', stdin=['tests/data/simple/01.txt', 'tests/data/simple/02.txt'], stdout=['tests/data/simple/01.txt', 'tests/data/simple/02.txt']),

    # matching groups
    Cmd("-d tests/data/complex -l -m \d+x\d+", stdout=[
        '1: tests/data/complex/sizes.txt: 57x57',
        '2: tests/data/complex/sizes.txt: 72x72',
        '3: tests/data/complex/sizes.txt: 114x114',
        '4: tests/data/complex/sizes.txt: 512x512',
        '5: tests/data/complex/sizes.txt: 200x200',
        '6: tests/data/complex/sizes.txt: 150x150',
        '7: tests/data/complex/sizes.txt: 150x150',
        '8: tests/data/complex/sizes.txt: 150x150',
        '9: tests/data/complex/sizes.txt: 500x500',
        '10: tests/data/complex/sizes.txt: 800x600',
        '11: tests/data/complex/sizes.txt: 150x150',
        '12: tests/data/complex/sizes.txt: 150x150',
    ]),
    Cmd("-d tests/data/complex -m \d+x\d+", stdout=[
        'tests/data/complex/sizes.txt: 57x57',
        'tests/data/complex/sizes.txt: 72x72',
        'tests/data/complex/sizes.txt: 114x114',
        'tests/data/complex/sizes.txt: 512x512',
        'tests/data/complex/sizes.txt: 200x200',
        'tests/data/complex/sizes.txt: 150x150',
        'tests/data/complex/sizes.txt: 150x150',
        'tests/data/complex/sizes.txt: 150x150',
        'tests/data/complex/sizes.txt: 500x500',
        'tests/data/complex/sizes.txt: 800x600',
        'tests/data/complex/sizes.txt: 150x150',
        'tests/data/complex/sizes.txt: 150x150',
    ]),
    Cmd("-d tests/data/complex -s -m \d+x\d+", stdout=[
        '57x57',
        '72x72',
        '114x114',
        '512x512',
        '200x200',
        '150x150',
        '150x150',
        '150x150',
        '500x500',
        '800x600',
        '150x150',
        '150x150',
    ]),
    Cmd("-d tests/data/complex -s -l -m \d+x\d+", stdout=[
        '1: 57x57',
        '2: 72x72',
        '3: 114x114',
        '4: 512x512',
        '5: 200x200',
        '6: 150x150',
        '7: 150x150',
        '8: 150x150',
        '9: 500x500',
        '10: 800x600',
        '11: 150x150',
        '12: 150x150',
    ]),
    Cmd("-d tests/data/complex -s -m (\d+x\d+)", stdout=[
        '57x57',
        '72x72',
        '114x114',
        '512x512',
        '200x200',
        '150x150',
        '150x150',
        '150x150',
        '500x500',
        '800x600',
        '150x150',
        '150x150',
    ]),

    # contexts
    Cmd('-d tests/data/context -p -c 3 five', stdout=[
        'tests/data/context/context.txt: two',
        'tests/data/context/context.txt: three',
        'tests/data/context/context.txt: four',
        'tests/data/context/context.txt: five',
        'tests/data/context/context.txt: six',
        'tests/data/context/context.txt: seven',
        'tests/data/context/context.txt: eight',
    ]),
    Cmd('-d tests/data/context -p -s -c 3 five', stdout=[
        'two',
        'three',
        'four',
        'five',
        'six',
        'seven',
        'eight',
    ]),
    Cmd('-d tests/data/context -p -s -l -c 3 five', stdout=[
        '2: two',
        '3: three',
        '4: four',
        '5: five',
        '6: six',
        '7: seven',
        '8: eight',
    ]),
    Cmd('-d tests/data/context -p -s -c 10 five', stdout=[
        'one',
        'two',
        'three',
        'four',
        'five',
        'six',
        'seven',
        'eight',
        'nine',
        'ten',
        'nine',
        'eight',
        'seven'
    ]),
    Cmd('-d tests/data/context -p -s -c 3 nine', stdout=[
        'six',
        'seven',
        'eight',
        'nine',
        'ten',
        'nine',
        'eight',
        '',
        'eight',
        'nine',
        'ten',
        'nine',
        'eight',
        'seven'
    ]),

    # chinese
    Cmd('-d tests/data/chinese 你好', stdout=['tests/data/chinese/chinese.txt']),

]

cmds_as_process = [
    # argparse calls sys.exit() (grrr!) so we need to test argument errors in a process
    Cmd(some_bad_option,
        stderr=[pyf_usage_string_expanded, some_bad_option_error_msg],
        exitcode=2),
    Cmd('--force-pager one', chdir='tests/data/simple', stdout=['01.txt', '02.txt', '03.txt']),
    
]


@pytest.fixture(scope='module')
def inaccessible_files():
    # make dangling symlink
    slink = 'tests/inaccessible-files/dangling-symlink'
    if not os.path.lexists(slink):
        os.symlink('02.txt', slink)
    # make unreadable directory
    udir = 'tests/inaccessible-files/unreadable-directory'
    if not os.path.exists(udir):
        os.mkdir(udir)
    # make files unreadable
    unreadable_files = [
        'tests/inaccessible-files/01.txt',
        udir
    ]
    all_read = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    for f in unreadable_files:
        statinfo = os.stat(f)
        os.chmod(f, statinfo.st_mode & ~all_read)


@pytest.mark.usefixtures('inaccessible_files')
class TestCmd(object):
    @pytest.mark.parametrize('cmd', cmds)
    def test_cmd(self, cmd):
        r = cmd.run()
        assert r.stderr == cmd.stderr
        assert r.stdout == cmd.stdout
        assert r.exitcode == cmd.exitcode

    @pytest.mark.parametrize('cmd', cmds_as_process)
    def test_cmd_as_process(self, cmd):
        r = cmd.run_as_process()
        assert r.stderr == cmd.stderr
        assert r.stdout == cmd.stdout
        assert r.exitcode == cmd.exitcode


def make_filelist():
    # the starting directory to make a list of files to check
    #start_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    start_dir = 'tests'
    
    filelist = []
    for dpath, dirs, files in os.walk(start_dir):
        for f in files:
            fn = os.path.join(dpath, f)
            if os.path.exists(fn):
                statinfo = os.stat(fn)
                if statinfo.st_size > 0:
                    filelist.append(fn)
    return filelist

class TestFileType(object):
    def file_is_text(self, file):
        try:
            cmd = ['file', file]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            pytest.fail(msg='file_is_text: exception running %s: %s' % (cmd, e))
        else:
            stdout, stderr = p.communicate()
            p.wait()
            if stdout:
                stdout = stdout.decode().strip()
                if stdout.find('text') != -1:
                    return True
        return False

    @pytest.mark.parametrize('afile', make_filelist())
    def test_file_type(self, afile):
        file_is_text = self.file_is_text(afile)
        is_text = pyf.filetype.is_text(afile)
        assert file_is_text == is_text


if __name__ == '__main__':
    pytest.main()


