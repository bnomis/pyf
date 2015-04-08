#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import re

# simple check if the regex matching pattern works how we think
# it check that the pattern looks like a regex
# not if it is a valid regex

def is_regex(pattern):
    # search pattern for special regex characters
    regexp = re.compile(r'[.^$*+?|\\{}[\]()]')
    
    if pattern:
        if regexp.search(pattern):
            return True
    return False


regexes = [
    'abc',
    '.abc',
    '^abc',
    'abc$',
    'abc*',
    'abc+',
    'abc?',
    'abc|',
    'abc\\',
    'abc{',
    'abc}',
    '[abc',
    'abc]',
    '(abc',
    'abc)',
    
]

for r in regexes:
    v = is_regex(r)
    if v:
        print("'%s' is a regex" % r)
    else:
        print("'%s' is NOT a regex" % r)

    