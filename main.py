# -*- coding: utf-8 -*-

import time
import requests
import json
import sys
import unicodedata
import datetime

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent

import study
import kodule
import kb
import telegrambot

class Input:
    def __init__(self):
        self.value = ''
input = Input()

class Session:
    def __init__(self):
        self.generator = self.run()
        self.kbs = {}
        self.intro = u"Oi! Sou o @DaLanguageBot.\n"\
            + u"Sou professor. Já posso ministrar alguns cursos.\n"\
            + u"Nada muito elaborado por enquanto, pois estou apenas em fase de testes.\n"\
            + u"\n"\
            + u"Cada curso é dividido em módulos, lições e itens. Cada item será apresendato a você várias vezes, "\
            + u"a intervalos cada vez maiores, de maneira que consolide o conhecimento aos poucos."\
            + u"Se escolher um curso de idioma, para cada idem apresentado, responda com a tradução ou desista mandando o caractere '?'\n"\
            + u"\n"\
            + u"Boas aulas!\n\n"

    def next(self):
        return self.generator.next()

    def run(self):
        global input
        kodules = kodule.load_all('./kodules')
        kourses = [k for (n,k) in kodules.iteritems() if k.is_kourse]
        while True:
            # choose kourse
            while True:
                i=1
                output = u'Cursos disponíveis:\n\n'
                for k in kourses:
                    output = output + str(i)+'. ' + k.title + '\n'
                    i += 1
                yield output + u"\nO que quer estudar? Digite o número do curso."
                if not input.value.isdigit():
                    continue
                selected_item = int(input.value) - 1
                if selected_item < 0 or selected_item >= len(kourses):
                    continue
                break
            # study kourse
            output = ''
            kourse = kourses[selected_item]
            if kourse.title not in self.kbs:
                self.kbs[kourse.title] = kb.KnowledgeBase() # TODO load from file/DB
                yield '\n' \
                    + kourse.title + ':\n' \
                    + ' '.join(kourse.initial_material) \
                    + '\n\n' \
                    + u'Envie "ok" para começar o curso ou "não" para voltar para a escolha do curso.'
                if study.normalize_caseless(input.value) != 'ok':
                    continue
            else:
                output += 'Vamos continuar!\n\n'
            for x in study.study(input, kourse, kourse, self.kbs[kourse.title]):
                yield output + x
            yield u"Já viu material o suficiente, chega de '" \
                + kourse.title \
                + u"' por enquanto.\n" \
                + u"Por favor volte às " \
                + str( (self.kbs[kourse.title].get_next_revision_time() + datetime.timedelta(seconds=59)).time())[:5] \
                + u" para revisar o que aprendeu até agora e ver coisas novas!"

sessions = {}
bot = None

def handle(msg):
    global sessions
    global bot
    global input
    print(str(datetim.datetime.now()), msg['from']['first_name'], '->', msg['text'])
    content_type, chat_type, chat_id = telepot.glance(msg)
    output = ''
    if chat_id not in sessions:
        sessions[chat_id] = Session()
        output = sessions[chat_id].intro
    input.value = msg['text']
    output += sessions[chat_id].generator.next()
    print(str(datetim.datetime.now()), msg['from']['first_name'], '<-', output)
    bot.sendMessage(chat_id, output)

def console_main():
    global input
    session = Session()
    output = session.intro
    for x in session.generator:
        output += x
        input.value = raw_input(output + ' > ').decode(sys.stdin.encoding)
        output = ''

def bot_main():
    global bot
    bot = telepot.Bot(telegrambot.key)
    # MessageLoop(bot, {'chat': handle}).run_as_thread()
    MessageLoop(bot, handle).run_as_thread()
    print ('Listening ...')
    while 1:
        time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'bot':
        bot_main()
    else:
        console_main()