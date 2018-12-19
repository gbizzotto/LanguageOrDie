# -*- coding: utf-8 -*-

import threading
import datetime
import json
import os
import traceback

import util
import study
import kodule
import kb

sessions = {}

class Input:
    def __init__(self):
        self.value = ''
input = Input()

class Session:
    intro = u"Oi! Sou o @DaLanguageBot.\n"\
        + u"Sou professor. Já posso ministrar alguns cursos.\n"\
        + u"Nada muito elaborado por enquanto, pois estou apenas em fase de testes.\n"\
        + u"\n"\
        + u"Cada curso é dividido em módulos, lições e itens. Cada item será apresendato a você várias vezes, "\
        + u"a intervalos cada vez maiores, de maneira que consolide o conhecimento aos poucos."\
        + u"Se escolher um curso de idioma, para cada idem apresentado, responda com a tradução ou desista mandando o caractere '?'\n"\
        + u"\n"\
        + u"Boas aulas!\n\n"

    def __init__(self):
        self.lock = threading.Lock()
        self.touch()
        self.generator = self.run()
        self.kbs = {}

    def touch(self):
        self.dirty = True
        self.persist = datetime.datetime.now() + datetime.timedelta(seconds=2)

    def serialize(self):
        return {k:v.serialize() for k,v in self.kbs.iteritems()}

    def deserialize(self, j):
        self.kbs = {k:kb.KnowledgeBase().deserialize(v, k) for k,v in j.iteritems()}
        self.dirty = False
        return self

    def next(self):
        return self.generator.next()

    def run(self):
        global input
        while True:
            try:
                # choose kourse
                while True:
                    i=1
                    output = u'Cursos disponíveis:\n\n'
                    for k in kodule.all_kourses:
                        output = output + str(i)+'. ' + k.title + '\n'
                        i += 1
                    yield output + u"\nO que quer estudar? Digite o número do curso."
                    if not input.value.isdigit():
                        continue
                    selected_item = int(input.value) - 1
                    if selected_item < 0 or selected_item >= len(kodule.all_kourses):
                        continue
                    break
                # study kourse
                output = ''
                kourse = kodule.all_kourses[selected_item]
                if kourse.pathname not in self.kbs:
                    yield kourse.title + ':\n' \
                        + ' '.join(kourse.initial_material) \
                        + '\n\n' \
                        + u'Envie "ok" para começar o curso ou "não" para voltar para a escolha do curso.'
                    if util.normalize_caseless(input.value) != 'ok':
                        continue
                    self.kbs[kourse.pathname] = kb.KnowledgeBase() # TODO load from file/DB
                else:
                    output += 'Vamos continuar!\n\n'
                for x in study.study(input, kourse, self.kbs[kourse.pathname]):
                    yield output + x
                    output = ''

                now = datetime.datetime.now()
                be_back_datetime = self.kbs[kourse.pathname].get_next_revision_datetime() + datetime.timedelta(seconds=59)
                if be_back_datetime >= now + datetime.timedelta(days=7):
                    be_back_str = u'em ' + unicode(be_back_datetime.date())
                elif be_back_datetime.day == (now + datetime.timedelta(days=1)).day:
                    util.log(be_back_datetime)
                    be_back_str = unicode(datetime.datetime.strftime(be_back_datetime, "%A")) + u' às ' + unicode(be_back_datetime.time())[:5]
                else:
                    be_back_str = u'as ' + unicode(be_back_datetime.time())[:5]

                yield u"Já viu material o suficiente, chega de '" \
                    + kourse.title \
                    + u"' por enquanto.\n" \
                    + u"Por favor volte " \
                    + be_back_str \
                    + u" para revisar o que aprendeu até agora e ver coisas novas!"
            except Exception, e:
                import traceback
                util.log(e)
                util.log(traceback.format_exc())
                yield u'Me perdoe, tive um problema que me impediu de continuar. Vamos voltar do início por favor?'


def serialize(name, sess):
    s = json.dumps(sess.serialize(), indent=2, ensure_ascii=False).encode('utf8')
    with open('./sessions/'+name+'.session', "w") as out:
        out.write(s)

def deserialize(prefix):
    global sessions
    for (dirpath, dirnames, filenames) in os.walk('./sessions/'):
        for f in [f for f in filenames if f.startswith('telegram-') and f.endswith('.session')]:
            fullname = os.path.join(dirpath, f)
            id = f[:-len('.session')]
            s = ''
            with open(fullname, "r") as fin:
                s = fin.read()
            j = json.loads(s, encoding='utf-8')
            sessions[id] = Session().deserialize(j)
            