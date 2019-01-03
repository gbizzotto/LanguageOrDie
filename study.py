# -*- coding: utf-8 -*-

import time
import sys, os
import datetime
import random

import util
import module
import kb

def revise(input, course, knowledge_base):
    kbis = knowledge_base.get_kbis_to_revise()
    if len(kbis) == 0:
        return

    while True:
        can_go_to_next_lesson = kbis[0].next_revision_datetime > datetime.datetime.now()
        # choose kbi
        kbs_past_time_count = 0
        while kbs_past_time_count<10 and kbs_past_time_count < len(kbis) and kbis[kbs_past_time_count].next_revision_datetime <= datetime.datetime.now()+datetime.timedelta(days=1):
            kbs_past_time_count += 1
        if kbs_past_time_count < 10:
            kbi_idx = 0
        else:
            kbi_idx = random.randint(0, kbs_past_time_count-1)
        kbi = kbis[kbi_idx]
        # prepare question and acceptable answers
        question, answers = knowledge_base.get_question_from_kbi(kbi)
        if question is None: # invalid
            del kbis[kbi_idx]
            continue
        # ask the question and check the answer
        tries = 0
        hint = ''
        while True:
            next_lesson_text = u'(+ para ir para a próxima lição)\n' if can_go_to_next_lesson else ''
            yield hint + u'\n(? para pedir ajuda)\n' \
                + next_lesson_text \
                + question
            tentative = input.value
            tries += 1
            if util.normalize_caseless(tentative) == '?':
                # help
                hint = u'Tradução possível: ' + answers.get_possible_solution() + '\n'\
                    + u'(! para sair do curso)\n'
                continue
            elif util.normalize_caseless(tentative) == '+':
                # next lesson
                for x in add_lesson(input, course, knowledge_base):
                    yield x
                kbis = knowledge_base.get_kbis_to_revise()
                continue
            if answers.accept(tentative):
                break
            hint = u'Resposta errada\n'
            continue
        # update knowledge base
        for kbi_involved in answers.kbis_involved:
            kbi_advancement = 0
            if tries == 1 and kbi_involved.next_revision_datetime <= datetime.datetime.now():
                kbi_advancement = 1
            kbi_involved.consolidate(kbi_advancement)
        del kbis[kbi_idx]
        kbis.add(kbi)

def get_next_unknown_lesson(module, knowledge_base):
    for dep in module.dependencies:
        kod, kess = get_next_unknown_lesson(dep, knowledge_base)
        if kess is not None:
            return kod, kess
    for lesson in module.lessons:
        lesson_pathname = os.path.join(module.pathname, lesson.title)
        if not knowledge_base.has_lesson(lesson_pathname):
            return module, lesson
    return None, None

def add_lesson(input, module, knowledge_base):
    module, lesson = get_next_unknown_lesson(module, knowledge_base)
    if lesson is None:
        return
    output = u'A próxima lição do módulo "' + module.title + u'", é "' + lesson.title + '"\n'
    if len(lesson.initial_material) > 0:
        output += u'Material inicial:\n'
        for im in lesson.initial_material:
            output += '    ' + im + '\n'
    else:
        output = u'Não há material inicial para esta lição.\n'
    output += u'\n'\
        + u'Se preferir continuar revisando por mais uma hora, digite "revisar".\n'\
        + u'Se já tiver domínio do material, digite "pular".\n'\
        + u'Se quiser estudar esta lição, digite "ok" ou qualquer outra coisa.'
    yield output
    if util.normalize_caseless(input.value) == 'revisar':
        return
    skip = (util.normalize_caseless(input.value) == 'pular')
    lesson_pathname = os.path.join(module.pathname, lesson.title)
    knowledge_base.add_lesson(lesson, lesson_pathname, skip)
