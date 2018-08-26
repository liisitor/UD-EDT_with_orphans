# UD-EDT_with_orphans

### For running:

python3 elliptical_sentences.py --files korpus1.conllu korpus2.conllu --exclusions-file exclude_sentences.txt --endings-file exclude_endings.txt

#### Orphan relations using program:

Orphan relations: 278

('orphan:obl', 128), ('orphan:advmod', 110), ('orphan:obj', 19), ('orphan:acl', 11), ('orphan:xcomp', 5), ('orphan:nsubj', 4), ('orphan:compound:prt', 1)


#### Orphan relations after fixing program output manually:

Orphan relations: 344

('orphan:obl', 151), ('orphan:advmod', 121), ('orphan:obj', 38), ('orphan:xcomp', 13), ('orphan:acl', 10), ('orphan:nsubj', 5), ('orphan:advcl', 3), ('orphan:parataxis', 2), ('orphan:compound:prt', 1)

Files (et-ud-dev_with_orphans.conllu, et-ud-test_with_orphans.conllu, et-ud-train_with_orphans.conllu) included in here are automatically and then manually annotated.
