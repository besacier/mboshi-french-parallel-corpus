#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: split_buckeye.py
# date: Mon November 17 19:54 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""split_buckeye: split the buckeye_modified corpus by NOISE and __

"""

from __future__ import division

from collections import namedtuple
from itertools import tee, izip
import os
import os.path as path
import string
import fnmatch
import sys
from contextlib import contextmanager


# get the name of the corpus from the environmental variable CORPUS
# that can be set on the 'config' file in the root ../scripts??
# and it's activated with the bash command:
#
#   $ . config
#
# or 
#
#   $ source config
#

try:
    CORPUS = os.environ['CORPUS']   
except:                                             
    raise ValueError('CORPUS environmental variable not set bash')    


Interval = namedtuple('Interval', ['start', 'end'])
Fragment = namedtuple('Fragment', ['name', 'interval', 'mark'])
FileSet = namedtuple('FileSet', ['phn', 'wrd'])

@contextmanager
def verb(label, verbose, when_done=False):
    if verbose:
        if when_done:
            print label,
        else:
            print label
        sys.stdout.flush()
    try:
        yield
    finally:
        if verbose and when_done:
            print 'done.'
            sys.stdout.flush()


def split_by(iterable, cond):
    r = []
    for e in iterable:
        if cond(e):
            if r:
                yield r
                r = []
        else:
            r.append(e)
    if r:
        yield r


def index_by(iterable, query, key):
    for ix, element in enumerate(iterable):
        if key(element) == query:
            return ix
    raise ValueError('{0} is not in list'.format(query))


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def read_phn(fname):
    bname = path.basename(fname)
    fragments = []
    for line in open(fname):
        try:
            start, end, mark = line.strip().split(' ')
        except ValueError as e:
            print fname
            print line
            raise e
        fragments.append(Fragment(bname, Interval(start, end), mark))
    return fragments


def read_wrd(fname):
    bname = path.basename(fname)
    fragments = []
    for line in open(fname):
        splitline = line.strip().split(' ')
        start = splitline[0]
        end = splitline[1]
        wordchunk = ' '.join(splitline[2:])
        word = wordchunk.split(';')[0]
        fragments.append(Fragment(bname, Interval(start, end), word))
    return fragments


def rglob(rootdir, pattern):
    for root, _, files in os.walk(rootdir):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                yield path.join(root, basename)


def check_files_equality(phnfiles, wrdfiles):
    if not (len(phnfiles) == len(wrdfiles)):
        phnfiles = set(phnfiles.keys())
	wrdfiles = set(wrdfiles.keys())
	missing_phn = wrdfiles  - phnfiles
        missing_wrd = phnfiles  - wrdfiles
	print '--------------------'
        print 'MISSING PHONE FILES:'
        print '--------------------'
        print '\n'.join(missing_phn)
        print
        print '-------------------'
        print 'MISSING WORD FILES:'
        print '-------------------'
        print '\n'.join(missing_wrd)
        print
        print 'some files were missing'
        exit()


def gather_files(buckeye_folder):
    phnfiles = {path.splitext(path.basename(f))[0]: f
                for f in rglob(buckeye_folder, '*.phn')}
    wrdfiles = {path.splitext(path.basename(f))[0]: f
                for f in rglob(buckeye_folder, '*.wrd')}

    check_files_equality(phnfiles, wrdfiles)

    filesets = {}
    for bname, _ in phnfiles.iteritems():
        filesets[bname] = FileSet(phnfiles[bname], wrdfiles[bname])
    return filesets

def check_source(source):
    if not path.exists(source):
        print 'no such directory: {0}'.format(source)
        exit()


def check_destination(destination):
    if not path.exists(destination):
        os.makedirs(destination)
        os.makedirs(path.join(destination, 'phn'))
        os.makedirs(path.join(destination, 'wrd'))


def check_wrd_boundaries(phn_spl, wrd_spl):
    # check that all word boundaries correspond to a phone boundary
    for fragment in wrd_spl:
        try:
            index_by(phn_spl, fragment.interval.start,
                     lambda f: f.interval.start)
            index_by(phn_spl, fragment.interval.end,
                     lambda f: f.interval.end)
        except ValueError:
            # missing boundary
            return False
    return True


def process_corpus(source, destination, log, verbose):
    
    # storing the original name of phn/wrd and their directory 
    filesets = gather_files(source)
    with verb('reading phone annotation...', verbose, when_done=True):
        phn_annot = {b: read_phn(filesets[b].phn)
                     for b in sorted(filesets.keys())}

    with verb('reading word annotation...', verbose, when_done=True):
        wrd_annot = {b: read_wrd(filesets[b].wrd)
                     for b in sorted(filesets.keys())}

    # maps original fname and interval to new fname and interval
    mapping = []
    for b in sorted(filesets.keys()):
        with verb('processing {0}...'.format(b), verbose, when_done=True):
            pass

        phn_annot_split = list(split_by(phn_annot[b],
                                 lambda x: x.mark == 'SIL' in x.mark))
        #print b, len(phn_annot_split)
        # check that annotation is contiguous
        if not (all(all(x[0].interval.end == x[1].interval.start
                        for x in pairwise(a))
                    for a in phn_annot_split)):
            continue

        ix = 0
        for phn_spl in phn_annot_split:
            offset = float(phn_spl[0].interval.start)
            duration = float(phn_spl[-1].interval.end) - offset

            # find wrd split associated with this phn split
            try:
                start_ix = index_by(wrd_annot[b], phn_spl[0].interval.start,
                                    lambda f: f.interval.start)
                end_ix = index_by(wrd_annot[b], phn_spl[-1].interval.end,
                                  lambda f: f.interval.end)
            except ValueError:
                # if there is a boundary mismatch, skip this split
                continue

            wrd_spl = []
            for fragment in wrd_annot[b][start_ix:end_ix+1]:
                if fragment.mark == '__':
                    continue
                # remove punctuation and cast to lowercase
                newmark = fragment.mark.translate(string.maketrans('', ''),
                                                  string.punctuation).lower()
                # remove time offset
                newstart = '{0:.4f}'.format(float(fragment.interval.start) -
                                            offset)
                newend = '{0:.4f}'.format(float(fragment.interval.end) -
                                          offset)
                newinterval = Interval(newstart, newend)
                wrd_spl.append(Fragment(fragment.name, newinterval, newmark))

            # check that there are no zero-length words in this split
            if any(f.interval.start == f.interval.end for f in wrd_spl):
                continue

            # remove offset from phones
            old_phn_spl = phn_spl
            phn_spl = [Fragment(f.name, 
                       Interval('{0:.4f}'.format(float(f.interval.start) - offset),
                                '{0:.4f}'.format(float(f.interval.end) - offset)),
                       f.mark) for f in phn_spl]

            # check for zero-length phones
            if any(f.interval.start == f.interval.end for f in phn_spl):
                continue

            # check that all word boundaries correspond to a phone boundary
            if not check_wrd_boundaries(phn_spl, wrd_spl):
                continue

            # write out wrd file
            outfile_wrd = path.join(destination, 'wrd', b + '_{0}.wrd'.format(ix))
            with open(outfile_wrd, 'w') as fid:
                for fragment in wrd_spl:
                    fid.write('{:.4f} {:.4f} {}\n'.format(float(fragment.interval.start),
                                                   float(fragment.interval.end),
                                                   fragment.mark))

            # write out phn file
            outfile_phn = path.join(destination, 'phn', b + '_{0}.phn'.format(ix))
            with open(outfile_phn, 'w') as fid:
                for fragment in phn_spl:
                    fid.write('{:.4f} {:.4f} {}\n'.format(float(fragment.interval.start),
                                                  float(fragment.interval.end),
                                                  fragment.mark))

            mapping.append((b+'_{0}'.format(ix), 
			    phn_spl[0].interval.start, phn_spl[-1].interval.end,
			    b, 
			    old_phn_spl[0].interval.start, old_phn_spl[-1].interval.end))
            ix += 1
    if log:
        with verb('writing log...', verbose, when_done=True):
            with open(log, 'w') as fid:
                for b, start, end, dest, dest_start, dest_end in mapping:
                    fid.write('{} {:.4f} {:.4f} {}\n'.format(
                        dest, float(dest_start), float(dest_end), b)) # start, end


if __name__ == '__main__':
    import argparse
    def parse_args():
        parser = argparse.ArgumentParser(
            prog='corpus_split_noise.py',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Split the buckeye corpus by noise',
            epilog="""Example usage:

$ python corpus_split_noise.py /path/to/buckeye/ /path/to/destination/
""")
        parser.add_argument('source', metavar='SOURCE',
                            nargs=1,
                            help='location of your corpus')
        parser.add_argument('destination', metavar='DESTINATION',
                            nargs=1,
                            help='location for output')
        parser.add_argument('--log',
                            action='store',
                            dest='log',
                            default=None,
                            help='save log of transformations performed on corpus')
        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            dest='verbose',
                            default=False,
                            help='print process information')
        return vars(parser.parse_args())

    args = parse_args()
    source = args['source'][0]
    check_source(source)
    destination = args['destination'][0]
    check_destination(destination)

    log = args['log']

    verbose = args['verbose']

    process_corpus(source, destination, log, verbose)
