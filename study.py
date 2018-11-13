# -*- coding: utf-8 -*-

import time
import sys
import datetime
import random

import util
import kodule
import kb

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
        tries = 0
        hint = ''
        while True:
            yield hint + u'\n(? para pedir ajuda)\n' + question
            tentative = input.value
            tries += 1
            if tentative == '?':
                hint = u'Tradução possível: ' + answers.get_possible_solution() + '\n'\
                    + u'(! para sair do curso)\n'
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
            if input.value == '!':
                return

    for x in revise(input, knowledge_base):
        yield x
        if input.value == '!':
            return

    for kesson in kodule.kessons:
        if knowledge_base.has_kesson(kesson):
            continue
        output = u'A próxima lição do módulo "' + kodule.title + u'", é "' + kesson.title + '"\n'\
            + u'Se não quiser estudá-la, digite "pular", senão, digite "ok".'
        yield output
        hidden = util.normalize_caseless(input.value) == 'pular'
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
            if input.value == '!':
                return
            output = ''
