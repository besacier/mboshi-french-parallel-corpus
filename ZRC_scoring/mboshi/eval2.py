"""Evaluate Spoken Term Discovery"""

from __future__ import division

import os
import os.path as path
import sys
import math
from itertools import izip

import numpy as np
from joblib import Parallel, delayed

VERSION = "0.2.2"

from tde.util.reader import load_classes_txt, load_corpus_txt, load_split
from tde.util.printing import verb_print, banner, pretty_score_f, \
    pretty_score_nlp
from tde.util.splits import truncate_intervals, check_intervals
from tde.util.functions import fscore, nCr

from tde.measures.nlp import NED, coverage
from tde.measures.group import evaluate_group
from tde.measures.boundaries import Boundaries, eval_from_bounds
from tde.measures.match import eval_from_psets, make_pdisc, make_pgold, \
    make_psubs
from tde.measures.token_type import evaluate_token_type


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


def _load_classes(fname, corpus, split_mapping=None):
    return load_classes_txt(fname, corpus, split=split_mapping)


def load_disc(fname, corpus, split_file, truncate, verbose):
    with verb_print('  loading discovered classes',
                             verbose, True, True, True):
        split_mapping = load_split(split_file)
        disc, errors = _load_classes(fname, corpus, split_mapping)
        if not truncate:
            errors_found = len(errors) > 0
            if len(errors) > 100:
                print 'There were more than 100 interval errors found.'
                print 'Printing only the first 100.'
                print
                errors = errors[:100]
            for fragment in sorted(errors, key=lambda x: (x.name, x.interval.start)):
                print '  error: {0} [{1:.3f}, {2:.3f}]'.format(
                    fragment.name, fragment.interval.start, fragment.interval.end)
            if not truncate and errors_found:
                print 'There were errors in {0}. Use option -f to'\
                    ' automatically skip invalid intervals.'.format(fname)
                sys.exit()

    if truncate:
        with verb_print('  checking discovered classes and truncating'):
            disc, filename_errors, interval_errors = \
                truncate_intervals(disc, corpus,
                                   split_mapping)
    else:
        with verb_print('  checking discovered classes', verbose, True,
                                 True, True):
            filename_errors, interval_errors = \
                check_intervals(disc, split_mapping)
    if not truncate:
        filename_errors = sorted(filename_errors,
                                 key=lambda x: (x.name, x.interval.start))
        interval_errors = sorted(interval_errors,
                                 key=lambda x: (x.name, x.interval.start))
        interval_error = len(interval_errors) > 0
        filename_error = len(filename_errors) > 0
        errors_found = filename_error or interval_error
        if interval_error:
            print banner('intervals found in {0} outside of valid'
                                      ' splits'.format(fname))
            if len(interval_errors) > 100:
                print 'There were more than 100 interval errors found.'
                print 'Printing only the first 100.'
                print
                interval_errors = interval_errors[:100]
            for fragment in sorted(interval_errors,
                                   key=lambda x: (x.name, x.interval.start)):
                print '  error: {0} [{1:.3f}, {2:.3f}]'.format(
                    fragment.name,
                    fragment.interval.start, fragment.interval.end)
        if filename_error:
            print banner('unknown filenames found in {0}'
                                      .format(fname))
            if len(filename_errors) > 100:
                print 'There were more than 100 filename errors found.'
                print 'Printing only the first 100.'
                print
                filename_errors = filename_errors[:100]
            for fragment in sorted(filename_errors,
                                   key=lambda x: (x.name, x.interval.start)):
                print '  error: {0}'.format(fragment.name)
        if not truncate and errors_found:
            print 'There were errors in {0}. Use option -f to automatically skip invalid intervals.'.format(fname)
            sys.exit()
    return disc


def _match_sub(disc_clsdict, gold_clsdict, phn_corpus, names, label,
               verbose, n_jobs):
    em = eval_from_psets
    if verbose:
        print '  matching ({2}): subsampled {0} files in {1} sets'\
            .format(sum(map(len, names)), len(names), label)
    with verb_print('  matching ({0}): prepping psets'.format(label),
                             verbose, True, True, True):
        pdiscs = [make_pdisc(disc_clsdict.restrict(fs, True),
                             False, False)
                  for fs in names]
        pgolds = [make_pgold(gold_clsdict.restrict(fs, True),
                             False, False)
                  for fs in names]
        psubs = [make_psubs(disc_clsdict.restrict(fs, True),
                            phn_corpus, 3, 20, False, False)
                 for fs in names]
    with verb_print('  matching ({0}): calculating scores'
                             .format(label), verbose, False, True, False):
        tp, tr = izip(*Parallel(n_jobs=n_jobs,
                                verbose=5 if verbose else 0,
                                pre_dispatch='n_jobs')
                      (delayed(em)(pdisc, pgold, psub)
                      for pdisc, pgold, psub in zip(pdiscs, pgolds, psubs)))
    tp, tr = np.fromiter(tp, dtype=np.double), np.fromiter(tr, dtype=np.double)
    tp, tr = praggregate(tp, tr)
    return tp, tr


def match(disc_clsdict, gold_clsdict, phn_corpus,
          fragments_within, fragments_cross,
          dest, verbose, n_jobs):
    if verbose:
        print banner('MATCHING')
    pc, rc = _match_sub(disc_clsdict, gold_clsdict, phn_corpus,
                        fragments_cross, 'cross', verbose, n_jobs)
    fc = np.fromiter((fscore(pc[i], rc[i]) for i in xrange(pc.shape[0])), dtype=np.double)

    pw, rw = _match_sub(disc_clsdict, gold_clsdict, phn_corpus,
                        fragments_within, 'within', verbose, n_jobs)
    fw = np.fromiter((fscore(pw[i], rw[i]) for i in xrange(pw.shape[0])), dtype=np.double)
    with open(path.join(dest, 'matching'), 'w') as fid:
        fid.write(pretty_score_f(pc, rc, fc, 'match total',
                                 len(fragments_cross),
                                 sum(map(len, fragments_cross))))
        fid.write('\n')
        fid.write(pretty_score_f(pw, rw, fw, 'match within-speaker only',
                                 len(fragments_within),
                                 sum(map(len, fragments_within))))

def _group_sub(disc_clsdict, names, label, verbose, n_jobs):
    eg = evaluate_group
    if verbose:
        print '  group ({2}): subsampled {0} files in {1} sets'\
            .format(sum(map(len, names)), len(names), label)
    with verb_print('  group ({0}): calculating scores'.format(label),
                             verbose, False, True, False):
        p, r = izip(*(Parallel(n_jobs=n_jobs,
                              verbose=5 if verbose else 0,
                              pre_dispatch='n_jobs')
                     (delayed(eg)(disc_clsdict.restrict(ns, True))
                      for ns in names)))
    p, r = np.fromiter(p, dtype=np.double), np.fromiter(r, dtype=np.double)
    p, r = praggregate(p, r)
    return p, r


def group(disc_clsdict, fragments_within, fragments_cross, dest, verbose, n_jobs):
    if verbose:
        print banner('GROUP')
    pc, rc = _group_sub(disc_clsdict, fragments_cross, 'cross', verbose, n_jobs)
    fc = np.fromiter((fscore(pc[i], rc[i]) for i in xrange(pc.shape[0])), dtype=np.double)

    pw, rw = _group_sub(disc_clsdict, fragments_within, 'within', verbose, n_jobs)
    fw = np.fromiter((fscore(pw[i], rw[i]) for i in xrange(pw.shape[0])), dtype=np.double)
    with open(path.join(dest, 'group'), 'w') as fid:
        fid.write(pretty_score_f(pc, rc, fc, 'group total',
                                 len(fragments_cross),
                                 sum(map(len, fragments_cross))))
        fid.write('\n')
        fid.write(pretty_score_f(pw, rw, fw, 'group within-speaker only',
                                 len(fragments_within),
                                 sum(map(len, fragments_within))))


def _token_type_sub(clsdict, wrd_corpus, names, label, verbose, n_jobs):
    et = evaluate_token_type
    if verbose:
        print '  token/type ({2}): subsampled {0} files in {1} sets'\
            .format(sum(map(len, names)), len(names), label)
    with verb_print('  token/type ({0}): calculating scores'
                             .format(label), verbose, False, True, False):
        pto, rto, pty, rty = izip(*(et(clsdict.restrict(ns, False),
                                       wrd_corpus.restrict(ns))
                                    for ns in names))
    pto, rto, pty, rty = np.array(pto), np.array(rto), np.array(pty), np.array(rty)
    pto, rto = praggregate(pto, rto)
    pty, rty = praggregate(pty, rty)

    return pto, rto, pty, rty


def token_type(disc_clsdict, wrd_corpus, fragments_within, fragments_cross,
               dest, verbose, n_jobs):
    if verbose:
        print banner('TOKEN/TYPE')
    ptoc, rtoc, ptyc, rtyc = _token_type_sub(disc_clsdict, wrd_corpus,
                                             fragments_cross, 'cross',
                                             verbose, n_jobs)
    ftoc = np.fromiter((fscore(ptoc[i], rtoc[i]) for i in xrange(ptoc.shape[0])),
                       dtype=np.double)
    ftyc = np.fromiter((fscore(ptyc[i], rtyc[i]) for i in xrange(ptyc.shape[0])),
                       dtype=np.double)

    ptow, rtow, ptyw, rtyw = _token_type_sub(disc_clsdict, wrd_corpus,
                                             fragments_within, 'within',
                                             verbose, n_jobs)
    ftow = np.fromiter((fscore(ptow[i], rtow[i]) for i in xrange(ptow.shape[0])),
                       dtype=np.double)
    ftyw = np.fromiter((fscore(ptyw[i], rtyw[i]) for i in xrange(rtyw.shape[0])),
                       dtype=np.double)
    with open(path.join(dest, 'token_type'), 'w') as fid:
        fid.write(pretty_score_f(ptoc, rtoc, ftoc, 'token total',
                                 len(fragments_cross),
                                 sum(map(len, fragments_cross))))
        fid.write('\n')
        fid.write(pretty_score_f(ptyc, rtyc, ftyc, 'type total',
                                 len(fragments_cross),
                                 sum(map(len, fragments_cross))))
        fid.write('\n')
        fid.write(pretty_score_f(ptow, rtow, ftow, 'token within-speaker only',
                                 len(fragments_within),
                                 sum(map(len, fragments_within))))
        fid.write('\n')
        fid.write(pretty_score_f(ptyw, rtyw, ftyw, 'type within-speaker only',
                                 len(fragments_within),
                                 sum(map(len, fragments_within))))


def _nlp_sub(disc_clsdict, gold_clsdict, names, label, verbose, n_jobs):
    # ned
    ned = NED
    cov = coverage
    if verbose:
        print '  nlp ({2}): subsampled {0} files in {1} sets'\
            .format(sum(map(len, names)), len(names), label)
    with verb_print('  nlp ({0}): calculating scores' .format(label), verbose, False, True, False):

        if n_jobs>1:
            ned_score = Parallel(n_jobs=n_jobs, verbose=5 if verbose else 0,
                          pre_dispatch='n_jobs')(delayed(ned)(disc_clsdict.restrict(ns, True))
                          for ns in names)
            cov_score = Parallel(n_jobs=n_jobs, verbose=5 if verbose else 0,
                          pre_dispatch='n_jobs')(delayed(cov)(disc_clsdict.restrict(ns, False),
                          gold_clsdict.restrict(ns, False)) for ns in names)
        else:
            ned_score = list(); cov_score = list() 
            for ns in names:
               ned_score_ = ned(disc_clsdict.restrict(ns, True))
               cov_score_ = cov(disc_clsdict.restrict(ns, False), gold_clsdict.restrict(ns, False))
               ned_score.append(ned_score_)
               cov_score.append(cov_score_)

 
    # don't replace nan's by 1, but ignore them, unless all values in ned_score
    # are nan
    ned_score, cov_score = np.array(ned_score), np.array(cov_score)
    ned_score, cov_score = aggregate(ned_score, default_score=1), \
                           aggregate(cov_score, default_score=0)
    return np.array(ned_score), np.array(cov_score)


def nlp(disc_clsdict, gold_clsdict, fragments_within, fragments_cross,
        dest, verbose, n_jobs):

    if verbose:
        print banner('NLP')
   
    nc, cc = _nlp_sub(disc_clsdict, gold_clsdict, fragments_cross, 'cross',
                      verbose, n_jobs)
    nw, cw = _nlp_sub(disc_clsdict, gold_clsdict, fragments_within, 'within',
                      verbose, n_jobs)
  

    # calculating the pairs/clusters found in the discovery algoritms, 
    # it's stored on the 'nlp' output file, used to compare diff algoritms
    nclust = len(disc_clsdict.items()) 
    try:
        npairs = sum([nCr(len(v[1]), 2) for v in disc_clsdict.items()])
    except:
        npairs = -1 
 
    with open(path.join(dest, 'nlp'), 'w') as fid:
        fid.write(pretty_score_nlp(nc, cc, 'NLP total',
                     len(fragments_cross), sum(map(len, fragments_cross)), 
                     nclust, npairs))
        fid.write('\n')

        fid.write(pretty_score_nlp(nw, cw, 'NLP within-speaker only',
                     len(fragments_within), sum(map(len, fragments_within)), 
                     nclust, npairs))


def _boundary_sub(disc_clsdict, corpus, names, label, verbose, n_jobs):
    eb = eval_from_bounds
    if verbose:
        print '  boundary ({2}): subsampled {0} files in {1} sets'\
            .format(sum(map(len, names)), len(names), label)
    with verb_print('  boundary ({0}): calculating scores'
                             .format(label), verbose, True, True, True):
        disc_bounds = [Boundaries(disc_clsdict.restrict(ns))
                       for ns in names]
        gold_bounds = [Boundaries(corpus.restrict(ns))
                       for ns in names]
    with verb_print('  boundary ({0}): calculating scores'
                             .format(label), verbose, False, True, False):
        p, r = izip(*Parallel(n_jobs=n_jobs, verbose=5 if verbose else 0,
                              pre_dispatch='2*n_jobs') \
                    (delayed(eb)(disc, gold)
                     for disc, gold in zip(disc_bounds, gold_bounds)))
    p, r = np.fromiter(p, dtype=np.double), np.fromiter(r, dtype=np.double)
    p, r = praggregate(p, r)
    return p, r


def boundary(disc_clsdict, corpus, fragments_within, fragments_cross,
               dest, verbose, n_jobs):
    if verbose:
        print banner('BOUNDARY')
    pc, rc = _boundary_sub(disc_clsdict, corpus, fragments_cross,
                           'cross', verbose, n_jobs)
    fc = np.fromiter((fscore(pc[i], rc[i]) for i in xrange(pc.shape[0])), dtype=np.double)
    pw, rw = _boundary_sub(disc_clsdict, corpus, fragments_within,
                           'within', verbose, n_jobs)
    fw = np.fromiter((fscore(pw[i], rw[i]) for i in xrange(pw.shape[0])), dtype=np.double)
    with open(path.join(dest, 'boundary'), 'w') as fid:
        fid.write(pretty_score_f(pc, rc, fc, 'boundary total',
                                 len(fragments_cross),
                                 sum(map(len, fragments_cross))))
        fid.write('\n')
        fid.write(pretty_score_f(pw, rw, fw, 'boundary within-speaker only',
                                 len(fragments_within),
                                 sum(map(len, fragments_within))))

def aggregate(array, default_score=0.):
    array = np.array(array)
    array = array[np.logical_not(np.isnan(array))]
    if array.shape[0] == 0:
        array = np.array([default_score])
    return array

def praggregate(p_array, r_array, default_score=0.):
    p_array, r_array = np.array(p_array), np.array(r_array)
    p_index = np.logical_not(np.isnan(p_array))
    r_index = np.logical_not(np.isnan(r_array))
    index = np.logical_and(p_index, r_index)
    p_array, r_array = p_array[index], r_array[index]
    if not np.any(index):
        p_array, r_array = np.array([default_score]), np.array([default_score])
    return p_array, r_array

def _load_corpus(fname):
    return load_corpus_txt(fname)

def load_wrd_corpus(wrd_corpus_file, verbose):
    with verb_print('  loading word corpus file',
                             verbose, True, True, True):
        wrd_corpus = _load_corpus(wrd_corpus_file)
    return wrd_corpus

def load_phn_corpus(phn_corpus_file, verbose):
    with verb_print('  loading phone corpus file',
                             verbose, True, True, True):
        phn_corpus = _load_corpus(phn_corpus_file)
    return phn_corpus

def load_fragments_cross(fname, verbose):
    with verb_print('  loading folds cross',
                             verbose, True, True, True):
        fragments = load_split(fname, multiple=True)
    return fragments

def load_fragments_within(fname, verbose):
    with verb_print('  loading folds within',
                             verbose, True, True, True):
        fragments = load_split(fname, multiple=True)
    return fragments

def load_gold(fname, corpus, verbose):
    with verb_print('  loading gold classes',
                             verbose, True, True, True):
        gold, _ = _load_classes(fname, corpus)
    return gold


if __name__ == '__main__':
    import argparse
    def parse_args():
        parser = argparse.ArgumentParser(
            prog='{}_eval2'.format(CORPUS),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Evaluate spoken term discovery on the test dataset',
            epilog="""Example usage:

$ ./{}_eval2 my_sample.classes resultsdir/

evaluates STD output `my_sample.classes` on the test dataset and stores the
output in `resultsdir/`.

Classfiles must be formatted like this:

Class 1 (optional_name)
fileID starttime endtime
fileID starttime endtime
...

Class 2 (optional_name)
fileID starttime endtime
...
""".format(CORPUS))
        parser.add_argument('disc_clsfile', metavar='DISCCLSFILE',
                            nargs=1,
                            help='discovered classes')
        parser.add_argument('outdir', metavar='DESTINATION',
                            nargs=1,
                            help='location for the evaluation results')
        parser.add_argument('-f', '--force-truncate',
                            action='store_true',
                            dest='truncate',
                            default=True,
                            help='force truncation of discovered fragments '
                            'outside of splits')
        parser.add_argument('-m', '--measures',
                            action='store',
                            nargs='*',
                            dest='measures',
                            default=[],
                            choices=['boundary', 'group', 'match', 'nlp',
                                     'token/type'],
                            help='select individual measures to perform')
        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            dest='verbose',
                            default=False,
                            help='display progress')
        parser.add_argument('-j', '--n-jobs',
                            action='store',
                            type=int,
                            dest='n_jobs',
                            default=1,
                            help='number of cores to use')
        parser.add_argument('-V', '--version', action='version',
                            version="%(prog)s version {version}".format(version=VERSION))
        return vars(parser.parse_args())
    args = parse_args()

    verbose = args['verbose']
    n_jobs = args['n_jobs']

    disc_clsfile = args['disc_clsfile'][0]
    dest = args['outdir'][0]

    if getattr(sys, 'frozen', False):
        # frozen
        rdir = path.dirname(sys.executable)
        resource_dir = path.join(rdir, 'resources')
    else:
        # unfrozen
        rdir = path.dirname(path.realpath(__file__))
        resource_dir = path.join(rdir, 'resources')


    fragments_cross_file  = path.join(resource_dir, '{}.intervals.cross'.format(CORPUS))
    fragments_within_file = path.join(resource_dir, '{}.intervals.within'.format(CORPUS))
    gold_clsfile          = path.join(resource_dir, '{}.classes'.format(CORPUS))
    phn_corpus_file       = path.join(resource_dir, '{}.phn'.format(CORPUS))
    wrd_corpus_file       = path.join(resource_dir, '{}.wrd'.format(CORPUS))
    split_file            = path.join(resource_dir, '{}.split'.format(CORPUS))

    if verbose:
        print '{}_eval2 version {}'.format(CORPUS, VERSION)
        print '---------------------------'
        print 'dataset:     test'
        print 'inputfile:   {}'.format(disc_clsfile)
        print 'destination: {}'.format(dest)
        print

    if verbose:
        print banner('LOADING FILES')

    wrd_corpus = load_wrd_corpus(wrd_corpus_file, verbose)
    phn_corpus = load_phn_corpus(phn_corpus_file, verbose)

    fragments_cross = load_fragments_cross(fragments_cross_file, verbose)
    fragments_within = load_fragments_within(fragments_within_file, verbose)

    truncate = args['truncate']
    disc_clsdict = load_disc(disc_clsfile, phn_corpus, split_file,
                             truncate, verbose)
    gold_clsdict = load_gold(gold_clsfile, phn_corpus, verbose)

    try:
        os.makedirs(dest)
    except OSError:
        pass

    with open(path.join(dest, 'VERSION_{0}'.format(VERSION)), 'w') as fid:
        fid.write('')

    measures = set(args['measures'])
    do_all = len(measures) == 0
    if do_all or 'match' in measures:
        match(disc_clsdict, gold_clsdict, phn_corpus, fragments_within,
              fragments_cross, dest, verbose, n_jobs)
    if do_all or 'group' in measures:
        group(disc_clsdict, fragments_within, fragments_cross, dest, verbose,
              n_jobs)
    if do_all or 'token/type' in measures:
        token_type(disc_clsdict, wrd_corpus, fragments_within, fragments_cross,
                   dest, verbose, n_jobs)
    if do_all or 'nlp' in measures:
        nlp(disc_clsdict, gold_clsdict, fragments_within, fragments_cross,
            dest, verbose, n_jobs)
    if do_all or 'boundary' in measures:
        boundary(disc_clsdict, wrd_corpus, fragments_within, fragments_cross,
                 dest, verbose, n_jobs)
    if verbose:
        print 'All done. Results stored in {0}'.format(dest)
