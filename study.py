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
            next_lesson_text = u'\n3. Próxima lição' if can_go_to_next_lesson else ''
            yield hint\
                + u'\n1. Sair do curso' \
                + u'\n2. Pedir ajuda' \
                + next_lesson_text \
                + '\n\n' \
                + question
            if isinstance(input.value, int):
                if input.value == 2:
                    # help
                    hint = u'Tradução possível: ' + answers.get_possible_solution() + '\n'
                    continue
                if input.value == 3 and len(next_lesson_text) > 0:
                    # next lesson
                    for x in add_lesson(input, course, knowledge_base):
                        yield x
                    kbis = knowledge_base.get_kbis_to_revise()
                    continue
            tentative = input.value
            tries += 1
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

def learn(input, course, knowledge_base, partial_knowledge_base):
    kbis = partial_knowledge_base.get_kbis_to_revise()
    if len(kbis) == 0:
        return

    while kbis[0].next_revision_datetime <= datetime.datetime.now():
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
            yield hint\
                + u'\n1. Sair do curso' \
                + u'\n2. Pedir ajuda' \
                + '\n\n' \
                + question
            if isinstance(input.value, int):
                if input.value == 2:
                    # help
                    hint = u'Tradução possível: ' + answers.get_possible_solution() + '\n'
                    continue
            tentative = input.value
            tries += 1
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

def add_lesson(input, module, knowledge_base, can_revise=True):
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
    output += u'\n1. Sair do curso'\
        + u'\n2. Estudar essa lição'\
        + u'\n3. Pular (já tenho domínio do material)'
    if can_revise:
        output += u'\n4. Continuar revisando'
    yield output
    if isinstance(input.value, int):
        skip = input.value == 3
        if input.value in [1,4]:
            return
    lesson_pathname = os.path.join(module.pathname, lesson.title)
    partial_knowledge_base = kb.KnowledgeBase()
    partial_knowledge_base.add_lesson(lesson, lesson_pathname, skip)
    if not skip:
        for x in learn(input, module, knowledge_base, partial_knowledge_base):
            yield x
            if isinstance(input.value, int) and input.value == 1:
                return
    knowledge_base.incorporate(partial_knowledge_base)
