#!/usr/bin/env python

import glob
import os.path as path
from collections import defaultdict

all_classes = defaultdict(list)
files = glob.glob(path.join('out', '*.classes.*'))
for f in files:
    with open(f) as infile:
        for line in infile.readlines():
            l = line.strip()
            if len(l) == 0: # empty line
                next
            elif l[:5] == 'Class': # the token
                new_class = l[l.find('[')+1:-1]
            else : # lines with info
                all_classes[new_class].append(l)

for n, token in enumerate(all_classes):
    print('Class {} [{}]'.format(n, token))
    print('\n'.join(set(all_classes['{}'.format(token)]))+'\n')

