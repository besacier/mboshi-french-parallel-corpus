#!/usr/bin/env python
# -*- coding: utf-8 -*- 

'''
correct_sil.py

Reads a file with the fields:

    _start_ _end_ _text_

where _start_ and _end_ are numerical time stamps (seconds, frames, ...)
and _text_ is a word. The file contain rows that should be sorted 
numerically and in ascendent order by the columns _start_ and _end_ (use linux command sort with parameters -k1n -k2n)

Corrects the aligmnet of SIL on wrd files that are stored on the 
french/wrd, mandarin/wrd and english/wrd. These files are build with
the prep_{french|mandarin|english}.sh scripts, and in a short they 
are build joining the SIL from the corpora phoneme file (that contains 
the SIL) with the words corpora file. 

The wrd's file problem looks like:

    10 20 word1  <- 1: wrong alignment
    15 20 SIL    <- 2: wrong alignment 
    20 30 word2  <- 3: ok

The problem is that line 1 and 2 are overlaping, and the correction 
is to swap 20 and 15 in lines 1 and 2 (checked listening samples on 
wav files) to have

    10 15 word1  <- 1: ok 
    15 20 SIL    <- 2: ok 
    20 30 word2  <- 3: ok

there are other errors that are corrected in this script and described 
on the code

'''

import argparse                                        
import pandas as pd                                    
import os
import numpy as np
from itertools import compress
import string

parser = argparse.ArgumentParser()                     
parser.add_argument('file_', metavar='FILE',     
                    nargs=1, help='the file to check')         
parser.add_argument('gap_', metavar='GAP_TOKEN', default='SIL', 
        action='store', help='token used to mark gaps [default "SIL"]')
parser.add_argument('type', metavar='FILE_TYPE', default='wrd', 
        action='store', help='token used to mark gaps [default "SIL"]')

args = parser.parse_args()                             
file_ = args.file_[0]                           
gap_ = args.gap_
file_type = args.type

data = pd.read_table(file_, sep=r'\s+|\t+|\s+\t+|\t+\s+|\xc2\xa0', 
        engine='python', header=None, names=['nfile', 'start','end', 'txt'])          

# convert to numarray for convenience 
f = list(data['nfile'])
s = np.array(data['start'])
e = np.array(data['end'])
t = list(data['txt']) 
new_data = list()

for f_, s_, e_, t_ in  zip(f, s, e, t):
    new_data.append([f_, np.float(s_), np.float(e_), t_])


#
# case 1: filling gaps with SIL
#6.3670 6.4040 d   
#6.4040 7.0740 SIL  <--- inserted row
#7.0740 7.3220 ae
#7.3220 7.3510 n
#
# case 2: swaping + filling gap with SIL  
# from
#41.4325 41.5825 seul      
#41.5375 41.7575 non       
# to
#41.4325 41.5375 seul <--- swap end      
#41.5375 41.5825 SIL  <--- inserted row
#41.5825 41.7575 non  <--- swap begin
#

case2 = False
final_data = list()
for n in xrange(len(new_data[:-1])): 
    curr_file, curr_start, curr_end, curr_text = new_data[n]
    next_file, next_start, next_end, next_text = new_data[n+1]
 
    # correcting values of starting and ending time are swaped (start>end)
    if curr_start > curr_end:
        curr_start,  curr_end = curr_end, curr_start
    if next_start > next_end:
        next_start, next_end = next_end, next_start 

    # if both sils
    if curr_text == next_text == 'SIL' and curr_file == next_file:
        case2 = False
        final_data.append([curr_file, curr_start, next_end, 'SIL']) 
        continue

    # never compare next_start == curr_end it is not need
    if (next_start > curr_end) and (curr_file == next_file): # the case 1
        final_data.append([curr_file, curr_start, next_start, curr_text])

    elif (next_start < curr_end) and (curr_file == next_file): # the case 2
        case2 = True
        next_start, curr_end = curr_end, next_start
        final_data.append([curr_file, curr_start, curr_end, curr_text])
        if next_start > curr_end:
            final_data.append([curr_file, curr_end, next_start, gap_])
        final_data.append([curr_file, next_start, next_end, next_text])     
    
    else:
        if case2:
            case2 = False
        else:
            case2 = False
            final_data.append([curr_file, curr_start, curr_end, curr_text])
        
        #final_data.append([next_start, next_end, next_text])
#else:
#    # including the missing end data on final_data  
#    final_data.append([next_file, next_start, next_end, next_text])

new_data=final_data


for nfile, start, end, text in final_data:
    try:
        print("{} {:.4f} {:.4f} {}".format(nfile, start, end, text))
    except ValueError:
        print("'{}' '{}' '{}' '{}'".format(nfile, start, end, text))
        raise



