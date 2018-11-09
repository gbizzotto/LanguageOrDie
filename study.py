# -*- coding: utf-8 -*-

import time
import random
import sys
import unicodedata
import datetime

from py2casefold import casefold

import kodule
import kb

def normalize_caseless(text):
    return unicodedata.normalize("NFKD", casefold(text))

# def print_lesson(l, depth):
#     print '  '*depth + 'Lesson', l.title, ':'
#     for m in l.initial_material:
#         print '  '*(depth+1) + 'Material:', m
#     for tr in l.translations:
#         print '  '*(depth+1) + 'Tr: ', unicode(tr)
#     for t,tr in l.translations_by_tag.iteritems():
#         print '  '*(depth+1) +'Tag:', t, tr

# def print_kodule(k, depth):
#     print '  '*depth + ('Course' if k.is_kourse else 'Module'), k.title, ':'
#     for d in k.dependencies:
#         print_kodule(d, depth+1)
#     for l in k.kessons:
#         print_lesson(l, depth+1)

def revise(input, knowledge_base):
    kbis = knowledge_base.get_kbis_to_revise()
    if len(kbis) == 0:
        return
    while kbis[0].next_revision_time <= datetime.datetime.now():
        kbi = kbis[0]
        if kbi.translation.secret is False:
            question = random.choice(kbi.translation.natives)
            answers = knowledge_base.answers(question)
            tries = 0
            hint = ''
            while True:
                yield hint + u'\n(? para pedir ajuda)\n' + question
                tentative = input.value
                tries += 1
                if tentative == '?':
                    hint = u'Traduções: ' + ', '.join(answers) + '\n'
                    continue
                if normalize_caseless(tentative) not in [normalize_caseless(t) for t in answers]:
                    hint = u'Resposta errada\n'
                    continue
                break
        del kbis[0]
        if tries == 1:
            kbi.got_it_right_on_1st_try()
        else:
            kbi.got_it_right_eventually()
        kbis.add(kbi)
        # print 'See you around', kbi.next_revision_time

def study(input, kodule, root_kodule, knowledge_base):
    for dep in kodule.dependencies:
        for x in study(input, dep, root_kodule, knowledge_base):
            yield x

    for x in revise(input, knowledge_base):
        yield x

    for kesson in kodule.kessons:
        if knowledge_base.has_kesson(kesson):
            continue
        knowledge_base.add_kesson(kesson)
        output = u'Acrescentando módulo "' + kodule.title + u'", lição "' + kesson.title + '"\n'
        output += u'Material inicial:\n'
        for im in kesson.initial_material:
            output += '    ' + im + '\n'
        for x in revise(input, knowledge_base):
            yield output + x
            output = ''
