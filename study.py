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
    revise_more = False
    while kbis[0].next_revision_datetime <= datetime.datetime.now() + datetime.timedelta(days=1):
        if not revise_more and kbis[0].next_revision_datetime > datetime.datetime.now():
            yield u'Já revisou o suficiente. Pode parar por aqui e voltar mais tarde ou continuar consolidando o que aprendeu.\n'\
                u'Responda "ok" se quiser continuar'
            if util.normalize_caseless(input.value) == 'ok':
                revise_more = True
            else:
                return
        kbs_past_time_count = 0
        while kbs_past_time_count<10 and kbs_past_time_count < len(kbis) and kbis[kbs_past_time_count].next_revision_datetime <= datetime.datetime.now()+datetime.timedelta(days=1):
            kbs_past_time_count += 1
        if kbs_past_time_count < 10:
            kbi_idx = 0
        else:
            kbi_idx = random.randint(0, kbs_past_time_count-1)
        kbi = kbis[kbi_idx]
        question, answers = knowledge_base.get_question_from_kbi(kbi)
        if question is None:
            del kbis[kbi_idx]
            continue
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
        for kbi_involved in answers.kbis_involved:
            kbi_advancement = 0
            if tries == 1 and kbi_involved.next_revision_datetime <= datetime.datetime.now():
                kbi_advancement = 1
            kbi_involved.consolidate(kbi_advancement)
        del kbis[kbi_idx]
        kbis.add(kbi)


def study(input, kodule, knowledge_base, do_revise=True):
    if do_revise:
        for x in revise(input, knowledge_base):
            yield x
            if input.value == '!':
                return

    for dep in kodule.dependencies:
        for x in study(input, dep, knowledge_base, do_revise=False):
            yield x
            if input.value == '!':
                return

    for kesson in kodule.kessons:
        kesson_pathname = kodule.pathname + '/' + kesson.title
        if knowledge_base.has_kesson(kesson_pathname):
            continue
        output = u'A próxima lição do módulo "' + kodule.title + u'", é "' + kesson.title + '"\n'\
            + u'Se não quiser estudá-la, digite "pular", senão, digite "ok".'
        yield output
        skip = (util.normalize_caseless(input.value) == 'pular')
        knowledge_base.add_kesson(kesson, kesson_pathname, skip)
        if not skip:
            if len(kesson.initial_material) > 0:
                output = u'Material inicial:\n'
                for im in kesson.initial_material:
                    output += '    ' + im + '\n'
            else:
                output = u'Não há material inicial.'
        for x in revise(input, knowledge_base):
            yield output + x
            if input.value == '!':
                return
            output = ''
