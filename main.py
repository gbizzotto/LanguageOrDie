# -*- coding: utf-8 -*-

import time
import sys
import datetime
import locale
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

bot = None

def telegram_bot_handle(msg):
    global bot
    print str(datetime.datetime.now()), msg['from']['first_name'], '->', msg['text']
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
        import traceback
        print e
        print traceback.format_exc()
    session.sessions[session_id].lock.release()
    print str(datetime.datetime.now()), msg['from']['first_name'], '<-', output
    if len(output) != 0:
        bot.sendMessage(chat_id, output)
    else:
        print "Bot would have sent an empty message."

def console_main():
    sess = session.Session()
    output = session.Session.intro
    for x in sess.generator:
        output += x
        session.input.value = raw_input(output + ' > ').decode(sys.stdin.encoding)
        output = ''

def telegram_bot_main():    
    global bot
    session.deserialize('telegram-')
    bot = telepot.Bot(telegrambot.key)
    MessageLoop(bot, telegram_bot_handle).run_as_thread()
    print ('Listening ...')
    while 1:
        time.sleep(10)
        for id,sess in session.sessions.iteritems():
            sess.lock.acquire()
            try:
                if sess.dirty and sess.persist <= datetime.datetime.now():
                    session.serialize(str(id), sess)
                    sess.dirty = False
            except Exception, e:
                print 'Error in serialization:', e
            sess.lock.release()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'telegram':
        telegram_bot_main()
    else:
        console_main()