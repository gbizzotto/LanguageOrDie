# -*- coding: utf-8 -*-

import threading
import datetime
import json
import os
import traceback
import sys  

import util
import study
import module
import kb

reload(sys)  
sys.setdefaultencoding('utf8')

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
                # choose course
                while True:
                    i=1
                    output = u'Cursos disponíveis:\n\n'
                    for k in module.all_courses:
                        output = output + str(i)+'. ' + k.title + '\n'
                        i += 1
                    yield output + u"\nO que quer estudar? Digite o número do curso."
                    if not input.value.isdigit():
                        continue
                    selected_item = int(input.value) - 1
                    if selected_item < 0 or selected_item >= len(module.all_courses):
                        continue
                    break
                # study course
                output = ''
                course = module.all_courses[selected_item]
                if course.pathname not in self.kbs:
                    yield course.title + u':\n' \
                        + u' '.join(course.initial_material) \
                        + u'\n\n' \
                        + u'Envie "ok" para começar o curso ou "não" para voltar para a escolha do curso.'
                    if util.normalize_caseless(input.value) != 'ok':
                        continue
                    self.kbs[course.pathname] = kb.KnowledgeBase() # TODO load from file/DB
                    for x in study.add_lesson(input, course, self.kbs[course.pathname]):
                        yield x
                else:
                    output += u'Vamos continuar!\n\n'

                for x in study.revise(input, course, self.kbs[course.pathname]):
                    yield output + x
                    output = u''
                    if input.value == '!':
                        break

            except Exception, e:
                import traceback
                util.log(e)
                util.log(unicode(traceback.format_exc()))
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
            