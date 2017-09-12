#!/usr/bin/env python

from itertools import chain, izip_longest
import itertools
import os
import os.path as path
import glob
from collections import namedtuple, Counter, defaultdict
import random
from random import Random
import argparse
from io import open # fix the unicode, it will open all files as utf-8 
from math import ceil
from operator import itemgetter

import numpy as np
from joblib import Parallel, delayed

import tde
from tde.util.reader import tokenlists_to_corpus
from tde.util.functions import grouper as grouper_
from tde.data.interval import Interval
from tde.data.fragment import FragmentToken
from tde.goldset import extract_gold_fragments


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
    raise ValueError('CORPUS environmental variable not set bash for scripts/prep_gold.py')    


try: 
    SPK_SEG = os.environ['SPK_SEG']
except:
    raise ValueError('SPK_SEG environmental variable not set bash')

try:
    N_FRAG = int(os.environ['N_FRAG'])
except:
    raise ValueError('N_FRAG environmental variable not set bash')

try:
    N_SHUFFLES = int(os.environ['N_SHUFFLES'])
except: 
    raise ValueError('N_SHUFFLES environmental variable not set bash')


# make the selection of data no so random (dev, reproductiblity)
# however in parallel processes the state of the generator is shared and 
# between processes giving non reproducible results .. 
# TODO: use random.Random?
random.seed(1)

FileSet = namedtuple('FileSet', ['phn', 'wrd'])

# from http://stackoverflow.com/questions/434287/what-is-the-most-pythonic-way-to-iterate-over-a-list-in-chunks
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)

def write_counts(phn_fragments, wrd_fragments, outdir):
    words = Counter(f.mark for f in chain.from_iterable(wrd_fragments))
    phones = Counter(f.mark for f in chain.from_iterable(phn_fragments))

    with open(path.join(outdir, 'wrd.stats'), 'w') as fid:
        fid.write('\n'.join('{0} {1}'.format(k, v)
                            for k, v in words.iteritems()))
    with open(path.join(outdir, 'phn.stats'), 'w') as fid:
        fid.write('\n'.join('{0} {1}'.format(k, v)
                            for k, v in phones.iteritems()))

def load_annot(fname):
    fs = []
    bname = path.splitext(path.basename(fname))[0]
    for line in open(fname):
        start, stop, mark = line.strip().split(' ')
        interval = Interval(round(float(start), 2), round(float(stop), 2))
        fragment = FragmentToken(bname, interval, mark)
        fs.append(fragment)
    return fs

def is_contiguous(tokens, name_):
    return all(f1.interval.end == f2.interval.start
               for f1, f2 in zip(tokens, tokens[1:]))

def load_filesets(phndir, wrddir):
    fragments = []
    for phn_file in glob.iglob(path.join(phndir, '*.phn')):
        bname = path.splitext(path.basename(phn_file))[0]
        wrd_file = path.join(wrddir, bname+'.wrd')
        phn_fragments = load_annot(phn_file)
        wrd_fragments = load_annot(wrd_file)
        
        if is_contiguous(phn_fragments, 'phn') and is_contiguous(wrd_fragments, 'wrd'):
            fragments.append(FileSet(phn_fragments, wrd_fragments))

    return fragments

def load(phndir, wrddir, outdir):
    fragments = load_filesets(phndir, wrddir)
    phn_fragments, wrd_fragments = zip(*fragments)

    # remove "sil", "sp", "SIL"
    phn_fragments = [[f for f in fl if not f.mark in ['sil', 'sp', 'SIL']]
                     for fl in phn_fragments]
    wrd_fragments = [[f for f in fl if not f.mark in ['sil', 'sp', 'SIL']]
                     for fl in wrd_fragments]

    intervals_from_phn = {fl[0].name: Interval(fl[0].interval.start,
                                               fl[-1].interval.end)
                          for fl in phn_fragments}
    intervals_from_wrd = {fl[0].name: Interval(fl[0].interval.start,
                                               fl[-1].interval.end)
                          for fl in wrd_fragments}
    
    # check that the total file intervals match up
    assert (intervals_from_phn == intervals_from_wrd)
    
    # check that each word corresponds to a sequence of phones exactly
    wrd_corpus = tokenlists_to_corpus(wrd_fragments)
    phn_corpus = tokenlists_to_corpus(phn_fragments)
    
    # (will raise exception if exact match is not found)
    (phn_corpus.tokens_exact(name, interval)
     for name, interval, mark in wrd_corpus.iter_fragments())

    # write concatenated phn, wrd files
    with open(path.join(outdir, '{}.phn'.format(CORPUS)), 'w') as fp:
        for fragment in sorted(chain.from_iterable(phn_fragments),
                               key=lambda x: (x.name, x.interval.start)):
            fp.write(u'{0} {1:.4f} {2:.4f} {3}\n'.format(
                fragment.name, fragment.interval.start, fragment.interval.end,
                fragment.mark))
    
    with open(path.join(outdir, '{}.wrd'.format(CORPUS)), 'w') as fp:
        for fragment in sorted(chain.from_iterable(wrd_fragments),
                               key=lambda x: (x.name, x.interval.start)):
            fp.write(u'{0} {1:.4f} {2:.4f} {3}\n'.format(
                fragment.name, fragment.interval.start, fragment.interval.end,
                fragment.mark))
    
    with open(path.join(outdir, '{}.split'.format(CORPUS)), 'w') as fp:
        for name, interval in sorted(intervals_from_phn.iteritems()):
            fp.write(u'{0} {1:.4f} {2:.4f}\n'.format(name,
                                                    interval.start,
                                                    interval.end))

    return phn_fragments, wrd_fragments

def generate_class_file(phn_, outdir, n):
    '''wrap the creation of class file to be able to make this proc parallel'''
    print('doing class {}'.format(n))
    pairs = extract_gold_fragments(phn_, verbose=False, n_jobs=1)
    classes = defaultdict(set)
    for fragment in chain.from_iterable(pairs):
        classes[fragment.mark].add(fragment)
    
    with open(path.join(outdir, '{}.classes.{}'.format(CORPUS,n)), 'w') as fp:
        for ix, mark in enumerate(sorted(classes.keys())):
            fp.write(u'Class {0} [{1}]\n'.format(ix, ','.join(mark)))
            for fragment in sorted(classes[mark],
                                   key=lambda x: (x.name,
                                                  x.interval.start)):
                fp.write(u'{0} {1:.4f} {2:.4f}\n'.format(
                    fragment.name, fragment.interval.start, fragment.interval.end))
            fp.write(u'\n')  
    
    print('finished class {}'.format(n))


class get_list_elements():
    '''get_list_elements: it is a generator that
    produce a list of random elements shuffled indexes in groups.
    an example use:

    # return a list of indexes for a-z list in groups of 2 elements and shuffled 5 times
    import string
    text_ = list(string.lowercase)
    ge = get_elements(len(text_), 5, 2)
    for d, n, r in r:
        print itemgetter(*d)(text_), n, r
    '''
    def __init__(self, len_data, n_shuffles, n_groups):
        self.dng = np.random.RandomState(42)
        self.len_data = len_data
        self.n_shuffles = n_shuffles
        self.n_groups = n_groups
        self.n_calls = 0
        self.done_shuffles = 0
        self._shuffle()

    def _shuffle(self):
        self.idx = np.arange(self.len_data)
        self.dng.shuffle(self.idx)
        self.idx = grouper(self.idx, self.n_groups, fillvalue=self.idx[0])
        self.done_shuffles+=1

    def __iter__(self):
        return self

    def next(self): # works in python 2.7 ... for higher is __next__(self)
        try:
            result = self.idx.next()
        except StopIteration:
            if (self.done_shuffles < self.n_shuffles):
                self._shuffle()
                result = self.idx.next()
            else:
                raise StopIteration
        self.n_calls += 1
        return self.done_shuffles, self.n_calls, result

def make_gold(phn_fragments, outdir, n_jobs, verbose):
    ''' make the {CORPUS}.classes 
    '''
    ## single job  
    ##generate_class_file(phn_fragments, outdir, 1)

    # Not all 100% of the space of gold ngrams are searched, 
    # but with the following random optimization I could found around 95% of the ngrams (ZSC2017)
    # the n_frags is the size of the utterances by array, the utterances are shuffled before (n_shuffles times)
    # to get different utterance comparissons. General the bigger the corpus bigger the n_frags and the n_shuffles 
    n_frag = N_FRAG; n_shuffles = N_SHUFFLES # to bootstrap the results ... n_shuffles between 10~20 gives acceptable results     
    if n_jobs > 1: # do it in parallel
        ge = get_list_elements(len(phn_fragments), n_shuffles, n_frag)
        Parallel(n_jobs=n_jobs)(delayed(generate_class_file)(itemgetter(*idx)(phn_fragments), outdir, n)
            for _, n, idx in ge)
    else: # without joblib in a single thread 
        for n, phn_ in enumerate(grouper(phn_fragments, n_frag, fillvalue=phn_fragments[0])):
            generate_class_file(phn_, outdir, n)

       
def split_em(phn_fragments, outdir):
    intervals = {f[0].name: Interval(f[0].interval.start, f[-1].interval.end)
                 for f in phn_fragments}
    
    group_size = 1000
    len_intervals = len(intervals.items())
    num_samples = len_intervals - len_intervals % group_size
    names_cross = list(grouper_(group_size, random.sample(intervals.items(), 
        num_samples)))
    intervals_per_speaker = defaultdict(set)
    for fname, interval in intervals.iteritems():
        # change this part to fit the new filenames and the name is the speaker
        #intervals_per_speaker[fname.split('_')[2]].add((fname, interval))
        # for C2017 MANDARIN corpus each file is a different speaker
        intervals_per_speaker[fname.split('_')[0]].add((fname, interval))
        #exec 'intervals_per_speaker[fname[{}]].add((fname, interval))'.format(SPK_SEG) in globals(), locals()


    names_within = [list(v)
                    for v in intervals_per_speaker.values()
                    if len(v) > 200]

    with open(path.join(outdir, '{}.intervals.cross'.format(CORPUS)), 'w') as fp:
        fp.write(u'\n\n'.join(u'\n'.join(u'{0} {1:.4f} {2:.4f}'.format(
            name, interval.start, interval.end)
                                       for name, interval in sorted(ns))
                             for ns in names_cross))

    with open(path.join(outdir, '{}.intervals.within'.format(CORPUS)), 'w') as fp:
        fp.write(u'\n\n'.join(
                 u'\n'.join(
                 u'{0} {1:.4f} {2:.4f}'.format(name, interval.start, interval.end)
                     for name, interval in sorted(ns))
                 for ns in names_within))
        
        # fp.write('\n\n'.join('\n'.join(sorted(ns)) for ns in names_within))

    fnames = list(set(f[0].name for f in phn_fragments))
    with open(path.join(outdir, '{}.files'.format(CORPUS)), 'w') as fp:
        fp.write(u'\n'.join(sorted(fnames)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='prep_gold.py',
        formatter_class=argparse.RawTextHelpFormatter,
        description='Prep the corpus for track 2')
    parser.add_argument('phndir', metavar='PHNDIR', nargs=1, help='directory of phone files')
    parser.add_argument('wrddir', metavar='WRDDIR', nargs=1, help='directory of word files')
    parser.add_argument('outdir', metavar='OUTDIR', nargs=1, help='output directory')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False, 
            help='talk more')
    parser.add_argument('-n', '--n_jobs', action='store', dest='n_jobs', default=1,
            help='number of parallel jobs')

    args = parser.parse_args()
    phndir = args.phndir[0]
    wrddir = args.wrddir[0]
    outdir = args.outdir[0]
    verbose = args.verbose
    n_jobs = int(args.n_jobs)

    if verbose:
        print('-------------')
        print('Phon_dir={}'.format(phndir))
        print('Word_dir={}'.format(wrddir))
        print('out_dir={}'.format(outdir))
        print('n_jobs={}'.format(n_jobs))
        print('-------------')
        print 'loading files'
    
    #####
    phn_fragments, wrd_fragments = load(phndir, wrddir, outdir)

    if verbose:
        print 'splitting folds'
    split_em(phn_fragments, outdir)

    if verbose:
        print 'extracting gold'
    make_gold(phn_fragments, outdir, n_jobs, verbose)

    if verbose:
        print 'all done.'
