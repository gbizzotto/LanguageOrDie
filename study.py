# -*- coding: utf-8 -*-

import time
import sys
import datetime
import random

import kodule
import kb

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
        if len(kbis) < 10:
            kbi_idx = 0
        else:
            kbi_idx = random.randint(0, 5)
        kbi = kbis[kbi_idx]
        question, answers = knowledge_base.get_question_from_kbi(kbi)
        # random.choice(kbi.translation.natives)
        # answers = knowledge_base.answers(question)
        tries = 0
        hint = ''
        while True:
            yield hint + u'\n(? para pedir ajuda)\n' + question
            tentative = input.value
            tries += 1
            if tentative == '?':
                hint = u'Traduções: ' + answers.get_possible_solution() + '\n'
                continue
            if answers.accept(tentative):
                break
            hint = u'Resposta errada\n'
            continue
        del kbis[kbi_idx]
        if tries == 1:
            kbi.got_it_right_on_1st_try()
        else:
            kbi.got_it_right_eventually()
        kbis.add(kbi)

def study(input, kodule, root_kodule, knowledge_base):
    for dep in kodule.dependencies:
        for x in study(input, dep, root_kodule, knowledge_base):
            yield x

    for x in revise(input, knowledge_base):
        yield x

    for kesson in kodule.kessons:
        if knowledge_base.has_kesson(kesson):
            continue
        output = u'A próxima lição do módulo "' + kodule.title + u'", é "' + kesson.title + '"\n'\
            + u'Se não quiser estudá-la, digite "pular", senão, digite "ok".'
        yield output
        hidden = input.value == 'pular'
        knowledge_base.add_kesson(kesson, hidden)
        if not hidden:
            if len(kesson.initial_material) > 0:
                output = u'Material inicial:\n'
                for im in kesson.initial_material:
                    output += '    ' + im + '\n'
            else:
                output = 'Não há material inicial.'
        for x in revise(input, knowledge_base):
            yield output + x
            output = ''
