#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pyf: programmers find
# https://github.com/bnomis/pyf
# (c) Simon Blanchard

import os
import os.path
import subprocess
import sys

from .logger import debug, error, init_logging, deinit_logging
from .filetype import is_binary


# pyf stdout
def writeout(options, line):
    options.stdout.write(line + '\n')


# pyf stderr
def writerr(options, line, exception=None, set_exit_status=True):
    if set_exit_status:
        options.exit_status = 'error'
    options.stderr.write(line + '\n')
    if exception:
        error(line, exc_info=True)


def writerr_file_access(options, line, exception=None):
    if not options.suppress_file_access_errors:
        writerr(options, line, exception=exception, set_exit_status=False)


def check_file_access(options, path):
    # check file exists
    # will return true even for broken symlinks
    if not os.path.lexists(path):
        writerr_file_access(options, 'File does not exist: %s' % path)
        return False

    # double check for broken symlinks
    if os.path.islink(path):
        if not os.path.exists(path):
            writerr_file_access(options, 'Broken symlink: %s' % path)
            return False

    # check can open for read
    if os.path.isdir(path):
        if not os.access(path, os.R_OK):
            writerr_file_access(options, 'Directory is not readable: %s' % path)
            return False
    else:
        try:
            fp = open(path)
        except Exception as e:
            writerr_file_access(options, 'File is not readable: %s' % path)
            error('check_file_access: exception for %s: %s' % (path, e), exc_info=True)
            return False
        else:
            fp.close()

    return True


def pyfwalk(options, path):
    debug('pyfwalk = %s' % path)

    if not check_file_access(options, path):
        return

    try:
        contents = os.listdir(path)
    except Exception as e:
        writerr(options, "Exception listing: '%s'" % path, exception=e)
        return

    files = []
    dirs = []

    for f in contents:
        longname = os.path.join(path, f)
        if os.path.isdir(longname):
            if options.skip_dirs_pattern:
                if not options.skip_dirs_pattern_regex.search(f):
                    dirs.append(f)
                else:
                    debug('pyfwalk: skipping dir: %s' % f)
            else:
                dirs.append(f)
        else:
            if options.skip_files_pattern:
                if not options.skip_files_pattern_regex.search(f):
                    if options.filename_pattern_regex.search(f):
                        files.append(f)
                else:
                    debug('pyfwalk: skipping file: %s' % f)
            else:
                if options.filename_pattern_regex.search(f):
                        files.append(f)
                else:
                    debug('pyfwalk: skipping file: %s' % f)

    yield(path, dirs, files)
    for d in dirs:
        longname = os.path.join(path, d)
        if not os.path.islink(longname):
            for x in pyfwalk(options, longname):
                yield x


def pyf_run(options, path):
    args = []
    for a in options.run.split():
        if a[0] == "'":
            a = a[1:-1]
        args.append(a)
    args.append(path)
    debug('pyf_run: %s' % args)
    try:
        p = subprocess.Popen(args)
    except Exception as e:
        writerr(options, "Error running: '%s'" % (' '.join(args)), exception=e)
    else:
        p.wait()


def print_path(options, path):
    options.didmatch = True
    if options.run:
        pyf_run(options, path)
    else:
        writeout(options, path)


def print_line(options, lnum, path, line):
    line = line.strip()
    if options.lnum:
        if options.no_filename:
            writeout(options, '%d: %s' % (lnum, line))
        else:
            writeout(options, '%d: %s: %s' % (lnum, path, line))
    else:
        if options.no_filename:
            writeout(options, '%s' % (line))
        else:
            writeout(options, '%s: %s' % (path, line))


def print_match_group(options, lnum, path, group):
    if options.lnum:
        if options.no_filename:
            writeout(options, '%d: %s' % (lnum, group))
        else:
            writeout(options, '%d: %s: %s' % (lnum, path, group))
    else:
        if options.no_filename:
            writeout(options, '%s' % (group))
        else:
            writeout(options, '%s: %s' % (path, group))


def print_match(options, lnum, path, line, mo):
    groups = mo.groups()
    if groups:
        for g in groups:
            print_match_group(options, lnum, path, g)
    else:
        print_match_group(options, lnum, path, mo.group())


def print_result(options, lnum, path, line, lines, mo):
    not_first_time = options.didmatch
    stop = False
    options.didmatch = True
    if not options.matches and not options.lines:
        if options.lnum:
            writeout(options, '%d: %s' % (lnum, path))
        else:
            print_path(options, path)
            stop = True
    else:
        if options.context:
            start = lnum - 1 - options.context
            end = lnum + options.context
            # check we're in range at start...
            if start < 0:
                start = 0
            # ... and end
            length = len(lines)
            if end > length:
                end = length
            if not_first_time:
                # write a blank line to separate the contexts
                writeout(options, '')
            # write the lines
            for i in range(start, end):
                print_line(options, i + 1, path, lines[i])
        elif options.matches:
            print_match(options, lnum, path, line, mo)
        elif options.lines:
            print_line(options, lnum, path, line)
    return stop


def pyf_file(options, path):
    if not check_file_access(options, path):
        return

    if not options.no_binary_check:
        if is_binary(path):
            debug('pyf_file: skipping binary file: %s' % path)
            return

    try:
        fp = open(path)
    except Exception as e:
        writerr(options, 'Error opening %s' % (path), exception=e)
        return
    else:
        lines = fp.readlines()
        fp.close()

    try:
        lnum = 0
        matched = False
        line = ''
        mo = None
        for line in lines:
            lnum += 1
            line = line.strip()
            mo = options.search_pattern_regex.search(line)
            # a match?
            if mo:
                matched = True
                if not options.invert:
                    if print_result(options, lnum, path, line, lines, mo):
                        break
            elif options.invert:
                if options.lines:
                    print_result(options, lnum, path, line, lines, mo)
        # print a non-matching file
        if options.invert and (not options.lines) and (not matched):
            print_result(options, lnum, path, line, lines, mo)
    # typically from a broken pipe
    # e.g. when 'q' is typed in the pager
    # should exit
    except IOError:
        writerr(options, 'IOError exception matching %s' % path)
    except Exception as e:
        writerr(options, 'Exception matching %s' % path, exception=e)


def pyf_dir(options):
    for root, dirs, files in pyfwalk(options, options.start_directory):
        if options.exit_status == 'error':
            break

        # handle printing of matching directory name
        if options.filename_pattern and not options.search_pattern:
            for d in dirs:
                debug('dir = %s' % d)
                if options.filename_pattern_regex.search(d):
                    print_path(options, os.path.join(root, d))

        # search files / print file names
        for f in files:
            if options.exit_status == 'error':
                break

            path = os.path.join(root, f)
            if options.search_pattern:
                pyf_file(options, path)
            else:
                print_path(options, path)


def pyf_stdin(options):
    for path in options.stdin.readlines():
        if options.exit_status == 'error':
            break

        path = path.strip()
        if path:
            pyf_file(options, path)


def pyf(options):
    if options.files:
        for f in options.files:
            if options.exit_status == 'error':
                break

            if f == '-':
                pyf_stdin(options)
            else:
                pyf_file(options, f)
    else:
        pyf_dir(options)


def main(argv, stdin=None, stdout=None, stderr=None):
    from .options import parse_opts

    exit_statuses = {
        'match': 0,
        'no-match': 1,
        'error': 2,
        'not-set': -1
    }

    options = parse_opts(argv, stdin=stdin, stdout=stdout, stderr=stderr)
    if not options:
        return exit_statuses['error']

    init_logging(options)

    debug('argv = %s' % argv)
    debug('options = %s' % options)

    # do the match
    try:
        pyf(options=options)
    except KeyboardInterrupt:
        if options.pager:
            options.pager.terminate()
        writerr(options, '\nInterrupted')
    except Exception as e:
        writerr(options, 'pyf exception', exception=e)
        options.exit_status = 'error'
    finally:
        # tidy up and wait for pager if used
        if options.pager:
            sys.stdout.flush()
            sys.stderr.flush()
            options.stdout.flush()
            options.stderr.flush()
            sys.stdout.close()
            sys.stderr.close()
            options.stdout.close()
            options.stderr.close()
            options.pager.wait()

    if options.exit_status == 'not-set':
        if options.didmatch:
            options.exit_status = 'match'
        else:
            options.exit_status = 'no-match'

    deinit_logging()

    return exit_statuses[options.exit_status]


def run():
    sys.exit(main(sys.argv[1:]))


if __name__ == '__main__':
    run()

