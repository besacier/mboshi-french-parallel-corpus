#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import argparse                                        
import pandas as pd                                    
from collections import defaultdict

parser = argparse.ArgumentParser()                     
parser.add_argument('file_', metavar='WORD_FILE',     
                    nargs=1, help='wrd file to clusterize')         
args = parser.parse_args()                             
file_ = args.file_[0]                            
                                                       
data = pd.read_table(file_, sep='\s+', encoding='utf-8', 
        header=None, names=['file', 'start','end', 'txt'])          

d = defaultdict(list)
for f, s, e, t in zip(data['file'], data['start'], data['end'], data['txt']):
    if t == 'SIL':
        #print("{} {} {} {}".format(f, s, e, t))
        pass
    d[t].append( (f, s, e) )

#print d.items()
for n, (k, v) in enumerate(d.items()):
    print("Class {} [{}]".format(n, k))
    for f, s, e in v:
        print("{} {:.4f} {:.4f}".format(f, s, e))
    print("")

