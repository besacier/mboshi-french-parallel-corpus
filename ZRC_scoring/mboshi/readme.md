HOW TO PREPERE FILES FOR EVALUTAION
-----------------------------------


To build the files used by Aren software and tde (evaluation kit) 
for the track2 of the challenge you need to follow:


1. install all the python dependences using conda/pip:

    $ conda create --name prep_corpus --file requirements.txt
    $ source activate prep_corpus
    
    # to install he tde
    $ pip install cx-Freeze==5.0.1 --user
    $ pip install pytz==2016.10 --user
    $ pip install toml==0.9.2 --user
    $ pip install tox==2.5.0 --user 
    $ pip install -b zerospeech2017 git+https://github.com/bootphon/tde --user


2. gnu-parallel (https://www.gnu.org/software/parallel/) is used on some 
   script to execute commands in parallel in bash, type the following line and
   follow the instructions:

   $ (wget -O - pi.dk/3 || curl pi.dk/3/ || fetch -o - http://pi.dk/3) | bash
   $ parallel --will-cite


3. copy your abkhazia alignements to the directory `alignement`, I use
   a symbolic link to the abkhazia alignments (done by Julien), these 
   files are in `/fhgfs/bootphon/projects/challenge2017/final_datasets/alignment/mandarin`

   $ cp your_phone_file.txt alignment/alignment_phone.txt
   $ cp your_word_file.txt alignment/alignment_word.txt

   where the format of the alignment_phone.txt file has the format:

   file start1(sec) end1(sec) phoneme1
   file start2(sec) end2(sec) phoneme2
   file start3(sec) end3(sec) phoneme3
   ...

   same format for alignment_word.txt but changing the phonemes by words

   **NOTE**: Silences are set on the phoneme file with the string SIL 


4. You will need to modify the "config" file with the parameters for
   your corpus ...


5. run the run.sh script, depending on the size of the corpus

    $ ./run.sh


if there is no errors you can use the eval2.py with the command line:

    $ CORPUS='CORPUS_NAME' python ./eval2/py -v [file.class] [out_dir]





