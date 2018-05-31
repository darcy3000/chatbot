import aiml
import os
from gtts import gTTS
import urllib
import json
from google import google
#from geotext import GeoText
import pyowm
from nltk.tag import pos_tag
import speech_recognition as sr
import time
from threading import Thread
import threading
from multiprocessing.pool import ThreadPool
import os
import signal
import sqlite3
#-----------------------------------------------------------------------------------


r = sr.Recognizer()
kernel = aiml.Kernel()
query = ""#TO store the question of the user
mutex =1 #TO resolve clashes
semaphore = threading.Semaphore()
mic_semaphore = threading.Semaphore()
tlock = threading.Lock()
trap =1
weather_trap=1
owm = pyowm.OWM('7e239dce9ab05ccd49418118e01f4140')

"""
con_main = sqlite3.connect("conversation.db")
cur_main = con_main.cursor()
cur_main.execute("CREATE TABLE corpus(question TEXT,answer TEXT,verdict TEXT)")
con_main.commit()
con_main.close()
"""


if os.path.isfile("bot_brain.brn"):
    kernel.bootstrap(brainFile = "bot_brain.brn")
else:
    kernel.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml b")
    kernel.saveBrain("bot_brain.brn")


#------------------------------------------------------------------------------------

def weather(message):
    try:
        sentence = message
        tagged_sent = pos_tag(sentence.split())
        places = [word for word, pos in tagged_sent if pos == 'NNP']
        # places = GeoText(message)
        # print(places.cities)
        for citi in places:
            observation = owm.weather_at_place(citi)
            w = observation.get_weather()
            #print('Wind Speed : '+ str(w.get_wind()["u'speed"]))
            print('Current Temperature : '+ str(w.get_temperature('celsius')['temp']))
            print('Max Temperature : ' + str(w.get_temperature('celsius')['temp_max']))
            print('Min Temperature : ' + str(w.get_temperature('celsius')['temp_min']))
            print("Humidity : " + str(w.get_humidity()))

    except Exception as e:
        print(e)
        say_this_bajaj("Please give a valid location")
        pass

#-------------------------------------------------------------------------------------
def search_internet(message):
    # searching
    search_results = google.search(message)

    for en in search_results:
        print(en.name)
        print(en.link)
        # print(en.descripition)
        print("\n")

    tts = gTTS(text='this is what I found on the internet', lang='en')
    tts.save("audio.mp3")
    os.system("mpg321 audio.mp3")

#--------------------------------------------------------------------------------------
def listen_keyboard():
    while True:

        message = input("Enter input")
        query=message#GOing to be used in main
        print("Keyboard going to acquire lock"+query)
        semaphore.acquire()
        print("Keyboard has to acquire lock" + query)
        mutex=0
        mic_semaphore.acquire()
        processing_keyboard(query)

        semaphore.release()

        time.sleep(1)
        mutex=1

    return message

#--------------------------------------------------------------------------------------
def listen_microphone1():
    print("Second thread spawned")
    global trap
    global weather_trap
    while True:

        #time.sleep(2)
        print("Speak something")

        message=''
        while(message==''):
            with sr.Microphone() as source:
                audio = r.listen(source)

            try:
                message = r.recognize_google(audio)
            except:
                pass

        query=message#Going to be used in main
        print("Mic going to acquire lock"+str(mutex))
        semaphore.acquire()
        mic_semaphore.acquire()
        """if(weather_trap==0):
            weather_trap=1
            processing_mic(query)
            mic_semaphore.release()
            semaphore.release()
            continue"""
        if( trap == 0):
            print("Mic sent back")
            semaphore.release()
            mic_semaphore.release()
            trap=1
            continue

        print("GOing to process"+query)
        processing_mic(query)
        mic_semaphore.release()
        semaphore.release()

    return message

def listen_microphone2():
    print("Speak something 2")
    message = ''
    while (message == ''):
        with sr.Microphone() as source:
            audio = r.listen(source)

        try:
            message = r.recognize_google(audio)
        except:
            pass
    #query = message  # Going to be used in main
    #processing(query)

    return message

#--------------------------------------------------------------------------------------
def say_this_bajaj(message):
    tts = gTTS(text=message, lang='en')
    tts.save("audio.mp3")
    os.system("mpg321 audio.mp3")


'''
kernel.learn("std-startup.xml")
kernel.respond("load aiml b")'''
owm = pyowm.OWM('7e239dce9ab05ccd49418118e01f4140')



# kernel now ready for use


    #message = raw_input("Enter your message >> ")
    #Creating threads for multithreading
def Main():
    key_input = Thread(target=listen_keyboard)
    voice_input = Thread(target=listen_microphone1)
    voice_input.start()
    print("GOing to start second thread")
    key_input.start()

def processing_keyboard(query):
    global trap
    global weather_trap
    while(query==""):
        pass


    print("Keyboard "+query)
    if(query=='quit'):
        os.kill(os.getpid(), signal.SIGUSR1)

    #e = pyttsx.init()
        #e.say(kernel.respond(message))
        #e.runAndWait()
        #espeak.synth(kernel.respond(message))

    if(query.find('weather' )!=-1 or query.find('Weather' )!=-1):
        try:

            weather(query)
            weather_trap = 0
            mic_semaphore.release()
            return
        except:
            pass

    #text-to-speech using gTT
    answer = kernel.respond(query)


    print (answer)
    say_this_bajaj(answer)
    text = 'do you want me to search the internet for this query?'
    say_this_bajaj(text)
    #y_or_n = raw_input("Enter yes or no. >>>")
    print("Enter yes or no. >>>")
    trap=0
    y_or_n = listen_microphone2()

    print(y_or_n)
    # Creating a connection to database
    con = sqlite3.connect("conversation.db")
    cur = con.cursor()

    cur.execute("INSERT INTO corpus(question,answer,verdict) VALUES(?,?,?)",(query, answer, y_or_n))  # Adding to database
    con.commit()
    con.close()
    if(y_or_n=='yes' or y_or_n=='Yes'):
        search_internet(query)
    query=""
    mic_semaphore.release()

def processing_mic(query):
    global trap
    while(query==""):
        pass


    print(query)
    if(query=='quit'):
        os.kill(os.getpid(),signal.SIGUSR1)

    #e = pyttsx.init()
        #e.say(kernel.respond(message))
        #e.runAndWait()
        #espeak.synth(kernel.respond(message))

    if(query.find('weather' )!=-1 or query.find('Weather' )!=-1):
        try:
            weather(query)
            return
        except:
            pass

    #text-to-speech using gTT
    answer = kernel.respond(query)


    print (answer)
    say_this_bajaj(answer)
    text = 'do you want me to search the internet for this query?'
    say_this_bajaj(text)
    #y_or_n = raw_input("Enter yes or no. >>>")
    print("Enter yes or no. >>>")

    y_or_n = listen_microphone2()

    print(y_or_n)
    # Creating a connection to database
    con = sqlite3.connect("conversation.db")
    cur = con.cursor()

    cur.execute("INSERT INTO corpus(question,answer,verdict) VALUES(?,?,?)",(query,answer,y_or_n))  # Adding to database
    con.commit()
    con.close()

    if(y_or_n=='yes' or y_or_n=='Yes'):
        search_internet(query)
    query=""

if __name__ == '__main__':
    # message = listen_keyboard()
    print('Try Writing or Saying Something >>>>')
    Main()