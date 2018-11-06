
import random
import sys
import unicodedata
import datetime
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
    kbis = knowledge_base.get_kbis_to_revise()
    if len(kbis) == 0:
        return
    while kbis[0].next_revision_time <= datetime.datetime.now():
        kbi = kbis[0]
        if kbi.translation.secret is False:
            question = random.choice(kbi.translation.natives)
            answers = knowledge_base.answers(question)
            tries = 0
            while True:
                tentative = raw_input('(g for giveup) ' + question + ' > ').decode(sys.stdin.encoding)
                tries += 1
                if tentative == 'g':
                    print 'Translations:', ', '.join(answers)
                    continue
                if normalize_caseless(tentative) not in [normalize_caseless(t) for t in answers]:
                    print('Wrong answer')
                    continue
                break
        del kbis[0]
        if tries == 1:
            kbi.got_it_right_on_1st_try()
        else:
            kbi.got_it_right_eventually()
        kbis.add(kbi)
        # print('See you around', kbi.next_revision_time)

def study(kodule, root_kodule, knowledge_base):
    for dep in kodule.dependencies:
        study(dep, root_kodule, knowledge_base)

    while revise(knowledge_base):
        pass

    for kesson in kodule.kessons:
        if knowledge_base.has_kesson(kesson):
            continue
        knowledge_base.add_kesson(kesson)
        print('Adding module "' + kodule.title + '", lesson "' + kesson.title + '"')
        print('Initial material:')
        for im in kesson.initial_material:
            print '  ' + im

    while revise(knowledge_base):
        pass

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
    print "You're all set for now. Please come back around", str(knowledge_base.get_next_revision_time().time())[:5]

if __name__ == "__main__":
    main()