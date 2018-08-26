import os
from conllu import parse
import argparse
from os.path import join

COP_RELS = ['cop', 'nsubj:cop', 'csubj:cop']
NUM_PHRASE = ['kroon', 'aasta', 'kord', 'km', 'meeter']
IGNORE_DEPENDENTS = ['punct', 'cc', 'amod', 'advcl']
IGNORE_ORPHANS = ['cc', 'punct', 'amod', 'case', 'appos', 'flat', 'acl:relcl', 'compound', 'advcl',
                  'mark', 'ccomp', 'det', 'amod', 'conj', 'parataxis', 'orphan']


def file_to_list(filename):
    with open(filename) as f:
        return [line.strip() for line in f.readlines()]


def exclude_sentences(sentence, strings):
    for string in strings:
        if string in sentence:
            return True
    return False


def get_dependents(word, words):
    dep_list = []
    for dep in words:
        if word['id'] == dep['head']:
            dep_list.append(dep)
    return dep_list


def get_conj_count(verb, words):
    """
    Finds sentences, where one verb has many deps with 'conj' deprel
    """
    verb_deprels_xpos = []
    conj_deprels = []
    for conj in get_dependents(verb, words):
        if conj['deprel'] == 'conj' and conj['xpostag'] not in ['V']:
            verb_deprels_xpos.append(conj['xpostag'])
            for conj_dep in get_dependents(conj, words):
                if conj_dep['deprel'] == 'cc':
                    conj_deprels.append(conj_dep['deprel'])
    return len(set(verb_deprels_xpos)), len(conj_deprels)


def change_to_orphan(row_id, sentence, row_deprel):
    """
    Changes deprel to orphan:previous_deprel
    """
    rows = sentence.split("\n")
    new_deprel = "orphan:%s" % row_deprel
    for i, row in enumerate(rows):
        if not row.startswith("%s\t" % row_id):
            continue
        if row_deprel != 'orphan':
            if row_deprel in ['nmod', 'nummod']:
                rows[i] = row.replace(row_deprel, 'orphan:obl')
            else:
                rows[i] = row.replace(row_deprel, new_deprel)
    return "\n".join(rows)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Finds elliptical sentences and outputs orphan-annotated corpuses"
    )
    parser.add_argument(
        "--files",
        nargs="+", help="Corpus files to be processed"
    )
    parser.add_argument(
        "--results-path",
        help="Specifies where the result files will be stored", default="results"
    )
    parser.add_argument(
        "--exclusions-file",
        help="A file containing sentence identifiers (sent_id-s) for excluded sentences", required=True
    )
    parser.add_argument(
        "--endings-file",
        help="A file containing sentence endings which should be excluded", required=True
    )
    return parser.parse_args()


def annotate_orphan(sentence, verb_id, verb_dependent, words):
    '''
    Changes orphans in a sentence
    '''
    if verb_dependent['id'] == verb_id:
        for orphan in get_dependents(verb_dependent, words):
            if orphan['deprel'] not in IGNORE_ORPHANS:
                if orphan['deprel'] == 'nmod':
                    if orphan.get('feats').get('Case') in ['Gen', 'Ela', 'Nom']:
                        continue
                if orphan['deprel'] == 'nummod':
                    if verb_dependent['lemma'] in NUM_PHRASE:
                        continue
                sentence = change_to_orphan(orphan['id'], sentence, orphan['deprel'])
    return sentence


def find_copular_sentence(word, words):
    '''
    Finds whether a sentence has olema-verb ellipsis
    '''
    for olema in get_dependents(word, words):
        if not olema['lemma'] == 'olema':
            continue
        for conj in words:
            if conj['head'] == word['id'] or conj['head'] == olema['id'] \
                    and conj['deprel'] == 'conj' and conj['xpostag'] == word['xpostag']:
                conj_dependents = []
                for dep in get_dependents(conj, words):
                    conj_dependents.append(dep['deprel'])
                if 'cop' not in conj_dependents and (
                        'nsubj:cop' in conj_dependents or 'csubj:cop' in conj_dependents):
                    return True
    return False


def apply_main_rule(verb_dependent, words):
    '''
    Finds elliptical sentences for further annotation
    '''
    copula, sent_is_elliptical, verb_deps = False, False, set()
    if verb_dependent['deprel'] == 'conj' and verb_dependent['xpostag'] != 'V':
        for conj_dependent in get_dependents(verb_dependent, words):
            if conj_dependent['deprel'] in COP_RELS:
                copula = True
                break
            if conj_dependent['deprel'] not in IGNORE_DEPENDENTS:
                sent_is_elliptical = True
                verb_deps.add(verb_dependent['id'])
    return copula, sent_is_elliptical, verb_deps


def is_false_postive_ellips(verb_dependent, word):
    '''
    Finds sentences that are not actually elliptical
    '''
    cf = verb_dependent.get('feats')
    vf = word.get('feats')
    if cf and cf.get('Case') in ['Ela', 'Ine', 'All'] \
            and vf and vf.get('VerbForm') in ['Conv', 'Sup']:
        return True
    return False


def main(args):
    results_path = args.results_path
    files = args.files
    endings = file_to_list(args.endings_file)
    unsuitable_sentences = file_to_list(args.exclusions_file)

    elliptical_sentences = 0
    copula_sentences = 0
    all_sentences = 0

    if not os.path.exists(results_path):
        os.mkdir(results_path)

    output_elliptical_sentences = join(results_path, 'elliptical_sentences.conllu')
    output_copular_sentences = join(results_path, 'copula_sentences.conllu')
    with open(output_elliptical_sentences, 'w') as f, open(output_copular_sentences, 'w') as c:
        for file in files:
            output_whole_corpus = join(results_path, file.replace('.conllu', '') + '_with_orphans.conllu')
            with open(output_whole_corpus, 'a') as o:
                raw = open(file).read()
                sentences = raw.split("\n\n")
                for sentence in sentences:
                    all_sentences += 1
                    ignore_sentence = exclude_sentences(sentence, endings)
                    if ignore_sentence:
                        o.write(sentence + '\n\n')
                        continue
                    elliptical_sentence_found = False
                    copular_sentence_found = False
                    for words in parse(sentence):
                        for word in words:
                            if word['xpostag'] == 'V' and word['lemma'] != 'olema' and word['deprel'] not in ['xcomp',
                                                                                                              'csubj']:
                                # error handling
                                conj_counts = get_conj_count(word, words)
                                if conj_counts[0] > 1 or conj_counts[1] > 1:
                                    continue
                                adjectives_errors = [] # ignore, if there are more than 2 adjectives with 'conj' deprel
                                title_errors = []  # ignore, if dependents are quotation marks
                                for verb_dependent in get_dependents(word, words):
                                    if verb_dependent['deprel'] == 'conj' and verb_dependent['xpostag'] == 'A':
                                        adjectives_errors.append(verb_dependent)
                                    if word['deprel'] != 'root' and verb_dependent['form'] == '"':
                                        title_errors.append(verb_dependent)
                                    if is_false_postive_ellips(verb_dependent, word):
                                        break
                                    # main rule
                                    copula, sent_is_elliptical, verb_deps = apply_main_rule(verb_dependent, words)
                                    if copula or not sent_is_elliptical or len(adjectives_errors) >= 2 or len(
                                            title_errors) == 2:
                                        continue
                                    elliptical_sentence_found = True
                                    sentence_not_to_annotate = exclude_sentences(sentence, unsuitable_sentences)
                                    if sentence_not_to_annotate:
                                        continue
                                    for verb_id in verb_deps:
                                        sentence = annotate_orphan(sentence, verb_id, verb_dependent, words)
                            # finds olema-verb elliptical sentences
                            if word['xpostag'] == 'V':
                                continue
                            copular_sentence_found = find_copular_sentence(word, words)
                            if copular_sentence_found:
                                break

                        if copular_sentence_found:
                            copula_sentences += 1
                            c.write("%s\n\n" % sentence)
                            break
                        if elliptical_sentence_found:
                            elliptical_sentences += 1
                            f.write("%s\n\n" % sentence)
                            break

                    o.write(sentence + '\n\n')
    print("Elliptical sentences: %s " % (elliptical_sentences +copula_sentences))
    print("Percentage of elliptical sentences: %s " % round(((elliptical_sentences+copula_sentences) / all_sentences), 4))
    print("Olema-verb elliptical sentences: %s " % copula_sentences)
    print("Percentage of olema-verb elliptical sentences: %s " % round((copula_sentences / all_sentences), 4))
    print("Other verb elliptical sentences: %s " % elliptical_sentences)
    print("Percentage of other verb elliptical sentences: %s " % round((elliptical_sentences / all_sentences), 4))


if __name__ == "__main__":
    arguments = parse_arguments()
    main(arguments)
