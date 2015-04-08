# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import os
import re
import subprocess
import sys

from . import __version__

from .pyf import writerr

# match all file names
filename_pattern_default = r'.+'


def is_regex(pattern):
    # search pattern for special regex characters
    regexp = re.compile(r'[.^$*+?{}[\]|()\\]')

    if pattern:
        if regexp.search(pattern):
            return True
    return False


def make_regex(pattern):
    if pattern:
        if not is_regex(pattern):
            pattern = r'%s$' % pattern
    return pattern


def open_pager(options):
    default_pager = 'less'
    if 'PAGER' in os.environ:
        pager = os.environ['PAGER']
    else:
        pager = default_pager
    args = [pager, ]
    if pager == 'less':
        if 'LESS' not in os.environ:
            args.append('-FRSX')
    try:
        options.pager = subprocess.Popen(args, stdin=subprocess.PIPE)
    except Exception as e:
        writerr(options, 'Error opening pager process: %s' % (' '.join(args)), exception=e)
    else:
        options.stdout = options.pager.stdin


# put these string here so we can import them for testing
program_name = 'pyf'
usage_string = '%(prog)s [options] [search-pattern [filename-pattern [start-directory]]]'
version_string = '%(prog)s %(version)s' % {'prog': program_name, 'version': __version__}
description_string = '''pyf: programmers find

Recursively search for files whose contents matches search-pattern.
Optionally restrict the search to files whose name matches filename-pattern.
Patterns are Python regular expressions.

It's pronounced "pif".'''
no_pattern_error_message = 'Error: no pattern given. At least search-pattern and/or filename-pattern needed.'
regex_compile_error_message = 'Exception compiling %(type)s regex: \'%(regex)s\''


def parse_opts(argv, stdin=None, stdout=None, stderr=None):
    parser = argparse.ArgumentParser(
        prog=program_name,
        usage=usage_string,
        description=description_string,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--version',
        action='version',
        version=version_string
    )

    parser.add_argument(
        '--debug',
        dest='debug',
        action='store_true',
        default=False,
        help='Turn on debug logging.'
    )

    parser.add_argument(
        '--debug-log',
        dest='debug_log',
        default='',
        metavar='FILE',
        help='Save debug logging to FILE.'
    )

    parser.add_argument(
        '-c',
        '--context',
        default=0,
        type=int,
        dest='context',
        metavar='COUNT',
        help='Show COUNT surrounding context lines of the matches. \
        Only makes sense when printing matched lines with the -p option. Default %(default)s.'
    )

    parser.add_argument(
        '-d',
        '--chdir',
        default='.',
        dest='start_directory',
        help='Change to directory START_DIRECTORY before starting the search. \
        Can also be given as the third positional argument.'
    )

    parser.add_argument(
        '-e',
        '--regexp',
        dest='search_pattern',
        help='Use SEARCH_PATTERN as the pattern to match in a file; use when defining patterns beginning with -. \
        Can also be given as the first positional argument.'
    )

    parser.add_argument(
        '-f',
        '--file',
        dest='files',
        metavar='FILE',
        action='append',
        help='File to search for a match. Instead of recursively searching all files. \
        Can be given multiple times. If argument is - reads a list of files to match from stdin.'
    )

    parser.add_argument(
        '-i',
        '--ignore-case',
        default=False,
        action='store_true',
        dest='ignore',
        help='Ignore case. Default %(default)s.'
    )

    parser.add_argument(
        '-l',
        '--line-number',
        default=False,
        action='store_true',
        dest='lnum',
        help='Print the matching line number. Default %(default)s.'
    )

    parser.add_argument(
        '-m',
        '--matches',
        default=False,
        action='store_true',
        dest='matches',
        help='Print the matching regex group. Default %(default)s.'
    )

    parser.add_argument(
        '-n',
        '--filename',
        dest='filename_pattern',
        help='Recursively find files whose name matches FILENAME_PATTERN. Only search in those files. \
        Can also be given as the second positional argument. Default: %s' % filename_pattern_default
    )

    parser.add_argument(
        '-p',
        '--print-lines',
        default=False,
        action='store_true',
        dest='lines',
        help='Print the matching line. Default %(default)s.'
    )

    parser.add_argument(
        '-r',
        '--run',
        dest='run',
        metavar='CMD',
        help='Run a program CMD for each matching file, passing the path name of the matching file as an argument. \
        Ignored if the -p or -l options are given.'
    )

    parser.add_argument(
        '-s',
        '--no-filename',
        default=False,
        action='store_true',
        dest='no_filename',
        help='Do not print the file name when printing matched lines. Only makes sense with the -p option. Default %(default)s.'
    )

    parser.add_argument(
        '-v',
        '--invert-match',
        default=False,
        action='store_true',
        dest='invert',
        help='Invert the sense of the match. Print non-matching files and lines. Default %(default)s.'
    )

    parser.add_argument(
        '-A',
        '--suppress-file-access-errors',
        default=False,
        action='store_true',
        help='Do not print file/directory access errors.'
    )

    parser.add_argument(
        '-B',
        '--no-binary-check',
        default=False,
        action='store_true',
        help='Ignore (heuristic) binary file check, do not skip probably binary files.'
    )

    parser.add_argument(
        '-N',
        '--no-pager',
        default=False,
        action='store_true',
        dest='nopager',
        help='Do not pipe output to a pager when stdout it detected as a tty.'
    )

    parser.add_argument(
        '--force-pager',
        default=False,
        action='store_true',
        help='Always try to pipe output to a pager, do not check if stdout is a tty. Ignored when running with the -r option.'
    )

    parser.add_argument(
        '--skip-dirs-pattern',
        default='(^\..+|CVS|RCS|__pycache__)',
        help='Regex of directories to skip. Default \'%(default)s\'.'
    )

    parser.add_argument(
        '--skip-files-pattern',
        default='(^\..+|\.pyc$)',
        help='Regex of files to skip. Default \'%(default)s\'.'
    )

    parser.add_argument(
        'search-pattern',
        nargs='?',
        help='Match this pattern in files.'
    )

    parser.add_argument(
        'filename-pattern',
        nargs='?',
        help='Only search files whose name matches this pattern.'
    )

    parser.add_argument(
        'start-directory',
        nargs='?',
        help='Change to this directory before findind and searching files.'
    )

    # print('argv = %s' % argv)
    options = parser.parse_args(argv)

    sp = getattr(options, 'search-pattern', None)
    if sp:
        options.search_pattern = sp
    fp = getattr(options, 'filename-pattern', None)
    if fp:
        options.filename_pattern = fp
    sd = getattr(options, 'start-directory', None)
    if sd:
        options.start_directory = sd

    # set up i/o options
    options.stdin = stdin or sys.stdin
    options.stdout = stdout or sys.stdout
    options.stderr = stderr or sys.stderr

    # print('options = %s' % options)

    # check we have at least one of a search-pattern or filename-pattern
    if options.search_pattern:
        if not options.filename_pattern:
            options.filename_pattern = filename_pattern_default
    else:
        if not options.filename_pattern:
            parser.print_help()
            writerr(options, no_pattern_error_message)
            return None

    # compile the skip regex
    if options.search_pattern:
        flags = 0
        if options.ignore:
            flags = re.IGNORECASE
        try:
            options.search_pattern_regex = re.compile(options.search_pattern, flags)
        except Exception as e:
            msg = regex_compile_error_message % {'type': 'search-pattern', 'regex': options.search_pattern}
            writerr(options, msg, exception=e)
            return None

    try:
        options.filename_pattern_regex = re.compile(make_regex(options.filename_pattern))
    except Exception as e:
        msg = regex_compile_error_message % {'type': 'filename-pattern', 'regex': options.filename_pattern}
        writerr(options, msg, exception=e)
        return None

    if options.skip_dirs_pattern:
        try:
            options.skip_dirs_pattern_regex = re.compile(options.skip_dirs_pattern)
        except Exception as e:
            msg = regex_compile_error_message % {'type': 'skip-dirs-pattern', 'regex': options.skip_dirs_pattern}
            writerr(options, msg, exception=e)
            return None

    if options.skip_files_pattern:
        try:
            options.skip_files_pattern_regex = re.compile(options.skip_files_pattern)
        except Exception as e:
            msg = regex_compile_error_message % {'type': 'skip-files-pattern', 'regex': options.skip_files_pattern}
            writerr(options, msg, exception=e)
            return None

    # set option to check if we matched
    options.didmatch = False

    # ignore run if printing lines or line numbers
    if options.lines or options.lnum:
        options.run = None

    # use pager?
    options.pager = None
    if not options.run and not options.nopager and (options.stdout.isatty() or options.force_pager):
        try:
            open_pager(options)
        except Exception as e:
            writerr(options, 'Exception opening pager', exception=e)
            return None

    options.exit_status = 'not-set'
    return options

