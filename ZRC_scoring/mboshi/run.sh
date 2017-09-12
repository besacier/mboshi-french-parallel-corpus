#!/bin/bash

set -e

#- passing some parameters
#$ -S /bin/bash        # the shell used 
#$ -N run_gold     # gives the name of the job
#$ -pe openmpi_ib 4 # nb of cores required (this is purely declarative)
#$ -j yes   # join stdout and stderr in the same file
#$ -q cpu   # name of the queue (cpu, gpu, all)
#$ -cwd     # puts the logs in the current directory

. config

# NSLOTS is the number of cpu used by qsub and parallel
#
# if using the script from the command line with bash,
# then you must export the variable first:
#
# $ export NSLOTS=40
#
if [ -z ${NSLOTS+x} ]; then
    NSLOTS=1
fi
echo "## number of cpus/NSLOTS = " $NSLOTS

# testing for needed commands in this script
for cmd in "parallel" ; do
    printf "%-10s" "$cmd"
    if hash "$cmd" 2>/dev/null; then
        printf "OK\n"; 
    else
        printf "missing\n";
        exit 1;
    fi
done

mkdir -p in out/phn out/wrd wrd phn

# prepare the phn and wrd files (split by speaker/file)
echo "### preparing the phn and files ..."
./scripts/prep_gold.sh

# split the corpus in small tokens 
echo "### split the corpus ..."
./scripts/corpus_split_noise.py --log SPLIT_LOG -v in out

# make the files ${CORPUS}.{files,intervals.cross,intervals.within,phn,split,wrd} 
# the output files are in the out directory ..
#
# these gold files are used by the evaluation toolkit 
# https://github.com/bootphon/tde/tree/zerospeech2017
# 
# TODO: change the value of max_time ... for mandarin~60min .. french~5h .. english~10h
echo "### making the gold for the evaluation (tde)"
./scripts/prep_gold.py -n $NSLOTS -v out/phn out/wrd out

# gattering all the file names of splits with its related start and ending time stamps
# and building a translation dictionary between that data and the original non-split
# data

# change the names of speakers that were previusly splited, these names
# are the first column on ${CORPUS}.{files,intervals.cross,intervals.within,phn,split,wrd}
# but must be trasformed to the original speaker name and its corresponding
# time stamp 
echo "### converting speaker and time stamps back to original"
ls out/${CORPUS}.* | parallel -j $NSLOTS \
    './scripts/split_to_original.py {} SPLIT_LOG > {}.tmp; 
    mv {}.tmp {}'

### join all the splited class files into one with common phonemes 
###
echo "### joining all the class files into one "
./scripts/join_classes.py > out/${CORPUS}.classes

# correcting the 
cut -d' ' -f1 out/${CORPUS}.phn | sort -u > out/${CORPUS}.files

## create the VAD files used by Aren's programs
#echo "### creating files for AGu ..."
#./scripts/make_vad.sh

## creating the files for AGu: 
echo "### creating files for the AGu topline (tags.txt and gold.txt) ..."
./scripts/create_gold.sh


# removing and copying the files for the evaluation
rm -rf out/*.tmp out/${CORPUS}.classes.* 
cp out/${CORPUS}.* resources/




