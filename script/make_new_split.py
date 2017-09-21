#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import sys
import os
import collections
import subprocess
import random
import pickle

if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

all_dir = '/vol/work/godard/dat/mboshi-french-parallel-corpus/full_corpus_spkr/all/'
dev_dir = '/vol/work/godard/dat/mboshi-french-parallel-corpus/full_corpus_spkr/dev/'
train_dir = '/vol/work/godard/dat/mboshi-french-parallel-corpus/full_corpus_spkr/train/'
all_dir_ns = '/vol/work/godard/dat/mboshi-french-parallel-corpus/full_corpus_newsplit/all/'
dev_dir_ns = '/vol/work/godard/dat/mboshi-french-parallel-corpus/full_corpus_newsplit/dev/'
train_dir_ns = '/vol/work/godard/dat/mboshi-french-parallel-corpus/full_corpus_newsplit/train/'


def make_sent_list_from_multiple_files(source_dir, extension):
    """Create a list of one-line text strings contained in source_dir/*.extension files."""
    lines = []
    for fname in glob.glob(source_dir + '*.' + extension):
        with open(fname, encoding='utf-8') as f:
            line = f.read().strip()
            lines += [line]
    return lines


def calculate_text_overlap(dir1, dir2):
    count = 0
    lines_1 = make_sent_list_from_multiple_files(dir1, 'mb.cleaned')
    lines_2 = make_sent_list_from_multiple_files(dir2, 'mb.cleaned')
    for l in lines_1:
        if l in lines_2:
            count += 1
    print('overlap ratio: ', count/len(lines_1), '(', count, '/', len(lines_1), ')')


def make_dictionary(source_dir, extension):
    """Makes a dictionary from source_dir/*.extension files.
    
    Dictionary format is {fileid:(text, source, speaker)}
    source in {dico, part}, speaker in {kouarata, abiayi, martial}
    """
    d = {}
    for fname in glob.glob(source_dir + '*.' + extension):
        bname = os.path.basename(fname)
        with open(fname, encoding='utf-8') as f:
            text = f.read().strip()
            if bname.find('Part') != -1:
                source = 'part'
            elif bname.find('Dico') != -1:
                source = 'dico'
            else:
                sys.exit('Unknown source for text.')
            speaker = bname.split('_')[0]
            fileid = bname[:-(len(extension) + 1)]
            d[fileid] = (text, source, speaker)
    return d


def count_source_and_speakers(d):
    source_list = []
    speaker_list = []
    for key, value in d.items():
        source_list += [value[1]]
        speaker_list += [value[2]]
    print(collections.Counter(source_list))
    print(collections.Counter(speaker_list))


def action_on_file_list(source_dir, extension, input_list, action='ls', target_dir=None, dry_run=True):
    """Applies action to source_dir/*.extension files filtered by input_list."""
    
    for fname in glob.glob(source_dir + '*.' + extension):
        for filtered_name in input_list:
            bname = os.path.basename(fname)
            # Switch to this to remove bad FA files (no speaker names in the list provided)
            # if bname.split('_', maxsplit=1)[1][:-(len(extension) + 1)] == filtered_name:
            if bname[:-(len(extension) + 1)] == filtered_name:
                if dry_run:
                    if target_dir:
                        print([action, fname, target_dir])
                    else:
                        print([action, fname])
                else:
                    if target_dir:
                        print([action, fname, target_dir])
                        subprocess.call([action, fname, target_dir])
                    else:
                        print([action, fname])
                        subprocess.call([action, fname])
    

# Clean bad forced alignments
bad_fa_txt_list = ['2015-09-07-14-53-15_samsung-SM-T530_mdw_elicit_Dico19_70',
                '2015-09-07-15-24-49_samsung-SM-T530_mdw_elicit_Dico19_131',
                '2015-09-07-15-24-49_samsung-SM-T530_mdw_elicit_Dico19_70',
                '2015-09-07-15-24-49_samsung-SM-T530_mdw_elicit_Dico19_84',
                '2015-09-08-11-33-57_samsung-SM-T530_mdw_elicit_Dico18_116',
                '2015-09-08-11-33-57_samsung-SM-T530_mdw_elicit_Dico18_124',
                '2015-09-08-11-33-57_samsung-SM-T530_mdw_elicit_Dico18_152',
                '2015-09-08-11-33-57_samsung-SM-T530_mdw_elicit_Dico18_158',
                '2015-09-08-11-33-57_samsung-SM-T530_mdw_elicit_Dico18_161',
                '2015-09-08-11-33-57_samsung-SM-T530_mdw_elicit_Dico18_7',
                '2015-09-08-11-33-57_samsung-SM-T530_mdw_elicit_Dico18_96',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_36',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_37',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_38',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_39',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_41',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_43',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_49',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_50',
                '2015-09-08-15-33-17_samsung-SM-T530_mdw_elicit_Dico15_53',
                '2015-09-10-09-17-49_samsung-SM-T530_mdw_elicit_Dico9_40',
                '2015-09-10-09-17-49_samsung-SM-T530_mdw_elicit_Dico9_51',
                '2015-09-10-09-17-49_samsung-SM-T530_mdw_elicit_Dico9_90',
                '2015-09-11-06-45-48_samsung-SM-T530_mdw_elicit_Dico4_98',
                '2015-09-11-07-49-16_samsung-SM-T530_mdw_elicit_Dico3_170',
                '2015-09-11-07-49-16_samsung-SM-T530_mdw_elicit_Dico3_79']

# # removing 26 files for each extensions corresponding to bad forced alignments
# action_on_file_list(all_dir_ns, 'fr', bad_fa_txt_list, action='rm', dry_run=False)
# action_on_file_list(all_dir_ns, 'fr.cleaned', bad_fa_txt_list, action='rm', dry_run=False)
# action_on_file_list(all_dir_ns, 'mb', bad_fa_txt_list, action='rm', dry_run=False)
# action_on_file_list(all_dir_ns, 'mb.cleaned', bad_fa_txt_list, action='rm', dry_run=False)
# action_on_file_list(all_dir_ns, 'mb.cleaned.split', bad_fa_txt_list, action='rm', dry_run=False)
# action_on_file_list(all_dir_ns, 'stm', bad_fa_txt_list, action='rm', dry_run=False)
# action_on_file_list(all_dir_ns, 'wav', bad_fa_txt_list, action='rm', dry_run=False)


def sample_dev_from_dict(d):
    """Samples a dev set that won't overlap with the train set."""
    count = 0
    file_id_list = []
    # Extract dictionary keys as list
    keys = list(d.keys())
    # Shuffle the keys
    random.shuffle(keys)
    while count < 514:
        # Sample entry in dict
        file_id = keys[0]
        keys.remove(file_id)
        count += 1
        file_id_list += [file_id]
        # Reminder: d's format is {fileid:(text, source, speaker)}
        text = d[file_id][0]
        # Check if there is identical text in other keys/ids and add the new ids to the list
        same = [k for k in keys if d[k][0] == text]
        for k in same:
            file_id_list += [k]
            keys.remove(k)
            count += 1
    return file_id_list


# ONE SHOT: create list for dev set
# dev_list_ns = sample_dev_from_dict(all_dict_ns)
# with open('dev_list.pkl', 'wb') as f:
#     pickle.dump(dev_list_ns, f)
    
# Retrieve dev_list
with open('dev_list.pkl', 'rb') as f:
    dev_list_ns = pickle.load(f)

# Move proper files from train to dev    
# action_on_file_list(train_dir_ns, 'fr', dev_list_ns, action='mv', target_dir=dev_dir_ns, dry_run=False)
# action_on_file_list(train_dir_ns, 'fr.cleaned', dev_list_ns, action='mv', target_dir=dev_dir_ns, dry_run=False)
# action_on_file_list(train_dir_ns, 'mb', dev_list_ns, action='mv', target_dir=dev_dir_ns, dry_run=False)
# action_on_file_list(train_dir_ns, 'mb.cleaned', dev_list_ns, action='mv', target_dir=dev_dir_ns, dry_run=False)
# action_on_file_list(train_dir_ns, 'mb.cleaned.split', dev_list_ns, action='mv', target_dir=dev_dir_ns, dry_run=False)
# action_on_file_list(train_dir_ns, 'stm', dev_list_ns, action='mv', target_dir=dev_dir_ns, dry_run=False)
# action_on_file_list(train_dir_ns, 'wav', dev_list_ns, action='mv', target_dir=dev_dir_ns, dry_run=False)
    

calculate_text_overlap(dev_dir_ns, train_dir_ns)
    
# Print stats
dev_dict_ns = make_dictionary(dev_dir_ns, 'mb.cleaned')
train_dict_ns = make_dictionary(train_dir_ns, 'mb.cleaned')
all_dict_ns = make_dictionary(all_dir_ns, 'mb.cleaned')
print('---dev')
count_source_and_speakers(dev_dict_ns)
print('---train')
count_source_and_speakers(train_dict_ns)
print('---all')
count_source_and_speakers(all_dict_ns)
