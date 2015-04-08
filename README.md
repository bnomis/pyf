# pyf: Programmers find

It's pronounced "pif".

```shell
pyf [options] [search-pattern [filename-pattern [start-directory]]]
```

Recursively search for files whose contents matches search-pattern.

* Optionally restrict the search to files whose name matches filename-pattern.
* Optionally chdir to start-directory before starting the search.
* Patterns are Python regular expressions.

Written because I got tired of writing:

```shell
find . -name '*.py' -exec egrep -l regex {} \;
```

The above with pyf would be:

```shell
pyf regex '\.py$'
```

or

```shell
pyf regex 'py$'
```

or just

```shell
pyf regex py
```

If you don't pass in a regex as the file name pattern, pyf assumes it is a file extension match and adds a $ on the end.

File name patterns and the search patterns inside of files are both [Python regular expressions](https://docs.python.org/3/library/re.html).

## Examples

### Find Files Containing A Regex

```shell
pyf regex
```

The above example will recursively find files and search for 'regex' in the file.

### Restrict The Search To Certain File Extensions

```shell
pyf regex py
```

The above example will recursively find files whose name ends in 'py' and search
for 'regex' in the file.

### Finding Files Which Contain One Thing But Not Another

```shell
pyf post html | pyf -v -f - csrf_token
```

Above finds all files whose name ends in 'html' and contain 'post' but do not contain 'csrf_token'.

### Running A Command On A Matched File

```shell
pyf -r "sed -i '' -e 's/yajogo\.core\.debug/yajogo.core.logging/g'" 'yajogo\.core\.debug' py
```

Above finds files with extention 'py' that contain the string 'yajogo.core.debug' and runs a sed command on them.

### Printing Regex Matches

```shell
pyf -s -m '\d+x\d+' html
```

Above will print all matches of the pattern '\d+x\d+' in files whose names ends in 'html'. The -s option suppresses printing of the filename for the match. The -m option causes the matched regex to be printed. So, with the above you might get an output like this:

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

```shell
pyf -s -m html '(\d+x\d+)' | sort | uniq
```

Would give us a sorted and unique list of matches:

    114x114
    150x150
    200x200
    500x500
    512x512
    57x57
    72x72
    800x600

## Installation

```shell
pip install pyf-programmers-find
```

## Usage

```shell
$ pyf -h
usage: pyf [options] [search-pattern [filename-pattern [start-directory]]]

pyf: programmers find

Recursively search for files whose contents matches search-pattern.
Optionally restrict the search to files whose name matches filename-pattern.
Patterns are Python regular expressions.

It's pronounced "pif".

positional arguments:
  search-pattern        Match this pattern in files.
  filename-pattern      Only search files whose name matches this pattern.
  start-directory       Change to this directory before findind and searching
                        files.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug               Turn on debug logging.
  --debug-log FILE      Save debug logging to FILE.
  -c COUNT, --context COUNT
                        Show COUNT surrounding context lines of the matches.
                        Only makes sense when printing matched lines with the
                        -p option. Default 0.
  -d START_DIRECTORY, --chdir START_DIRECTORY
                        Change to directory START_DIRECTORY before starting
                        the search. Can also be given as the third positional
                        argument.
  -e SEARCH_PATTERN, --regexp SEARCH_PATTERN
                        Use SEARCH_PATTERN as the pattern to match in a file;
                        use when defining patterns beginning with -. Can also
                        be given as the first positional argument.
  -f FILE, --file FILE  File to search for a match. Instead of recursively
                        searching all files. Can be given multiple times. If
                        argument is - reads a list of files to match from
                        stdin.
  -i, --ignore-case     Ignore case. Default False.
  -l, --line-number     Print the matching line number. Default False.
  -m, --matches         Print the matching regex group. Default False.
  -n FILENAME_PATTERN, --filename FILENAME_PATTERN
                        Recursively find files whose name matches
                        FILENAME_PATTERN. Only search in those files. Can also
                        be given as the second positional argument. Default:
                        .+
  -p, --print-lines     Print the matching line. Default False.
  -r CMD, --run CMD     Run a program CMD for each matching file, passing the
                        path name of the matching file as an argument. Ignored
                        if the -p or -l options are given.
  -s, --no-filename     Do not print the file name when printing matched
                        lines. Only makes sense with the -p option. Default
                        False.
  -v, --invert-match    Invert the sense of the match. Print non-matching
                        files and lines. Default False.
  -A, --suppress-file-access-errors
                        Do not print file/directory access errors.
  -B, --no-binary-check
                        Ignore (heuristic) binary file check, do not skip
                        probably binary files.
  -N, --no-pager        Do not pipe output to a pager when stdout it detected
                        as a tty.
  --force-pager         Always try to pipe output to a pager, do not check if
                        stdout is a tty. Ignored when running with the -r
                        option.
  --skip-dirs-pattern SKIP_DIRS_PATTERN
                        Regex of directories to skip. Default
                        '(^\..+|CVS|RCS|__pycache__)'.
  --skip-files-pattern SKIP_FILES_PATTERN
                        Regex of files to skip. Default '(^\..+|\.pyc$)'.

```