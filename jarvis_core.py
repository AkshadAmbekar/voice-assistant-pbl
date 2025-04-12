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
import pywhatkit
from googlesearch import search
import subprocess
import cv2


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
    try:
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&country=in&language=en"
        response = requests.get(url)
        data = response.json()
        articles = data.get("results", [])[:5]

        if not articles:
            speak("Sorry, I couldn't find any news right now.")
            return

        for article in articles:
            title = article.get("title", "")
            if title:
                print(title)
                speak(title)

    except Exception as e:
        print("News error:", e)
        speak("Sorry, I couldn't fetch the news.")

def open_webcam():
    speak("Opening webcam.")
    cap = cv2.VideoCapture(0)  # 0 is the default camera

    if not cap.isOpened():
        speak("Sorry, I couldn't access the webcam.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            speak("Failed to grab frame.")
            break
        cv2.imshow('Webcam - Press Q to exit', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

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
        return hotword in detected_text
    except sr.UnknownValueError:
        return False
    except sr.RequestError as e:
        print(f"Hotword detection error: {e}")
        return False

def google_search_and_speak(query):
    speak(f"Searching Google for {query}")
    try:
        results = list(search(query, num_results=5))
        print(f"Google search result: {results}")

        for result in results:
            if result.startswith("http"):
                print(f"Opening: {result}")
                speak("Opening the result in your browser.")
                webbrowser.open(result)
                return result

        speak("Sorry, I didn't find a valid URL.")
    except Exception as e:
        print("Search error:", e)
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
        search_url = f"spotify:search:{song_name.replace(' ', '%20')}"
        result = os.system(f"start {search_url}")
        if result != 0:
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

def evaluate_expression(expression):
    try:
        expression = expression.replace('plus', '+') \
                               .replace('minus', '-') \
                               .replace('times', '*') \
                               .replace('x', '*') \
                               .replace('divided by', '/') \
                               .replace('into', '*') \
                               .replace('by', '/')  # for "8 by 2"

        result = eval(expression)
        speak(f"The result is {result}")
        print(f"Result: {result}")
    except Exception as e:
        print("Calculation error:", e)
        speak("Sorry, I couldn't calculate that.")

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
    speak("I am Kirmaadaaa. How may I help you?")

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
    wishMe()
    while True:
        query = takeCommand()
        if query == "none":
            continue

        if 'wikipedia' in query:
            speak('Searching Wikipedia...')
            query = query.replace("wikipedia", "")
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia")
            print(results)
            speak(results)

        elif 'open youtube' in query:
            webbrowser.open("https://www.youtube.com")

        

        elif 'play music' in query:
            music_dir = r"C:\Users\ambek\OneDrive\Desktop\offlinesongs"
            try:
                songs = [song for song in os.listdir(music_dir) if song.endswith(".mp3")]

                if songs:
                    speak("Here are the available songs.")
                    for i, song in enumerate(songs[:5], 1):  # Limit to 5 options for simplicity
                        print(f"{i}. {song}")
                        speak(f"Option {i}: {song.replace('.mp3', '')}")

                    speak("Please say the number of the song you want to play.")
                    choice = takeCommand()

            # Try to extract number from user's speech
                    number_match = re.search(r'\d+', choice)
                    if number_match:
                        song_index = int(number_match.group()) - 1
                        if 0 <= song_index < len(songs[:5]):
                            song_path = os.path.join(music_dir, songs[song_index])
                            os.startfile(song_path)
                            speak(f"Playing {songs[song_index].replace('.mp3', '')}")
                        else:
                            speak("Invalid choice number.")
                    else:
                        speak("I didn't catch a valid number.")

                else:
                    speak("No music files found!")
            except Exception as e:
                print("Music error:", e)
                speak("Something went wrong while trying to play music.")

        elif 'open webcam' in query or 'camera' in query:
            open_webcam()


        elif 'current time' in query:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            speak(f"Sir, the time is {strTime}")
            
        elif 'open notepad' in query:
            speak("Opening Notepad.")
            os.system("notepad.exe")
            
        elif 'open calculator' in query or 'calculator' in query:
            speak("Opening Calculator.")
            os.system("calc")


        elif 'open paint' in query:
            speak("Opening Paint.")
            subprocess.Popen(['mspaint.exe'])

        elif 'calculate' in query:
            speak("What would you like to calculate?")
            expression = takeCommand()
            evaluate_expression(expression)
            
        elif 'open explorer' in query or 'file explorer' in query:
            speak("Opening File Explorer.")
            os.system("explorer")

        elif 'open folder' in query:
            speak("Which folder would you like to open?")
            folder = takeCommand()
            path = f"C:\\Users\\Akshad\\{folder}"
            if os.path.exists(path):
                os.system(f'explorer "{path}"')
                speak(f"Opening {folder}")
            else:
                speak("Sorry, I couldn't find that folder.")


        elif 'open chatbot' in query:
            webbrowser.open('https://chat.openai.com/')

        elif 'open mail' in query:
            webbrowser.open('https://mail.google.com/mail/u/0/#inbox')

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

        elif 'how much battery' in query or 'battery' in query:
            battery = psutil.sensors_battery()
            percentage = battery.percent
            speak(f"Sir, we have {percentage} percent battery left.")

        elif 'play on spotify' in query:
            speak("Which song would you like to play?")
            song = takeCommand()
            play_on_spotify(song)

        elif 'news' in query or 'headlines' in query:
            getNewsNewsData()

        elif 'tell me a joke' in query or 'make me laugh' in query:
            tell_joke()

        elif 'set alarm' in query:
            set_alarm()

        elif 'play marathi news' in query:
            webbrowser.open('https://www.youtube.com/live/QnQVOxOVCJg?si=s72-IHOwJM3b4Z2t')

        elif 'search google for' in query:
            search_query = query.replace("search google for", "").strip()
            if search_query:
                google_search_and_speak(search_query)
            else:
                speak("What would you like me to search for?")
                search_query = takeCommand()
                
                if search_query and search_query != "none":
                    google_search_and_speak(search_query)


        elif 'play on youtube' in query or 'youtube' in query:
            song = query.replace("play on youtube", "").replace("youtube", "").strip()
            if song:
                speak(f"Playing {song} on YouTube.")
                pywhatkit.playonyt(song)
            else:
                speak("I didn't catch the song name.")

        elif 'close' in query or 'stop' in query:
            speak("Goodbye! Have a nice day.")
            break
