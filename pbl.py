import pyttsx3 #pip install pyttsx3
import speech_recognition as sr #pip install speechRecognition
import datetime
import wikipedia #pip install wikipedia
import webbrowser
import os
import smtplib
import requests
from bs4 import BeautifulSoup 
import sys
import psutil
import pyaudio

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
# print(voices[1].id)
engine.setProperty('voice', voices[0].id)


def speak(audio):
    engine.say(audio)
    engine.runAndWait()


def wishMe():
    hour = int(datetime.datetime.now().hour)
    if hour>=0 and hour<12:
        speak("Good Morning!")

    elif hour>=12 and hour<18:
        speak("Good Afternoon!")   

    else:
        speak("Good Evening!")  

    speak("I am Jarvis. How may I help you")       

def takeCommand():
    #It takes microphone input from the user and returns string output

    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")    
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")

    except Exception as e:
        # print(e)    
        print("Say that again please...")  
        return "None"
    
    

    return query

def sendEmail(to, content):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login('youremail@gmail.com', 'your-password')
    server.sendmail('youremail@gmail.com', to, content)
    server.close()
    

if __name__ == "__main__":
    wishMe()
    while True:
    # if 1:
        query = takeCommand().lower()

        # Logic for executing tasks based on query
        if 'wikipedia' in query:
            speak('Searching Wikipedia...')
            query = query.replace("wikipedia", "")
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia")
            print(results)
            speak(results)

        elif 'open youtube' in query:
            webbrowser.open("youtube.com")
            break

        elif 'current weather' in query:
            webbrowser.open("https://www.youtube.com/watch?v=m0MD6Ukm0cQ")
            break

        elif 'open news' in query:
            webbrowser.open("https://www.youtube.com/watch?v=m0MD6Ukm0cQ")
            break

        elif "How to get rid of chashmish" in query:
            webbrowser.open("google.com")
            break


        elif 'play music' in query:
            music_dir = (r"C:\Users\uday dherange\Downloads\Starboy(PagalWorld).mp3")
            os.startfile(music_dir)
            break    
            

        elif 'current time' in query:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")    
            speak(f"Sir, the time is {strTime}")
            break

        elif 'open ppt' in query:
            os.startfile("C:\PBL voice assistant\PBL Final - 1.pptx")
            break

        elif 'open chat bot' in query :
            webbrowser.open('https://chat.openai.com/')
            break

        elif 'open report'in query:
            os.startfile("C:\PBL voice assistant\Voice Assistant Report Final.docx")
            break

        elif 'open mail' in query:
            webbrowser.open('https://mail.google.com/mail/u/0/#inbox')
            break
        elif 'email to yash' in query:
            try:
                speak("What should I say?")
                content = takeCommand()
                to = "sarangdeshpande.ssd@gmail.com"    
                sendEmail(to, content)
                speak("Email has been sent!")
            except Exception as e:
                print(e)
                speak("Sorry my friend. I am not able to send this email") 
                break  
        
        elif 'temperature' in query:
            speak("temperature of which city")
            x = takeCommand()
            search=("temperature in ",{x})
            url=f"https://www.google.com/search?q={search}"
            r=requests.get(url)
            data=BeautifulSoup(r.text,"html.parser")
            temp=data.find("div",class_="BNeawe").text
            speak(f"current {search} is {temp}")
            break
        
    
        elif 'how much battery is left' or 'battery' in query: 
            battery = psutil.sensors_battery()
            percentage = battery.percent
            speak (f"sir we have {percentage} percent battery left")    
            break
        
        elif 'close' or 'stop' in query:
            exit()