# -*- coding: utf-8 -*-

import time
import sys
import datetime
import traceback
import locale
import util
util.APP_NAME = 'LanguageOrDie'

try:
    locale.setlocale(locale.LC_TIME, "pt_BR.utf8")
except:
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except:
        pass

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent

import telegrambot
import session
import signal

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)
  def exit_gracefully(self,signum, frame):
    self.kill_now = True

bot = None

def telegram_bot_handle(msg):
    global bot
    util.log(msg['from']['first_name'], '->', msg['text'])
    content_type, chat_type, chat_id = telepot.glance(msg)
    output = ''
    session_id = 'telegram-' + str(chat_id)
    if session_id not in session.sessions:
        session.sessions[session_id] = session.Session()
        output = session.Session.intro
    session.input.value = msg['text']
    session.sessions[session_id].lock.acquire()
    try:
        output += session.sessions[session_id].generator.next()
        session.sessions[session_id].touch()
    except Exception, e:
        util.log(e)
        util.log(traceback.format_exc())
    session.sessions[session_id].lock.release()
    for line in output.split('\n'):
        util.log(msg['from']['first_name'], '<-', line)
    if len(output) != 0:
        bot.sendMessage(chat_id, output)
    else:
        util.log("Bot would have sent an empty message.")

def console_main():
    sess = session.Session()
    output = session.Session.intro
    for x in sess.generator:
        output += x
        session.input.value = raw_input(output + u' > ').decode(sys.stdin.encoding)
        output = ''

def telegram_bot_main():    
    global bot
    killer = GracefulKiller()
    session.deserialize('telegram-')
    bot = telepot.Bot(telegrambot.key)
    MessageLoop(bot, telegram_bot_handle).run_as_thread()
    util.log('Listening ...')
    # serializer loop
    while not killer.kill_now:
        # check for SIGINT and SIGTERM for some time
        until = datetime.datetime.now() + datetime.timedelta(seconds=10)
        while datetime.datetime.now() < until and not killer.kill_now:
            time.sleep(0.1)
        # serialize students' progress so far
        for id,sess in session.sessions.iteritems():
            sess.lock.acquire()
            try:
                if sess.dirty and sess.persist <= datetime.datetime.now():
                    session.serialize(str(id), sess)
                    sess.dirty = False
            except Exception, e:
                util.log('Error in serialization:', e)
            sess.lock.release()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'telegram':
        telegram_bot_main()
    else:
        console_main()