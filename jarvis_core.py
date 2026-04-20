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
import subprocess
import cv2
from dotenv import load_dotenv
import threading
from urllib.parse import quote_plus, urlparse
import uuid
import tempfile

try:
    import pywhatkit
    PYWHATKIT_IMPORT_ERROR = None
except Exception as e:
    pywhatkit = None
    PYWHATKIT_IMPORT_ERROR = str(e)

load_dotenv()

# api-keys
NEWSDATA_API_KEY = os.getenv('NEWSDATA_API_KEY')
API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

output_callback = None
status_callback = None

tts_lock = threading.Lock()

# initialize-spotify-client--deactivated
try:
    if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and SPOTIFY_REDIRECT_URI:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-playback-state,user-modify-playback-state"
        ))
    else:
        sp = None
except Exception as e:
    sp = None
    print(f"Spotify client initialization failed: {e}")

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

def initialize_tts():
    """Probe TTS availability once at startup for clear diagnostics."""
    try:
        probe_engine = pyttsx3.init()
        voices = probe_engine.getProperty('voices')
        if voices:
            probe_engine.setProperty('voice', voices[0].id)
        probe_engine.stop()
        log_output("TTS initialized with pyttsx3.")
    except Exception as e:
        log_output(f"pyttsx3 initialization failed: {e}. Using Windows speech fallback.")

def speak_with_pyttsx3(text):
    """Speak text with a fresh pyttsx3 engine per utterance for stability."""
    local_engine = pyttsx3.init()
    voices = local_engine.getProperty('voices')
    if voices:
        local_engine.setProperty('voice', voices[0].id)
    local_engine.say(text)
    local_engine.runAndWait()
    local_engine.stop()

def fallback_speak_windows(text):
    """Fallback to Windows speech API when pyttsx3 is unavailable."""
    try:
        escaped_text = text.replace("'", "''")
        ps_cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Speak('{escaped_text}')"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            check=False,
            capture_output=True,
            text=True
        )
    except Exception as e:
        log_output(f"Fallback speech failed: {e}")

def speak(audio):
    """Text to speech function"""
    log_output(f"Assistant: {audio}")
    text = str(audio)
    with tts_lock:
        try:
            speak_with_pyttsx3(text)
            return
        except Exception as e:
            log_output(f"pyttsx3 speak failed: {e}. Switching to fallback.")
        fallback_speak_windows(text)

initialize_tts()

def takeCommand():
    """Takes microphone input and returns string output"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        update_status("Listening...")
        log_output("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            log_output("Listening timed out. No speech detected.")
            return "none"
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
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            return False
    try:
        detected_text = recognizer.recognize_google(audio, language='en-in').lower()
        log_output(f"You said: {detected_text}")
        return hotword in detected_text
    except sr.UnknownValueError:
        return False
    except sr.RequestError as e:
        log_output(f"Hotword detection error: {e}")
        return False
    except Exception as e:
        log_output(f"Unexpected hotword error: {e}")
        return False

def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

def getNewsNewsData():
    try:
        if not NEWSDATA_API_KEY:
            speak("News API key is missing. Please configure it in your environment file.")
            return
        log_output("Fetching news...")
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&country=in&language=en"
        response = requests.get(url, timeout=10)
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
            url = None
            if isinstance(result, str):
                url = result
            elif hasattr(result, "url"):
                url = getattr(result, "url")
            elif isinstance(result, dict):
                url = result.get("url") or result.get("href") or result.get("link")

            if url:
                parsed = urlparse(url)
                if parsed.scheme in ("http", "https") and parsed.netloc:
                    webbrowser.open(url)
                    speak("Opening the result in your browser.")
                    return

        fallback_url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(fallback_url)
        speak("I couldn't find a direct result, so I opened Google search results in your browser.")
    except Exception as e:
        log_output(f"Search error: {e}")
        fallback_url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(fallback_url)
        speak("I couldn't use the search API right now, so I opened Google search in your browser.")

def parse_basic_number_words(text):
    """Convert simple number words to integers where possible."""
    units = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19
    }
    tens = {
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50
    }
    tokens = [t for t in re.split(r"[\s\-]+", text.strip().lower()) if t]
    if not tokens:
        return None

    if len(tokens) == 1:
        if tokens[0] in units:
            return units[tokens[0]]
        if tokens[0] in tens:
            return tens[tokens[0]]
        return None

    if len(tokens) == 2 and tokens[0] in tens and tokens[1] in units:
        return tens[tokens[0]] + units[tokens[1]]

    return None

def parse_alarm_datetime(alarm_input):
    """Parse alarm input from text into a datetime."""
    text = alarm_input.strip().lower()
    now = datetime.datetime.now()

    duration_match = re.search(
        r"(?:in\s+)?(\d+|[a-z\-\s]+?)\s*(minutes?|mins?|hours?|hrs?)\s*(?:from now)?$",
        text
    )
    if duration_match:
        qty_raw = duration_match.group(1).strip()
        unit = duration_match.group(2)
        qty = int(qty_raw) if qty_raw.isdigit() else parse_basic_number_words(qty_raw)
        if qty is None or qty <= 0:
            return None
        if unit.startswith("hour") or unit.startswith("hr"):
            return now + datetime.timedelta(hours=qty)
        return now + datetime.timedelta(minutes=qty)

    # Handle direct 24-hour format HH:MM
    clock_match = re.search(r"\b(\d{1,2})[:.](\d{2})\b", text)
    if clock_match:
        hour, minute = int(clock_match.group(1)), int(clock_match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            return target
        return None

    # Handle spoken/recognized compact formats like "910" or "0910"
    digits = re.sub(r"\D", "", text)
    if len(digits) in (3, 4):
        if len(digits) == 3:
            hour = int(digits[0])
            minute = int(digits[1:])
        else:
            hour = int(digits[:2])
            minute = int(digits[2:])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            return target
        return None

    # Handle simple spoken pair like "nine ten"
    words = [w for w in re.split(r"[\s\-]+", text) if w]
    if len(words) == 2:
        hour = parse_basic_number_words(words[0])
        minute = parse_basic_number_words(words[1])
        if hour is not None and minute is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            return target

    return None

def create_windows_alarm_task(alarm_dt):
    """Create a one-time native Windows scheduled task for the alarm."""
    service_check = subprocess.run(
        ["sc", "query", "schedule"],
        capture_output=True,
        text=True
    )
    service_text = f"{service_check.stdout}\n{service_check.stderr}".upper()
    if "RUNNING" not in service_text:
        raise RuntimeError(
            "Windows Task Scheduler service is not running. "
            "Start service 'Schedule' and try again."
        )

    task_name = f"JarvisAlarm_{alarm_dt.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    spoken_time = alarm_dt.strftime("%I:%M %p").lstrip("0")
    escaped_spoken_time = spoken_time.replace("'", "''")
    script_path = os.path.join(tempfile.gettempdir(), f"{task_name}.ps1")
    script_content = (
        "Add-Type -AssemblyName System.Speech\n"
        "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "$synth.Volume = 100\n"
        "$synth.Rate = 0\n"
        f"$synth.Speak('Jarvis alarm for {escaped_spoken_time}.')\n"
        "[console]::Beep(1000,500)\n"
        "Start-Sleep -Milliseconds 250\n"
        "[console]::Beep(1200,500)\n"
        "Start-Sleep -Milliseconds 250\n"
        "[console]::Beep(1000,500)\n"
        f"schtasks /Delete /TN \"{task_name}\" /F | Out-Null\n"
        "Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue\n"
    )
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    task_action = (
        f'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden '
        f'-File "{script_path}"'
    )

    date_candidates = [
        alarm_dt.strftime("%d/%m/%Y"),  # common in India
        alarm_dt.strftime("%m/%d/%Y"),  # US format
        alarm_dt.strftime("%Y/%m/%d"),  # accepted in some environments
    ]
    time_candidates = [
        alarm_dt.strftime("%H:%M"),
        alarm_dt.strftime("%I:%M %p"),
    ]

    errors = []
    current_user = os.getenv("USERNAME", "")
    ru_candidates = [None]
    if current_user:
        ru_candidates.append(current_user)
    for date_text in date_candidates:
        for time_text in time_candidates:
            for ru_value in ru_candidates:
                args = [
                    "schtasks",
                    "/Create",
                    "/SC", "ONCE",
                    "/TN", task_name,
                    "/TR", task_action,
                    "/ST", time_text,
                    "/SD", date_text,
                    "/RL", "LIMITED",
                    "/F",
                ]
                if ru_value:
                    args.extend(["/RU", ru_value])
                result = subprocess.run(args, capture_output=True, text=True)
                if result.returncode == 0:
                    return task_name
                err = (result.stderr or result.stdout or "Unknown Task Scheduler error").strip()
                user_suffix = f" /RU {ru_value}" if ru_value else ""
                errors.append(f"/SD {date_text} /ST {time_text}{user_suffix} -> {err}")

    # Last fallback: omit /SD for same-day schedules in some locales.
    if alarm_dt.date() == datetime.datetime.now().date():
        for time_text in time_candidates:
            for ru_value in ru_candidates:
                args = [
                    "schtasks",
                    "/Create",
                    "/SC", "ONCE",
                    "/TN", task_name,
                    "/TR", task_action,
                    "/ST", time_text,
                    "/RL", "LIMITED",
                    "/F",
                ]
                if ru_value:
                    args.extend(["/RU", ru_value])
                result = subprocess.run(args, capture_output=True, text=True)
                if result.returncode == 0:
                    return task_name
                err = (result.stderr or result.stdout or "Unknown Task Scheduler error").strip()
                user_suffix = f" /RU {ru_value}" if ru_value else ""
                errors.append(f"/ST {time_text} (no /SD){user_suffix} -> {err}")

    try:
        os.remove(script_path)
    except OSError:
        pass
    raise RuntimeError(" ; ".join(errors))

def set_alarm(alarm_input=None):
    if not alarm_input:
        speak("Tell me the alarm time. You can say 24-hour time like 09:10 or duration like 30 minutes from now.")
        alarm_input = takeCommand()
    if not alarm_input or alarm_input == "none":
        speak("I couldn't hear the alarm time.")
        return

    alarm_dt = parse_alarm_datetime(alarm_input)
    if not alarm_dt:
        speak("I couldn't parse the alarm time. Please say HH:MM in 24-hour format or for example 30 minutes from now.")
        return

    try:
        task_name = create_windows_alarm_task(alarm_dt)
        speak(f"Alarm set for {alarm_dt.strftime('%I:%M %p')}. I'll keep listening for your next command.")
        log_output(
            f"Alarm scheduled natively in Windows Task Scheduler for "
            f"{alarm_dt.strftime('%Y-%m-%d %H:%M:%S')} as task '{task_name}'."
        )
    except Exception as e:
        log_output(f"Alarm scheduling error: {e}")
        speak("I couldn't set the alarm in Windows Task Scheduler. Please check the log for the exact error and run Jarvis as administrator once.")

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
        response = requests.get(url, timeout=10)
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
        if not expression or expression == "none":
            speak("I didn't catch the expression.")
            return
        expression = expression.replace('plus', '+')\
                               .replace('minus', '-')\
                               .replace('times', '*')\
                               .replace('x', '*')\
                               .replace('divided by', '/')\
                               .replace('into', '*')\
                               .replace('by', '/')
        expression = expression.strip()
        if not re.fullmatch(r"[0-9+\-*/().\s]+", expression):
            speak("I can only calculate basic arithmetic expressions.")
            return
        log_output(f"Calculating: {expression}")
        result = eval(expression, {"__builtins__": None}, {})
        speak(f"The result is {result}")
    except Exception as e:
        log_output(f"Calculation error: {e}")
        speak("Sorry, I couldn't calculate that.")

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
    if not query or query == "none":
        return True

    if 'wikipedia' in query or 'search on wikipedia' in query:
        topic = query.replace("search on wikipedia", "").replace("wikipedia", "").strip()
        if not topic:
            speak("Please tell me what topic you want to search on Wikipedia.")
            return True
        try:
            speak('Searching Wikipedia...')
            results = wikipedia.summary(topic, sentences=2)
            speak("According to Wikipedia")
            speak(results)
        except Exception as e:
            log_output(f"Wikipedia error: {e}")
            speak("Sorry, I couldn't fetch that Wikipedia summary.")

    elif 'play on youtube' in query:
        song = query.replace("play on youtube", "").strip()
        if song:
            if pywhatkit is not None:
                try:
                    pywhatkit.playonyt(song)
                    speak(f"Playing {song} on YouTube.")
                except Exception as e:
                    log_output(f"YouTube play error: {e}")
                    webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")
                    speak("I couldn't auto-play, so I opened YouTube search.")
            else:
                webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")
                speak("pywhatkit is unavailable right now, so I opened YouTube search in your browser.")
                if PYWHATKIT_IMPORT_ERROR:
                    log_output(f"pywhatkit import error: {PYWHATKIT_IMPORT_ERROR}")
        else:
            speak("I didn't catch the song name.")

    elif 'open youtube' in query or 'go to youtube' in query or query.strip() == "youtube":
        webbrowser.open("https://www.youtube.com")

    elif 'play music' in query or 'play song' in query or 'music' in query:
        music_dir = r"C:\Sarang\Media\Audios"
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
        if not city or city == "none":
            speak("I couldn't hear the city name.")
            return True
        if not API_KEY or not BASE_URL:
            speak("Weather service is not configured. Please add API key and base URL in your environment file.")
            return True
        params = {"access_key": API_KEY, "query": city}
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            weather_data = response.json()
            if "current" in weather_data:
                temp = weather_data["current"]["temperature"]
                speak(f"The current temperature in {city} is {temp} degrees Celsius.")
            else:
                speak("Sorry, I couldn't fetch the temperature.")
        except Exception as e:
            log_output(f"Weather error: {e}")
            speak("Sorry, I couldn't fetch the weather right now.")

    elif 'battery' in query or 'battery status' in query:
        battery = psutil.sensors_battery()
        if battery is None:
            speak("Sorry, I couldn't read battery information on this system.")
        else:
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
        alarm_text = query
        alarm_text = re.sub(r"\bset alarm\b", " ", alarm_text)
        alarm_text = re.sub(r"\balarm\b", " ", alarm_text)
        alarm_text = re.sub(r"\bfor\b", " ", alarm_text)
        alarm_text = re.sub(r"\bat\b", " ", alarm_text)
        alarm_text = re.sub(r"\s+", " ", alarm_text).strip()
        if alarm_text:
            set_alarm(alarm_text)
        else:
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

    elif 'exit' in query or 'stop listening' in query:
        speak("Going back to hotword detection mode. Say Jarvis to activate me again.")
        return False
    
    elif 'close' in query or 'shutdown' in query or 'goodbye' in query:
        speak("Goodbye! Have a nice day.")
        return "shutdown"
    
    return True

def run_voice_assistant():
    """Main function to run the voice assistant - for standalone usage"""
    wishMe()
    
    while True:
        continuous_mode = True
        
        while continuous_mode:
            query = takeCommand()
            if query != "none":
                result = process_query(query)
                if result == "shutdown":
                    return  
                elif result is False:
                    continuous_mode = False
                    break
        
        while not continuous_mode:
            if detect_hotword():
                speak("I'm back. How can I help you?")
                continuous_mode = True 
                break
