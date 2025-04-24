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

# api-keys
NEWSDATA_API_KEY = "pub_78348fa8cf5f3cb028a545aa4643b5e4fc3a8"
API_KEY = "fe057c28ff3077ebb41755e4bce2f959"
BASE_URL = "http://api.weatherstack.com/current"
SPOTIFY_CLIENT_ID = "93eca05e29d843f38e73382887dbe1c4"
SPOTIFY_CLIENT_SECRET = "0fed1d9137ac4c7fb24843e79bc65032"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080/callback/"

output_callback = None
status_callback = None

# initialize-TTS-engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# initialize-spotify-client--deactivated
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state"
))

def set_callbacks(output_cb, status_cb):
    """Set callback functions for GUI updates"""
    global output_callback, status_callback
    output_callback = output_cb
    status_callback = status_cb

def log_output(text):
    """Send output to GUI if callback is set"""
    print(text)
    if output_callback:
        output_callback(text)

def update_status(text):
    """Update status on GUI if callback is set"""
    print(f"Status: {text}")
    if status_callback:
        status_callback(text)

def speak(audio):
    """Text to speech function"""
    log_output(f"Assistant: {audio}")
    engine.say(audio)
    engine.runAndWait()

def takeCommand():
    """Takes microphone input and returns string output"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        update_status("Listening...")
        log_output("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
    try:
        update_status("Recognizing...")
        log_output("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        log_output(f"User said: {query}")
        return query.lower()
    except Exception as e:
        log_output(f"Recognition error: {str(e)}")
        log_output("Say that again please...")
        return "none"

def detect_hotword(hotword="jarvis"):
    """Detect the hotword to activate the assistant"""
    update_status("Listening for hotword...")
    log_output("Listening for hotword...")
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        detected_text = recognizer.recognize_google(audio, language='en-in').lower()
        log_output(f"You said: {detected_text}")
        return hotword in detected_text
    except sr.UnknownValueError:
        return False
    except sr.RequestError as e:
        log_output(f"Hotword detection error: {e}")
        return False

def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

def getNewsNewsData():
    try:
        log_output("Fetching news...")
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
                log_output(title)
                speak(title)
    except Exception as e:
        log_output(f"News error: {e}")
        speak("Sorry, I couldn't fetch the news.")

def open_webcam():
    speak("Opening webcam.")
    log_output("Opening webcam. Press Q to exit.")
    cap = cv2.VideoCapture(0)
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

def google_search_and_speak(query):
    speak(f"Searching Google for {query}")
    log_output(f"Searching Google for: {query}")
    try:
        results = list(search(query, num_results=5))
        for result in results:
            if result.startswith("http"):
                webbrowser.open(result)
                speak("Opening the result in your browser.")
                return
        speak("Sorry, I didn't find a valid URL.")
    except Exception as e:
        log_output(f"Search error: {e}")
        speak("Sorry, I couldn't perform the search.")

def play_spotify_playlist():
    playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    webbrowser.open(playlist_url)
    speak("Playing Spotify playlist.")

def play_on_spotify(song_name):
    try:
        if not song_name:
            speak("You didn't specify a song.")
            return
        web_url = f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}"
        webbrowser.open(web_url)
        speak(f"Opening {song_name} on Spotify Web.")
    except Exception as e:
        log_output(f"Error playing on Spotify: {e}")
        speak("Sorry, I couldn't play that on Spotify.")

def tell_joke():
    url = "https://v2.jokeapi.dev/joke/Any?format=json"
    try:
        log_output("Fetching a joke...")
        response = requests.get(url)
        data = response.json()
        if data["type"] == "single":
            joke = data["joke"]
        elif data["type"] == "twopart":
            joke = f"{data['setup']} ... {data['delivery']}"
        else:
            joke = "Sorry, I couldn't find a joke right now."
        log_output(joke)
        speak(joke)
    except Exception as e:
        log_output(f"Error fetching joke: {e}")
        speak("Sorry, I couldn't get a joke right now.")

def evaluate_expression(expression):
    try:
        expression = expression.replace('plus', '+')\
                               .replace('minus', '-')\
                               .replace('times', '*')\
                               .replace('x', '*')\
                               .replace('divided by', '/')\
                               .replace('into', '*')\
                               .replace('by', '/')
        log_output(f"Calculating: {expression}")
        result = eval(expression)
        speak(f"The result is {result}")
    except Exception as e:
        log_output(f"Calculation error: {e}")
        speak("Sorry, I couldn't calculate that.")

def set_alarm():
    speak("Please tell me the time for the alarm in HH:MM format.")
    alarm_time = takeCommand()
    match = re.match(r'(\d{1,2}):(\d{2})', alarm_time)
    if not match:
        speak("I didn't understand the time format.")
        return
    hour, minute = int(match.group(1)), int(match.group(2))
    now = datetime.datetime.now()
    alarm_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alarm_dt < now:
        alarm_dt += datetime.timedelta(days=1)
    speak(f"Alarm set for {alarm_dt.strftime('%I:%M %p')}")
    log_output(f"Alarm set for {alarm_dt.strftime('%I:%M %p')}")
    while datetime.datetime.now() < alarm_dt:
        time.sleep(10)
    speak("It's time! Here's your alarm.")
    os.system("start ms-windows-store://pdp/?ProductId=9WZDNCRFJ3PT")

def wishMe():
    hour = int(datetime.datetime.now().hour)
    if hour < 12:
        speak("Good Morning!")
    elif hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am Jarvis. How may I help you?")

def sendEmail(to, content):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login('youremail@gmail.com', 'your-app-password')
    server.sendmail('youremail@gmail.com', to, content)
    server.close()

def process_query(query):
    """Process user commands"""
    if 'wikipedia' in query or 'search on wikipedia' in query:
        speak('Searching Wikipedia...')
        query = query.replace("wikipedia", "").replace("search on wikipedia", "")
        results = wikipedia.summary(query, sentences=2)
        speak("According to Wikipedia")
        speak(results)

    elif 'youtube' in query or 'open youtube' in query or 'go to youtube' in query:
        webbrowser.open("https://www.youtube.com")

    elif 'play music' in query or 'play song' in query or 'music' in query:
        music_dir = r"C:\Sarang\Media\Songs"
        try:
            songs = [song for song in os.listdir(music_dir) if song.endswith(".mp3")]
            if songs:
                speak("Here are the available songs.")
                for i, song in enumerate(songs[:5], 1):
                    speak(f"Option {i}: {song.replace('.mp3', '')}")
                speak("Please say the number of the song you want to play.")
                choice = takeCommand()
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
            log_output(f"Music error: {e}")
            speak("Something went wrong while trying to play music.")

    elif 'open webcam' in query or 'open camera' in query or 'turn on webcam' in query:
        open_webcam()

    elif 'time' in query or 'current time' in query or 'what time is it' in query:
        strTime = datetime.datetime.now().strftime("%H:%M:%S")
        speak(f"Sir, the time is {strTime}")

    elif 'notepad' in query or 'open notepad' in query:
        os.system("notepad.exe")

    elif 'calculator' in query or 'open calculator' in query:
        os.system("calc")

    elif 'paint' in query or 'open paint' in query:
        subprocess.Popen(['mspaint.exe'])

    elif 'calculate' in query or 'do the math' in query:
        speak("What would you like to calculate?")
        expression = takeCommand()
        evaluate_expression(expression)

    elif 'explorer' in query or 'file explorer' in query:
        os.system("explorer")

    elif 'chatbot' in query or 'open chatbot' in query:
        webbrowser.open('https://chat.openai.com/')

    elif 'email' in query or 'open mail' in query:
        webbrowser.open('https://mail.google.com/mail/u/0/#inbox')

    elif 'weather' in query or 'temperature' in query:
        speak("Which city's weather would you like to know?")
        city = takeCommand()
        params = {"access_key": API_KEY, "query": city}
        response = requests.get(BASE_URL, params=params)
        weather_data = response.json()
        if "current" in weather_data:
            temp = weather_data["current"]["temperature"]
            speak(f"The current temperature in {city} is {temp} degrees Celsius.")
        else:
            speak("Sorry, I couldn't fetch the temperature.")

    elif 'battery' in query or 'battery status' in query:
        battery = psutil.sensors_battery()
        percentage = battery.percent
        speak(f"Sir, we have {percentage} percent battery left.")

    elif 'play on spotify' in query or 'spotify' in query:
        speak("Which song would you like to play?")
        song = takeCommand()
        play_on_spotify(song)

    elif 'news' in query or 'headlines' in query or 'latest news' in query:
        getNewsNewsData()

    elif 'joke' in query or 'tell me a joke' in query or 'make me laugh' in query:
        tell_joke()

    elif 'set alarm' in query or 'alarm' in query:
        set_alarm()

    elif 'search google for' in query or 'google search' in query:
        search_query = query.replace("search google for", "").replace("google search", "").strip()
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
            pywhatkit.playonyt(song)
        else:
            speak("I didn't catch the song name.")

    elif 'exit' in query or 'stop listening' in query:
        speak("Going back to hotword detection mode. Say Jarvis to activate me again.")
        return False
    
    elif 'close' in query or 'shutdown' in query or 'goodbye' in query:
        speak("Goodbye! Have a nice day.")
        return "shutdown"
    
    return True

def run_voice_assistant():
    """Main function to run the voice assistant - for standalone usage"""
    # Start with greeting
    wishMe()
    
    # Start in continuous mode by default, no initial hotword detection
    while True:
        # Always start in continuous listening mode
        continuous_mode = True
        
        # While in continuous mode, keep taking commands
        while continuous_mode:
            query = takeCommand()
            if query != "none":
                result = process_query(query)
                if result == "shutdown":
                    return  # Exit the entire program
                elif result is False:
                    # User said "exit" - only now switch to hotword detection
                    continuous_mode = False
                    break
        
        # Only reached after user says "exit"
        # Now start hotword detection loop
        while not continuous_mode:
            if detect_hotword():
                speak("I'm back. How can I help you?")
                continuous_mode = True  # Return to continuous mode
                break