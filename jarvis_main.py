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
from googlesearch import search

NEWSDATA_API_KEY = "pub_78348fa8cf5f3cb028a545aa4643b5e4fc3a8"
API_KEY = "fe057c28ff3077ebb41755e4bce2f959"
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

def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

def getNewsNewsData():
    news_url = "https://newsapi.org/v2/top-headlines?country=in&apiKey=pub_78348fa8cf5f3cb028a545aa4643b5e4fc3a8"
    response = requests.get(news_url)
    data = response.json()

    articles = data.get("articles", [])[:5]
    headlines = []

    for article in articles:
        title = article["title"]
        headlines.append(title)
        speak(title)

    return headlines


def detect_hotword(hotword="jarvis"):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        print("Listening for hotword...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        detected_text = recognizer.recognize_google(audio, language='en-in').lower()
        print(f"You said: {detected_text}")
        if hotword in detected_text:
            print(f"Hotword '{hotword}' detected.")
            return True
        else:
            return False
    except sr.UnknownValueError:
        return False
    except sr.RequestError as e:
        print(f"Hotword detection error: {e}")
        return False
    
def google_search_and_speak(query):
    speak(f"Searching Google for {query}")
    try:
        for result in search(query, num_results=1):
            speak("Here's what I found:")
            speak(result)
            return result
    except Exception as e:
        speak("Sorry, I couldn't perform the search.")
        return None
    

def play_spotify_playlist():
    playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    webbrowser.open(playlist_url)
    speak("Playing Spotify playlist.")

def play_on_spotify(song_name):
    try:
        if not song_name:
            speak("You didn't specify a song.")
            return
        # Try using the Spotify URI scheme
        search_url = f"spotify:search:{song_name.replace(' ', '%20')}"
        result = os.system(f"start {search_url}")
        if result != 0:
            # Fallback: open Spotify search in web browser
            web_url = f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}"
            webbrowser.open(web_url)
            speak(f"Opening {song_name} on Spotify Web.")
        else:
            speak(f"Playing {song_name} on Spotify.")
    except Exception as e:
        print("Error playing on Spotify:", e)
        speak("Sorry, I couldn't play that on Spotify.")


def tell_joke():
    url = "https://v2.jokeapi.dev/joke/Any?format=json"
    try:
        response = requests.get(url)
        data = response.json()
        if data["type"] == "single":
            joke = data["joke"]
        elif data["type"] == "twopart":
            joke = f"{data['setup']} ... {data['delivery']}"
        else:
            joke = "Sorry, I couldn't find a joke right now."
        print(joke)
        speak(joke)
    except Exception as e:
        print("Error fetching joke:", e)
        speak("Sorry, I couldn't get a joke right now.")

def set_alarm():
    speak("Please tell me the time for the alarm in HH:MM format.")
    alarm_time = takeCommand()
    match = re.match(r'(\d{1,2}):(\d{2})', alarm_time)
    if not match:
        speak("I didn't understand the time format. Please say it like 6:30 or 18:45.")
        return
    hour, minute = int(match.group(1)), int(match.group(2))
    now = datetime.datetime.now()
    alarm_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alarm_dt < now:
        alarm_dt += datetime.timedelta(days=1)
    speak(f"Alarm set for {alarm_dt.strftime('%I:%M %p')}.")
    print(f"Alarm set for: {alarm_dt}")
    while datetime.datetime.now() < alarm_dt:
        time.sleep(10)
    speak("It's time! Here's your alarm.")
    os.system("start ms-windows-store://pdp/?ProductId=9WZDNCRFJ3PT")

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
    speak("I am Friday. How may I help you?")

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
    server.login('youremail@gmail.com', 'your-app-password')
    server.sendmail('youremail@gmail.com', to, content)
    server.close()

if __name__ == "__main__":
    while True:
        if detect_hotword("jarvis"):
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
                        speak("Sorry, I couldn't fetch the temperature.")
                    break
                elif 'how much battery' in query or 'battery' in query:
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
                    getNewsNewsData()
                    break
                elif 'tell me a joke' in query or 'make me laugh' in query:
                    tell_joke()
                    break
                elif 'set alarm' in query:
                    set_alarm()
                    break
                elif 'play marathi news' in query:
                    webbrowser.open('https://www.youtube.com/live/QnQVOxOVCJg?si=s72-IHOwJM3b4Z2t')
                    break
                elif 'search on google' in query or 'google' in query:
                    speak("What should I search for?")
                    search_query = takeCommand()
                    google_search_and_speak(search_query)
                    break

                elif 'close' in query or 'stop' in query:
                    speak("Goodbye! Have a nice day.")
                    sys.exit()
