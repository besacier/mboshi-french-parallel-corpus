# mboshi-french-parallel-corpus

* full_corpus_newsplit:   contains the wav in mboshi, the linguists' transcriptions and the french translations ; this part is clean and has been checked carefully

* forced_alignments_supervised_spkr:   contains the forced alignements between mboshi speech and mboshi transcripts… might be useful if you want to score word or phone discovery from speech but …… you should consider this as a « silver » standard rather than a « gold standard » since we're not completely happy with these forced alignements yet (well, they are imperfect forced alignements obtained from a small corpus, etc.)…. so we're currently considering a possible improvement of these 

* ZRC_scoring: contains scripts + ref files to score spoken word discovery with the Zero Resource Challenge Metrics (see http://zerospeech.com and http://sapience.dec.ens.fr/bootphon/2017/page_3.html if you’re not familiar with these metrics)
the ref files for ZCR metrics were obtained from the above forced alignements



