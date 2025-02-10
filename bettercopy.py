import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pyautogui
import pyperclip
import time
import keyboard
import os
import sys
import logging


special_characters = {
    '!': ('shift', '1'),
    '@': ('shift', '2'),
    '#': ('shift', '3'),
    '$': ('shift', '4'),
    '%': ('shift', '5'),
    '^': ('shift', '6'),
    '&': ('shift', '7'),
    '*': ('shift', '8'),
    '(': ('shift', '9'),
    ')': ('shift', '0'),
    '_': ('shift', '-'),
    '+': ('shift', '='),
    '{': ('shift', '['),
    '}': ('shift', ']'),
    '|': ('shift', '\\'),
    ':': ('shift', ';'),
    '"': ('shift', "'"),
    '<': ('shift', ','),
    '>': ('shift', '.'),
    '?': ('shift', '/'),
}

# Constants
DEFAULT_SLEEP_TIME = "3"
TYPING_DELAY = 0.1
TEXT_WIDTH = 40
TEXT_HEIGHT = 5
STOP_KEY = "Shift + F10"
START_KEY = "Shift + F9"

class ClipboardTyper:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Typing Simulator")
        
        #Check if running as root
        if not self.is_running_as_root():
            messagebox.showerror("Error", "This program must be run as root!")
            sys.exit(1)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input field
        ttk.Label(main_frame, text="Text to type:").grid(row=0, column=0, sticky=tk.W)
        self.input_text = tk.Text(main_frame, width=TEXT_WIDTH, height=TEXT_HEIGHT)
        self.input_text.grid(row=1, column=0, columnspan=4, pady=5)
        self.input_text.bind('<Return>', self.simulate_typing)
        
        # Button to paste from clipboard
        self.clipboard_button = ttk.Button(main_frame, text="Paste from Clipboard", command=self.paste_from_cliboard)
        self.clipboard_button.grid(row=2, column=0, pady=5)
        
        # Clear button
        self.clear_button = ttk.Button(main_frame, text="Clear", command=lambda: self.input_text.delete("1.0", tk.END))
        self.clear_button.grid(row=2, column=1, padx=5)
        
        # Sleep time
        ttk.Label(main_frame, text="Sleep time (seconds):").grid(row=3, column=0, sticky=tk.W)
        self.sleep_time = ttk.Entry(main_frame, width=10)
        self.sleep_time.insert(0, DEFAULT_SLEEP_TIME)
        self.sleep_time.grid(row=3, column=1, sticky=tk.W, pady=5)
        self.sleep_time.bind('<Return>', self.simulate_typing)
        
        # Always on top checkbox
        self.always_on_top = tk.BooleanVar()
        self.always_on_top_cb = ttk.Checkbutton(main_frame, text="Always on top", variable=self.always_on_top, command=self.toggle_always_on_top)
        self.always_on_top_cb.grid(row=3, column=3, columnspan=2, pady=5)
        
        # Start button
        stop_key = "<Shift + F10>"
        pyautogui.FAILSAFE = True

        self.start_button = ttk.Button(main_frame, text=f"Start (Shift + F9)", command=self.simulate_typing)
        self.start_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=5, column=0, columnspan=4)
        
        # Stop button
        self.stop_button = ttk.Button(main_frame, text="Stop (Shift + F10)", command=self.stop_typing)
        self.stop_button.grid(row=4, column=2, columnspan=2, pady=5)
        
        # Bind hotkeys
        keyboard.add_hotkey("Shift + F9", self.simulate_typing)
        keyboard.add_hotkey("Shift + F10", self.stop_typing)
        self.root.bind('<Control-g>', self.simulate_typing)
        self.running = False
        
    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.always_on_top.get())
        
    def is_running_as_root(self):
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    
    def paste_from_cliboard(self):
        try:
            clipboard_content = pyperclip.paste()
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert(tk.END, clipboard_content)
        except Exception as e:
            self.status_label.config(text=f"Error pasting from clipboard: {e}")

    def simulate_typing(self, event=None):
        if self.running:
            return
            
        text_to_type = self.input_text.get("1.0", tk.END).strip()
        if not text_to_type:
            self.paste_from_cliboard()
            return
            
        sleep_seconds = self.validate_sleep_time()
        self.status_label.config(text=f"Starting in {sleep_seconds} seconds...")
        self.running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
    
        time.sleep(sleep_seconds)
    
        for char in text_to_type:
            if not self.running:
                break
            self.status_label.config(text="Typing...")
        
            # Enhanced typing logic for special characters
            if char.isupper():
                pyautogui.keyDown('shift')
                pyautogui.press(char.lower())
                pyautogui.keyUp('shift')
            elif char in special_characters:
                modifier, key = special_characters[char]
                pyautogui.keyDown(modifier)
                pyautogui.press(key)
                pyautogui.keyUp(modifier)
            else:
                pyautogui.write(char)
            
            time.sleep(0.1)
            self.root.update()
        
        self.reset_state()
        self.status_label.config(text="Typing complete" if self.running else "Typing stopped")

    def stop_typing(self, event=None):
        if self.running:
            self.running = False
            self.status_label.config(text="Typing stopped")
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')

    def reset_state(self):
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def validate_sleep_time(self):
        try:
            sleep_time = float(self.sleep_time.get())
            if sleep_time < 0 or sleep_time > 60:
                raise ValueError("Sleep time must be between 0 and 60 seconds")
            return sleep_time
        except ValueError:
            raise ValueError("Invalid sleep time format")


if __name__ == "__main__":
    root = tk.Tk()
    app = ClipboardTyper(root)
    root.mainloop()