
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
                output = ''
                for k in kourses:
                    output = output + str(i)+'. ' + k.title + '\n'
                    i += 1
                yield output + "Which kourse?"
                if not input.value.isdigit():
                    continue
                selected_item = int(input.value) - 1
                if selected_item < 0 or selected_item >= len(kourses):
                    continue
                break
            # study kourse
            kourse = kourses[selected_item]
            if kourse.title not in self.kbs:
                self.kbs[kourse.title] = kb.KnowledgeBase() # TODO load from file/DB
            for x in study.study(input, kourse, kourse, self.kbs[kourse.title]):
                yield x
            yield "You're all set with '"\
                + kourse.title\
                + "' for now. Please come back around "\
                + str( (self.kbs[kourse.title].get_next_revision_time() + datetime.timedelta(seconds=59)).time())[:5]

sessions = {}
bot = None

def handle(msg):
    global sessions
    global bot
    global input
    print msg
    content_type, chat_type, chat_id = telepot.glance(msg)
    if chat_id not in sessions:
        sessions[chat_id] = Session()
    input.value = msg['text']
    bot.sendMessage(chat_id, sessions[chat_id].generator.next())

def console_main():
    global input
    session = Session()
    for x in session.generator:
        input.value = raw_input(x + ' > ').decode(sys.stdin.encoding)

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