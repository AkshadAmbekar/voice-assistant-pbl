import tkinter as tk
from tkinter import messagebox
import threading
import jarvis_core

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - Voice Assistant")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        self.create_widgets()
        self.listening = False

    def create_widgets(self):
        self.label_title = tk.Label(self.root, text="Jarvis", font=("Helvetica", 32, "bold"), fg="#1E90FF")
        self.label_title.pack(pady=20)

        self.text_display = tk.Text(self.root, wrap=tk.WORD, font=("Helvetica", 12), height=18, width=58)
        self.text_display.pack(pady=10)
        self.text_display.insert(tk.END, "Welcome! Click 'Start Listening' to begin.\n")
        self.text_display.configure(state='disabled')

        self.listen_button = tk.Button(self.root, text="Start Listening", font=("Helvetica", 14), command=self.toggle_listen, bg="#1E90FF", fg="white", width=20)
        self.listen_button.pack(pady=20)

    def toggle_listen(self):
        if not self.listening:
            self.listening = True
            self.listen_button.configure(text="Stop Listening")
            threading.Thread(target=self.run_jarvis_loop).start()
        else:
            self.listening = False
            self.listen_button.configure(text="Start Listening")

    def display_text(self, text):
        self.text_display.configure(state='normal')
        self.text_display.insert(tk.END, text + "\n")
        self.text_display.see(tk.END)
        self.text_display.configure(state='disabled')

    def run_jarvis_loop(self):
        self.display_text("Hotword detection started. Say 'Jarvis'...")
        while self.listening:
            try:
                if jarvis_core.detect_hotword("jarvis"):
                    self.display_text("Hotword detected. Listening for command...")
                    jarvis_core.wishMe()
                    while self.listening:
                        query = jarvis_core.takeCommand()
                        if query and query != "none":
                            self.display_text(f"You said: {query}")
                            response = self.process_query(query)
                            if response == "exit":
                                self.display_text("Goodbye! Exiting.")
                                self.root.quit()
                                return
                            break
            except Exception as e:
                self.display_text(f"Error: {e}")

    def process_query(self, query):
        query = query.lower()
        if 'wikipedia' in query:
            jarvis_core.speak('Searching Wikipedia...')
            query = query.replace("wikipedia", "")
            result = jarvis_core.wikipedia.summary(query, sentences=2)
            self.display_text(result)
            jarvis_core.speak(result)

        elif 'open youtube' in query:
            jarvis_core.webbrowser.open("https://youtube.com")

        elif 'play music' in query:
            music_dir = r"C:\\Users\\uday dherange\\Downloads"
            songs = [song for song in jarvis_core.os.listdir(music_dir) if song.endswith(".mp3")]
            if songs:
                jarvis_core.os.startfile(jarvis_core.os.path.join(music_dir, songs[0]))
            else:
                jarvis_core.speak("No music files found.")

        elif 'current time' in query:
            now = jarvis_core.datetime.datetime.now().strftime("%H:%M:%S")
            jarvis_core.speak(f"The time is {now}")
            self.display_text(f"The time is {now}")

        elif 'open chatbot' in query:
            jarvis_core.webbrowser.open("https://chat.openai.com/")

        elif 'temperature' in query:
            jarvis_core.speak("Which city?")
            city = jarvis_core.takeCommand()
            params = {"access_key": jarvis_core.API_KEY, "query": city}
            res = jarvis_core.requests.get(jarvis_core.BASE_URL, params=params)
            weather_data = res.json()
            if "current" in weather_data:
                temp = weather_data["current"]["temperature"]
                result = f"The temperature in {city} is {temp}°C."
                jarvis_core.speak(result)
                self.display_text(result)
            else:
                jarvis_core.speak("Sorry, couldn't fetch temperature.")

        elif 'battery' in query:
            battery = jarvis_core.psutil.sensors_battery()
            percent = battery.percent
            jarvis_core.speak(f"We have {percent}% battery.")
            self.display_text(f"Battery: {percent}%")

        elif 'spotify' in query:
            jarvis_core.speak("Which song?")
            song = jarvis_core.takeCommand()
            jarvis_core.play_on_spotify(song)

        elif 'news' in query or 'headlines' in query:
            headlines = jarvis_core.getNewsNewsData()
            for headline in headlines:
                self.display_text(headline)
                
        

        elif 'joke' in query or 'laugh' in query:
            jarvis_core.tell_joke()

        elif 'alarm' in query:
            jarvis_core.set_alarm()

        elif 'search' in query or 'google' in query:
            jarvis_core.speak("What should I search for?")
            search_query = jarvis_core.takeCommand()
            result = jarvis_core.google_search_and_speak(search_query)
            self.display_text(f"Search result: {result}")

        elif 'close' in query or 'stop' in query:
            jarvis_core.speak("Goodbye!")
            return "exit"

        return "ok"

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
