#!/usr/bin/env python
"""
pyf: programmers find

It's pronounced "pif".

Recursively search for files whose name matches a pattern. Optionally search
inside matched files for a supplied pattern. Patterns are Python regular
expressions.

Written because I got tired of writing:

 > find . -name '*.py' -exec egrep -l regex {} \;

The above with pyf would be:

 > pyf '\.py$' regex

or

 > pyf 'py$' regex

you don't need to match the dot preceeding py since we match the end of the
string with $

or just

 > pyf py regex

if you don't pass in a regex as the name pattern pyf assumes it is a file
extension match and adds a $ on the end.

File name patterns and the search patterns inside of files are both Python
regular expressions.

Examples:

Find files containing a regex:

 > pyf py regex

The above example will recursively find files whose name ends in py and search
for regex in the file.

Finding files which contain one thing but not another:

 > pyf html post | pyf -v -f - csrf_token

Above finds all files whose name ends in html and contain 'post' but do not
contain 'csrf_token'.

Running a command on a matched file:

 > pyf -r "sed -i '' -e 's/yajogo\.core\.debug/yajogo.core.logging/g'" 'py$' 'yajogo\.core\.debug'

Above finds py files that contain the string yajogo.core.debug and runs a sed
command on them

Printing regex matches:

 > pyf -s -m html '(\d+x\d+)'

Above will print all matches of the pattern (\d+x\d+) in files whose names
ends in .html. The -s option suppresses printing of the filename for the match. 
The -m option causes the matched regex to be printed. So, with the above you 
might get an output like this:

57x57
72x72
114x114
512x512
200x200
150x150
150x150
150x150
500x500
800x600
150x150
150x150

We could pipe the output of this command to another program. For example:

 > pyf -s -m html '(\d+x\d+)' | sort | uniq
 
Would give us a sorted and unique list of matches:

114x114
150x150
200x200
500x500
512x512
57x57
72x72
800x600

"""

from optparse import OptionParser, IndentedHelpFormatter
import os
import re
import subprocess
import sys
import traceback

class MyHelpFormatter(IndentedHelpFormatter):
    """
    Help formatter with out description re-formatting
    """

    def format_description(self, description):
        return description

def writeout(options, line):
    # encode is needed here for Python 3
    options.outfd.write(('%s\n' % line).encode())

def writerr(line, exception=None):
    if exception:
        sys.stderr.write('%s: %s\n' % (line, exception))
        sys.stderr.write(traceback.format_exc())
    else:
        sys.stderr.write(line + '\n')

def make_regex(pattern):
    if pattern:
        regexp = re.compile(r'[\.\^\$\*\+\?\{\}\\\[\]\|\(\)]')
        if not regexp.search(pattern):
            pattern = '%s$' % pattern
    return pattern

def pyfwalk(options, path, name):
    #print 'pyfwalk = %s ' % path
    files = []
    dirs = []
    name_re = re.compile(make_regex(name))
    try:
        contents = os.listdir(path)
    except Exception as e:
        writerr("Error listing: '%s'" % (path), exception=e)
        return

    for f in contents:
        # skip files starting with a dot
        if f[0] == '.':
            continue
        longname = os.path.join(path, f)
        if os.path.isdir(longname):
            if not f in ('CVS', 'RCS'):
                dirs.append(f)
        else:
            if name:
                if name_re.search(f):
                    files.append(f)
            else:
                files.append(f)
    yield(path, dirs, files)
    for d in dirs:
        longname = os.path.join(path, d)
        if not os.path.islink(longname):
            for x in pyfwalk(options, longname, name):
                yield x

def pyf_run(options, path):
    args = []
    for a in options.run.split():
        if a[0] == "'":
            a = a[1:-1]
        args.append(a)
    args.append(path)
    #print args
    try:
        p = subprocess.Popen(args)
    except Exception as e:
        writerr("Error running: '%s'" % (' '.join(args)), exception=e)
    else:
        rc = p.wait()

def print_path(options, path):
    options.didmatch = True
    if options.run:
        pyf_run(options, path)
    else:
        writeout(options, path)

def print_line(options, lnum, path, line):
    line = line.strip()
    if options.lnum:
        if options.fname:
            writeout(options, '%d: %s' % (lnum, line))
        else:
            writeout(options, '%d: %s: %s' % (lnum, path, line))
    else:
        if options.fname:
            writeout(options, '%s' % (line))
        else:
            writeout(options, '%s: %s' % (path, line))

def print_match(options, lnum, path, line, mo):
    for g in mo.groups():
        if options.lnum:
            if options.fname:
                writeout(options, '%d: %s' % (lnum, g))
            else:
                writeout(options, '%d: %s: %s' % (lnum, path, g))
        else:
            if options.fname:
                writeout(options, '%s' % (g))
            else:
                writeout(options, '%s: %s' % (path, g))

def print_result(options, lnum, path, line, lines, mo):
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
            if start < 0:
                start = 0
            for i in range(start, end):
                print_line(options, i+1, path, lines[i])
            writeout(options, '')
        elif options.matches:
            print_match(options, lnum, path, line, mo)
        elif options.lines:
            print_line(options, lnum, path, line)
    return stop

def pyf_file(options, pattern_re, path):
    try:
        fp = open(path)
    except Exception as e:
        writerr('Error opening %s' % (path), exception=e)
        return
    else:
        lines = fp.readlines()
    finally:
        fp.close()

    try:
        lnum = 0
        matched = False
        line = ''
        mo = None
        for line in lines:
            lnum += 1
            line = line.strip()
            mo = pattern_re.search(line)
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
            #print 'non-matching file'
            print_result(options, lnum, path, line, lines, mo)
    # typically from a broken pipe
    except IOError:
        sys.exit()
    except Exception as e:
        writerr('Error matching %s' % (path), exception=e)

def pyf_dir(options, pattern_re):
    if options.name:
        name_re = re.compile(make_regex(options.name))
    
    for root, dirs, files in pyfwalk(options, options.chdir, options.name):
        dbase = os.path.basename(root)
        #print 'dbase = %s' % dbase
        #print 'root = %s' % root
        #print 'dirs = %s' % dirs
        #print 'files = %s' % files
        if len(root) > 1 and len(dbase) > 0:
            if dbase[0] == '.':
                continue
        # handle printing of matching directory name
        if options.name and not options.pattern:
            for d in dirs:
                if name_re.search(d):
                    print_path(options, os.path.join(root, d))
        # search files / print file names
        for f in files:
            if f[0] == '.':
                continue
            path = os.path.join(root, f)
            if options.pattern:
                pyf_file(options, pattern_re, path)
            else:
                print_path(options, path)

def pyf_stdin(options, pattern_re):
    for path in sys.stdin.readlines():
        path = path.strip()
        pyf_file(options, pattern_re, path)

def pyf(options):
    pattern_re = None
    if options.pattern:
        pattern = options.pattern
        if options.ignore:
            pattern_re = re.compile(pattern, re.IGNORECASE)
        else:
            pattern_re = re.compile(pattern)
    if options.name == '-':
        pyf_stdin(options, pattern_re)
    else:
        pyf_dir(options, pattern_re)

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
        writerr('Error opening pager process: %s' % (' '.join(args)), exception=e)
    else:
        options.outfd = options.pager.stdin

def main():
    usage = '%prog [options] filename-pattern [search-pattern [start-directory]]'
    version = '%prog version 1.0'
    desc = __doc__.strip()
    formatter = MyHelpFormatter()

    parser = OptionParser(usage=usage, version=version, description=desc, formatter=formatter)

    parser.add_option('-c', '--context',
        type='int', dest='context',
        help='Show surrounding CONTEXT lines of line that matches. Default %default')
    parser.set_defaults(context=0)

    parser.add_option('-d', '--chdir',
        dest='chdir',
        help='Change to directory CHDIR before starting the search.')
    parser.set_defaults(chdir='.')

    parser.add_option('-e', '--regexp',
        dest='pattern',
        help='Use PATTERN as the pattern in a file; useful to protect patterns beginning with -.')

    parser.add_option('-f', '--files',
        dest='name',
        help='Match file names to pattern NAME. Note: if argument is - reads a list of files to match from stdin.')

    parser.add_option('-i', '--ignore-case',
        action='store_true', dest='ignore',
        help='Ignore case. Default %default')
    parser.set_defaults(ignore=False)

    parser.add_option('-m', '--print-matches',
        action='store_true', dest='matches',
        help='Print the matching regex group. Default %default')
    parser.set_defaults(matches=False)

    parser.add_option('-n', '--line-number',
        action='store_true', dest='lnum',
        help='Prefix the matching line with the line number. Default %default')
    parser.set_defaults(lnum=False)

    parser.add_option('-p', '--print-lines',
        action='store_true', dest='lines',
        help='Print the matching line. Default %default')
    parser.set_defaults(lines=False)

    parser.add_option('-r', '--run',
        dest='run',
        help='Run a program RUN for each matching file, passing the path name of the matching file as an argument. Ignored if the -p or -n options are given.')

    parser.add_option('-s', '--no-filename',
        action='store_true', dest='fname',
        help='Suspress printing of file name. Default %default')
    parser.set_defaults(fname=False)

    parser.add_option('-v', '--invert-match',
        action='store_true', dest='invert',
        help='Invert the sense of the match. Print non-matching files and lines. Default %default')
    parser.set_defaults(invert=False)

    parser.add_option('-N', '--no-pager',
        action='store_true', dest='nopager',
        help='Do not pipe output to PAGER when stdout it detected as a tty.')
    parser.set_defaults(nopager=False)

    (options, args) = parser.parse_args()

    argc = len(args)

    if argc < 4 and argc > 0:
        if argc == 3:
            options.name = args[0]
            options.pattern = args[1]
            options.chdir = args[2]
        elif argc == 2:
            options.name = args[0]
            options.pattern = args[1]
        elif argc == 1:
            if options.name:
                options.pattern = args[0]
            else:
                options.name = args[0]
    else:
        parser.print_help()
        sys.exit('Error: wrong number of arguments: %d' % argc)

    # set option to check if we matched
    options.didmatch = False

    # ignore run if printing lines or line numbers
    if options.lines or options.lnum:
        options.run = None

    # set up output options
    options.outfd = sys.stdout
    options.pager = None
    if not options.run and not options.nopager and sys.stdout.isatty():
        try:
            open_pager(options)
        except Exception as e:
            writerr('Error opening pager', exception=e)

    # do the match
    try:
        pyf(options=options)
    except Exception as e:
        writerr('pyf exception', exception=e)
    except KeyboardInterrupt:
        if options.pager:
            options.pager.terminate()
        writerr('\nInterrupted')
    finally:
        # tidy up and wait for pager if used
        if options.pager:
            sys.stdout.flush()
            sys.stderr.flush()
            options.outfd.flush()
            sys.stdout.close()
            sys.stderr.close()
            options.outfd.close()
            options.pager.wait()

    if options.didmatch:
        exit_status = 0
    else:
        exit_status = 1
        
    return exit_status

if __name__ == '__main__':
    es = main()
    sys.exit(es)


