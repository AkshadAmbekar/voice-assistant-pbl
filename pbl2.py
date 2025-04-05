import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import smtplib
import requests
from bs4 import BeautifulSoup
import sys
import psutil
import pyaudio
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pyautogui
import time
import re

NEWSDATA_API_KEY = "pub_78348fa8cf5f3cb028a545aa4643b5e4fc3a8"   # Replace with your News API key

def clean_text(text):
    """Removes special characters for TTS compatibility"""
    return re.sub(r'[^\x00-\x7F]+', '', text)

def getNewsNewsData(category="top"):
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&country=in&language=en&category={category}"

    try:
        response = requests.get(url)
        data = response.json()

        if "results" in data:
            articles = data["results"][:5]
            speak(f"Here are the top {category} news headlines.")
            for i, article in enumerate(articles, start=1):
                title = clean_text(article.get("title", "No title available"))
                print(f"{i}. {title}")
                speak(f"News number {i}: {title}")
                time.sleep(1.5)
        else:
            speak("Sorry, I couldn't fetch the news.")
            print("API response error:", data)
    except Exception as e:
        print(f"Error fetching news: {e}")
        speak("Something went wrong while getting the news.")



API_KEY = "fe057c28ff3077ebb41755e4bce2f959"  # Replace with your actual Weatherstack API key
BASE_URL = "http://api.weatherstack.com/current"

SPOTIFY_CLIENT_ID = "93eca05e29d843f38e73382887dbe1c4"
SPOTIFY_CLIENT_SECRET = "0fed1d9137ac4c7fb24843e79bc65032"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080/callback/"


engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state"
))


            
            
def play_spotify_playlist():
    playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"  # Example: Top Hits Playlist
    webbrowser.open(playlist_url)
    speak("Playing Spotify playlist.")
    
def play_on_spotify(song_name):
    search_url = f"spotify:search:{song_name.replace(' ', '%20')}"  # Open Spotify search
    os.system(f"start {search_url}")  # Opens in Spotify App
    speak(f"Playing {song_name} on Spotify.")
    



def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishMe():
    hour = int(datetime.datetime.now().hour)
    if hour < 12:
        speak("Good Morning!")
    elif hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am Jarvis. How may I help you?")

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
    
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
    except Exception:
        print("Say that again please...")
        return "None"
    return query.lower()

def sendEmail(to, content):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login('youremail@gmail.com', 'your-app-password')  # Use App Password
    server.sendmail('youremail@gmail.com', to, content)
    server.close()

if __name__ == "__main__":
    wishMe()

    while True:
        query = takeCommand()

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

        elif 'play music' in query:
            music_dir = r"C:\\Users\\uday dherange\\Downloads"
            songs = [song for song in os.listdir(music_dir) if song.endswith(".mp3")]
            if songs:
                os.startfile(os.path.join(music_dir, songs[0]))
            else:
                speak("No music files found!")
            break  

        elif 'current time' in query:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            speak(f"Sir, the time is {strTime}")
            break

        elif 'open chatbot' in query:
            webbrowser.open('https://chat.openai.com/')
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
                speak("Sorry, I couldn't send the email.")
            break  

        elif 'temperature' in query:
            speak("Which city's temperature do you want to know?")
            city = takeCommand()

            params = {"access_key": API_KEY, "query": city}
            response = requests.get(BASE_URL, params=params)
            weather_data = response.json()

            if "current" in weather_data:
                temp = weather_data["current"]["temperature"]
                speak(f"The current temperature in {city} is {temp} degrees Celsius.")
            else:
                speak("Sorry, I couldn't fetch the temperature. Please try again later.")
            break

        elif 'how much battery is left' in query or 'battery' in query:
            battery = psutil.sensors_battery()
            percentage = battery.percent
            speak(f"Sir, we have {percentage} percent battery left.")
            break
        
        elif 'play on spotify' in query:
            speak("Which song would you like to play?")
            song = takeCommand()
            play_on_spotify(song)
            break
    
            
        elif 'news' in query or 'headlines' in query:
            speak("Which category of news would you like? For example, technology, sports, or health.")
            category = takeCommand()
            getNewsNewsData(category)
            break
            



        


        elif 'close' in query or 'stop' in query:
            speak("Goodbye! Have a nice day.")
            sys.exit()
