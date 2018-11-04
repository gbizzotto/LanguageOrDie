
import random
import sys
import unicodedata
from py2casefold import casefold

import kodule
import kb

def normalize_caseless(text):
    return unicodedata.normalize("NFKD", casefold(text))

def print_lesson(l, depth):
    print '  '*depth + 'Lesson', l.title, ':'
    for m in l.initial_material:
        print '  '*(depth+1) + 'Material:', m
    for tr in l.translations:
        print '  '*(depth+1) + 'Tr: ', unicode(tr)
    for t,tr in l.translations_by_tag.iteritems():
        print '  '*(depth+1) +'Tag:', t, tr

def print_kodule(k, depth):
    print '  '*depth + ('Course' if k.is_kourse else 'Module'), k.title, ':'
    for d in k.dependencies:
        print_kodule(d, depth+1)
    for l in k.kessons:
        print_lesson(l, depth+1)

def revise(knowledge_base):
    for kbi in knowledge_base.knowledge_items:
        question = random.choice(kbi.translation.natives)
        answers = knowledge_base.answers(question)
        while True:
            tentative = raw_input('(g for giveup) ' + question + ' > ').decode(sys.stdin.encoding)
            if tentative == 'g':
                print 'Translations:', ', '.join(answers)
                continue
            if normalize_caseless(tentative) not in [normalize_caseless(t) for t in answers]:
                print('Wrong answer')
                continue
            break

def study(kodule, root_kodule, knowledge_base):
    for dep in kodule.dependencies:
        study(dep, root_kodule, knowledge_base)

    revise(knowledge_base)

    for kesson in kodule.kessons:
        if knowledge_base.has_kesson(kesson):
            continue
        knowledge_base.add_kesson(kesson)
        print 'Adding module "' + kodule.title + '", lesson "' + kesson.title + '"'
        print 'Initial material:', ', '.join(kesson.initial_material)

def main():
    kodules = kodule.load_all('./kodules')
    kourses = [k for (n,k) in kodules.iteritems() if k.is_kourse]
    while(True):
        i=1
        for k in kourses:
            print str(i)+'.', k.title
            i += 1
        raw_choice = raw_input("Which kourse? ")
        if not raw_choice.isdigit():
            continue
        selected_item = int(raw_choice) - 1
        if selected_item < 0 or selected_item >= len(kourses):
            continue
        break
    knowledge_base = kb.KnowledgeBase() # TODO load from file/DB
    study(kourses[selected_item], kourses[selected_item], knowledge_base)

if __name__ == "__main__":
    main()