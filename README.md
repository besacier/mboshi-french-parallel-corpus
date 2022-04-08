# mboshi-french-parallel-corpus

This repository contains a speech
corpus collected during a realistic language documentation process. It is made up of 5k speech utterances in Mboshi (Bantu C25) aligned
to French text translations. Speech transcriptions are also made available: they correspond to a non-standard graphemic form close to
the language phonology.
The dataset is made available to the community for reproducible computational language documentation
experiments and their evaluation.


* full_corpus_newsplit:   contains the wav in mboshi, the linguists' transcriptions and the french translations ; this part is clean and has been checked carefully

* forced_alignments_supervised_spkr:   contains the forced alignements between mboshi speech and mboshi transcripts… might be useful if you want to score word or phone discovery from speech but …… you should consider this as a « silver » standard rather than a « gold standard » (well, they are imperfect forced alignements obtained from a small corpus, etc.) 

* ZRC_scoring: contains scripts + ref files to score spoken word discovery with the Zero Resource Challenge Metrics (see http://zerospeech.com and http://sapience.dec.ens.fr/bootphon/2017/page_3.html if you’re not familiar with these metrics)
the ref files for ZCR metrics were obtained from the above forced alignements

* lrec2018-submission.pdf : our LREC2018 paper that describes this dataset - see http://arxiv.org/abs/1710.03501 - use the following bibtex if you use this dataset in your publications:

``'
@article{DBLP:journals/corr/abs-1710-03501,
  author    = {Pierre Godard and
               Gilles Adda and
               Martine Adda{-}Decker and
               Juan Benjumea and
               Laurent Besacier and
               Jamison Cooper{-}Leavitt and
               Guy{-}No{\"{e}}l Kouarata and
               Lori Lamel and
               H{\'{e}}l{\`{e}}ne Maynard and
               Markus M{\"{u}}ller and
               Annie Rialland and
               Sebastian St{\"{u}}ker and
               Fran{\c{c}}ois Yvon and
               Marcely Zanon Boito},
  title     = {A Very Low Resource Language Speech Corpus for Computational Language
               Documentation Experiments},
  journal   = {CoRR},
  volume    = {abs/1710.03501},
  year      = {2017},
  url       = {http://arxiv.org/abs/1710.03501},
  archivePrefix = {arXiv},
  eprint    = {1710.03501},
  timestamp = {Tue, 16 Jan 2018 11:17:17 +0100},
  biburl    = {https://dblp.org/rec/bib/journals/corr/abs-1710-03501},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}
```

