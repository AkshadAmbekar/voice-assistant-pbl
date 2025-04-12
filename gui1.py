import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import pyttsx3
import speech_recognition as sr
from jarvis_core import detect_hotword, takeCommand, process_query, speak, wishMe, set_callbacks, run_voice_assistant

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - Voice Assistant")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f0f0")

        # Create a frame for the header
        header_frame = tk.Frame(root, bg="#4a6fa5")
        header_frame.pack(fill=tk.X)

        # Title label
        title_label = tk.Label(header_frame, text="Jarvis Voice Assistant", 
                              font=("Arial", 16, "bold"), bg="#4a6fa5", fg="white")
        title_label.pack(pady=10)

        # Middle frame for status and listen button
        middle_frame = tk.Frame(root, bg="#f0f0f0")
        middle_frame.pack(fill=tk.X, pady=5)

        # Status display
        self.status_label = tk.Label(middle_frame, text="Initializing...", 
                                    font=("Arial", 12), bg="#f0f0f0", fg="#333333")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Listen button with visual indicator
        self.listen_button_frame = tk.Frame(middle_frame, bg="#f0f0f0")
        self.listen_button_frame.pack(side=tk.RIGHT, padx=10)
        
        self.listen_indicator = tk.Canvas(self.listen_button_frame, width=30, height=30, bg="#f0f0f0", highlightthickness=0)
        self.listen_indicator.pack(side=tk.RIGHT, padx=5)
        
        # Draw initial inactive indicator (gray circle)
        self.indicator_circle = self.listen_indicator.create_oval(5, 5, 25, 25, fill="#cccccc", outline="#999999")
        
        # Make the indicator clickable
        self.listen_indicator.bind("<Button-1>", self.toggle_listening)
        
        # Label for the indicator
        self.indicator_label = tk.Label(self.listen_button_frame, text="Click to activate", 
                                      font=("Arial", 10), bg="#f0f0f0", fg="#666666")
        self.indicator_label.pack(side=tk.RIGHT)

        # Output text area
        self.output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, 
                                                   font=("Consolas", 11), 
                                                   bg="#ffffff", fg="#333333")
        self.output_text.pack(expand=True, fill='both', padx=10, pady=10)

        # Button frame
        button_frame = tk.Frame(root, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=10)

        # Exit button
        self.exit_button = tk.Button(button_frame, text="Exit", command=self.stop, 
                                    font=("Arial", 12), bg="#e74c3c", fg="white")
        self.exit_button.pack(side=tk.RIGHT, padx=10)

        # Clear button
        self.clear_button = tk.Button(button_frame, text="Clear Log", command=self.clear_log, 
                                     font=("Arial", 12), bg="#3498db", fg="white")
        self.clear_button.pack(side=tk.RIGHT, padx=10)

        # Listening state variables
        self.running = True
        self.continuous_mode = False
        self.manual_activation = False
        self.processing_command = False
        
        # Set up callbacks to update GUI from jarvis_core
        set_callbacks(self.log_output, self.update_status)
        
        # Start the assistant thread
        self.thread = threading.Thread(target=self.assistant_loop)
        self.thread.daemon = True
        self.thread.start()
        
        # Start indicator update thread
        self.indicator_thread = threading.Thread(target=self.update_indicator_loop)
        self.indicator_thread.daemon = True
        self.indicator_thread.start()

    def update_status(self, text):
        """Update status display safely from any thread"""
        self.root.after(0, lambda: self.status_label.config(text=text))

    def log_output(self, text):
        """Log output to text area safely from any thread"""
        self.root.after(0, lambda: self._append_to_log(text))
    
    def _append_to_log(self, text):
        """Actually append text to log (called in main thread)"""
        self.output_text.insert(tk.END, f"{text}\n")
        self.output_text.see(tk.END)

    def clear_log(self):
        """Clear the output log"""
        self.output_text.delete(1.0, tk.END)
        self.log_output("Log cleared")
    
    def update_indicator_loop(self):
        """Update visual indicator based on current state"""
        last_state = None
        
        while self.running:
            current_state = None
            
            if self.continuous_mode:
                if self.processing_command:
                    # Processing - yellow
                    current_state = "#f39c12"  # Orange/yellow
                else:
                    # Active listening - green
                    current_state = "#2ecc71"  # Green
            else:
                # Hotword detection - gray
                current_state = "#cccccc"  # Light gray
            
            # Only update UI if state changed
            if current_state != last_state:
                self.root.after(0, lambda color=current_state: self.update_indicator_color(color))
                last_state = current_state
            
            time.sleep(0.1)
    
    def update_indicator_color(self, color):
        """Update the indicator color (runs on main thread)"""
        self.listen_indicator.itemconfig(self.indicator_circle, fill=color)
        
        # Also update the label
        if color == "#2ecc71":  # Green
            self.indicator_label.config(text="Listening...")
        elif color == "#f39c12":  # Orange
            self.indicator_label.config(text="Processing...")
        else:  # Gray
            self.indicator_label.config(text="Click to activate")

    def toggle_listening(self, event=None):
        """Manually toggle the listening state when indicator is clicked"""
        if not self.continuous_mode and not self.manual_activation:
            # Activate assistant manually
            self.manual_activation = True
            self.log_output("Assistant manually activated")
        elif self.continuous_mode:
            # Return to hotword detection mode
            self.continuous_mode = False
            self.log_output("Returning to hotword detection mode")
            speak("Going back to hotword detection mode")

    def assistant_loop(self):
        """Main assistant loop that runs in background thread"""
        self.update_status("Starting up...")
        self.log_output("Voice Assistant initialized")
        wishMe()
        
        while self.running:
            # Check if manually activated through button
            if self.manual_activation:
                self.manual_activation = False
                self.continuous_mode = True
                speak("How can I help you?")
            
            # Hotword detection mode
            if not self.continuous_mode:
                self.update_status("Listening for hotword...")
                if detect_hotword():
                    self.log_output("Hotword detected!")
                    speak("How can I help you?")
                    self.continuous_mode = True
            
            # Continuous listening mode
            if self.continuous_mode and self.running:
                query = takeCommand()
                
                if query != "none":
                    self.update_status("Processing command...")
                    self.processing_command = True
                    
                    result = process_query(query)
                    
                    self.processing_command = False
                    
                    # Handle different return values from process_query
                    if result == "shutdown":
                        self.root.after(0, self.stop)
                        return
                    elif result is False:
                        # Exit continuous mode, go back to hotword detection
                        self.continuous_mode = False
                        self.update_status("Listening for hotword...")
                    else:
                        self.update_status("Ready for next command...")
            
            # Short sleep to prevent CPU hogging
            time.sleep(0.1)

    def stop(self):
        """Stop the assistant and close the application"""
        self.running = False
        self.root.after(1000, self.root.destroy)  # Give time for threads to clean up

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.stop)  # Handle window close button
    root.mainloop()