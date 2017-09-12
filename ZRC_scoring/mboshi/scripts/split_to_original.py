#!/usr/bin/env python

VERSION="0.1.0"

from collections import defaultdict
import sys

def read_mapping(fname):
    mapping = {}
    for line in open(fname):
        orig, start, end, dest = line.strip().split(' ')
        mapping[dest] = (float(start), float(end), orig)
    return mapping

class FileNameError(Exception):
    pass

class IntervalError(Exception):
    pass


def find(mapping, fname, start, end):
    try:
        return mapping[fname]
    except KeyError:
        print fname
        raise FileNameError


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='split_to_original.py')
	
    parser.add_argument('file', metavar='INPUTFILE', nargs=1, help='file in the split corpus')
    parser.add_argument('log', metavar='LOGFILE', nargs=1)
    args = parser.parse_args()
    fname = args.file[0] # a file that contains fname_split, start, end
    logfile = args.log[0]
    mapping = read_mapping(logfile)

    try:
        with open(fname) as rfile:
	    for line in rfile.readlines():
		try:
                    l_ = line.strip().split(' ')
		    name = l_[0]
                    start = float(l_[1])
                    end = float(l_[2])
	            orig_start, _, original_name = find(mapping, name, start, end)
                    line = "{} {:.4f} {:.4f}".format(original_name, start+orig_start, end+orig_start) 
                    if len(l_)>3:
                        line += " " + " ".join([str(x) for x in l_[3:]])
                    line+="\n"
		except:
		    pass

		sys.stdout.write('{}'.format(line))
                #try:
                #    splited_name, start, end = line.strip().split(' ')
                #except:
                #    next
                #start = float(start); end = float(end)
		#orig_start, _, original_name = find(mapping, splited_name, start, end)
                #sys.stdout.write('{0} {1:.4f} {2:.4f}:{3} {4:.4f} {5:.4f}\n'.format(
		#	splited_name, start, end,
		#	original_name, start+orig_start, end+orig_start	))


    except IntervalError:
        print 'Interval not found in any file: {0} {1:.3f} {2:.3f}'.format(
            fname, start, end)
    except FileNameError:
        print 'Filename not found: {0}'.format(fname)
