#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys

from .logger import init_logging, deinit_logging, error


def is_ascii(o):
    tab_feeds = (9, 10, 12, 13)
    return (o > 31 and o < 127) or (o in tab_feeds)


def is_text_ascii(data, confidence=0.7):
    data_length = len(data)
    out = []
    for d in data:
        if is_ascii(d):
            out.append(d)
    ascii_confidence = float(len(out)) / data_length
    if ascii_confidence >= confidence:
        return True
    return False


# https://en.wikipedia.org/wiki/UTF-8
def is_text_utf8(data, confidence=0.7):
    data_length = len(data)
    out = []
    i = 0
    while i < data_length:
        d = data[i]
        if is_ascii(d):
            out.append(d)
        # could be utf-8
        elif d & 0xc0 == 0xc0:
            if (i + 1 < data_length) and (d & 0xe0 == 0xc0) and (data[i + 1] & 0xc0 == 0x80):
                out.append(data[i])
                out.append(data[i + 1])
                i += 1
            elif (i + 2 < data_length) and (d & 0xf0 == 0xe0) and (data[i + 1] & 0xc0 == 0x80) and (data[i + 2] & 0xc0 == 0x80):
                out.append(data[i])
                out.append(data[i + 1])
                out.append(data[i + 2])
                i += 2
            elif (i + 3 < data_length) and (d & 0xf8 == 0xf0) and (data[i + 1] & 0xc0 == 0x80) and (data[i + 2] & 0xc0 == 0x80) and (data[i + 3] & 0xc0 == 0x80):
                out.append(data[i])
                out.append(data[i + 1])
                out.append(data[i + 2])
                out.append(data[i + 3])
                i += 3
            elif (i + 4 < data_length) and (d & 0xfc == 0xf8) and (data[i + 1] & 0xc0 == 0x80) and (data[i + 2] & 0xc0 == 0x80) and (data[i + 3] & 0xc0 == 0x80) and (data[i + 4] & 0xc0 == 0x80):
                out.append(data[i])
                out.append(data[i + 1])
                out.append(data[i + 2])
                out.append(data[i + 3])
                out.append(data[i + 4])
                i += 4
            elif (i + 5 < data_length) and (d & 0xfe == 0xfc) and (data[i + 1] & 0xc0 == 0x80) and (data[i + 2] & 0xc0 == 0x80) and (data[i + 3] & 0xc0 == 0x80) and (data[i + 4] & 0xc0 == 0x80) and (data[i + 5] & 0xc0 == 0x80):
                out.append(data[i])
                out.append(data[i + 1])
                out.append(data[i + 2])
                out.append(data[i + 3])
                out.append(data[i + 4])
                out.append(data[i + 5])
                i += 5
        i += 1
    utf8_confidence = float(len(out)) / data_length
    if utf8_confidence >= confidence:
        return True
    return False


def has_binary_signature(data):
    sigs = {
        'bzip2': bytearray([0x42, 0x5A, 0x68]),
        'gzip': bytearray([0x1F, 0x8B, 0x08]),
        'tar.z lzw': bytearray([0x1F, 0x9D]),
        'tar.z lzh': bytearray([0x1F, 0xA0]),
        'zip': bytearray([0x50, 0x4B, 0x03, 0x04]),
        'pkzip empty': bytearray([0x50, 0x4B, 0x05, 0x06]),
        'pkzip multi': bytearray([0x50, 0x4B, 0x07, 0x08]),
        '7zip': bytearray([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C]),
    }
    for k in sigs.keys():
        sig = sigs[k]
        length = len(sig)
        if data[:length] == sig:
            return True
    return False


def is_text(file, block=64, confidence=0.7):
    file_is_text = False
    try:
        with open(file, 'rb') as fp:
            data = fp.read(block)
        read_length = len(data)
        if read_length == 0:
            return False
        data = bytearray(data)

        # ascii check
        if is_text_ascii(data, confidence=confidence):
            file_is_text = True

        # utf-8 check
        elif is_text_utf8(data, confidence=confidence):
            file_is_text = True

        # binary signature check
        if file_is_text:
            file_is_text = not has_binary_signature(data)
    except Exception as e:
        error('is_text: exception for file %s: %s' % (file, e), exc_info=True)
    return file_is_text


def is_binary(file, block=64, confidence=0.7):
    return not is_text(file, block=block, confidence=confidence)


def test(f):
    if is_text(f):
        print('%s is text' % f)
    else:
        print('%s is NOT text' % f)


class Options(object):
    def __init__(self):
        self.debug = True
        self.debug_log = False


def main():
    options = Options()
    init_logging(options)
    for f in sys.argv[1:]:
        test(f)
    deinit_logging()


if __name__ == '__main__':
    main()

