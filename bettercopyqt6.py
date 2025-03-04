from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                            QSpinBox, QCheckBox, QMessageBox, QListWidget, QSplitter, QFrame)
from PyQt6.QtCore import Qt, QTimer
import pyautogui
import keyboard
import time
import sys
import locale
import ctypes
import re

class ClipboardTyper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyboard Typing Simulator")
        self.running = False
        self.clipboard_history = []
        self.max_history_size = 10
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # layout = QVBoxLayout(central_widget)

        # Use a horizontal splitter for main layout
        main_layout = QHBoxLayout(central_widget)

        # Create left panel for the main functionality
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Create right panel for history
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMinimumWidth(200)
        
        # Create UI elements
        self.input_text = QTextEdit()
        self.sleep_time = QSpinBox()
        self.sleep_time.setRange(1, 10)
        self.sleep_time.setValue(3)
        
        self.start_button = QPushButton("Start Typing")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        
        self.Paste_from_clipboard_button = QPushButton("Paste from Clipboard")
        self.clear_button = QPushButton("Clear")
        
        self.status_label = QLabel("Ready")

        # Add Keyboard Layout indicator
        self.layout_label = QLabel("Current keyboard layout: Unknown")
        
        # ADd widgets to left layout
        left_layout.addWidget(QLabel("Text to type:"))
        left_layout.addWidget(self.input_text)

        button_layout1 = QHBoxLayout()
        button_layout1.addWidget(self.Paste_from_clipboard_button)
        button_layout1.addWidget(self.clear_button)
        left_layout.addLayout(button_layout1)
        left_layout.addWidget(QLabel("Delay before typing (seconds):"))
        left_layout.addWidget(self.sleep_time)
        
        button_layout2 = QHBoxLayout()
        button_layout2.addWidget(self.start_button)
        button_layout2.addWidget(self.stop_button)
        left_layout.addLayout(button_layout2)        
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.layout_label)

        # Create and add history list
        history_loabel = QLabel("History")
        history_loabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.history_item_clicked)

        right_layout.addWidget(history_loabel)
        right_layout.addWidget(self.history_list)

        # Add panels to main layout with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter)
        
        # Connect buttons
        self.start_button.clicked.connect(self.simulate_typing)
        self.stop_button.clicked.connect(self.stop_typing)
        self.Paste_from_clipboard_button.clicked.connect(self.paste_from_clipboard)
        self.clear_button.clicked.connect(self.clear_text)
        
        # Define special characters mapping with direct character input
        self.special_characters = {
            '!': ['shift', '1'],
            '@': ['shift', '2'],
            '#': ['shift', '3'],
            '$': ['shift', '4'],
            '%': ['shift', '5'],
            '^': ['shift', '6'],
            '&': ['shift', '7'],
            '*': ['shift', '8'],
            '(': ['shift', '9'],
            ')': ['shift', '0'],
            '_': ['shift', '-'],
            '+': ['shift', '='],
            '{': ['shift', '['],
            '}': ['shift', ']'],
            '|': ['shift', '\\'],
            ':': ['shift', ';'],
            '"': ['shift', "'"],
            '<': ['shift', ','],
            '>': ['shift', '.'],
            '?': ['shift', '/'],
            '~': ['shift', '`'],
            ' ': ['space']
        }
        
        # Update keyboard layout indicator
        self.update_keyboard_layout()
        
        # Set a timer to periodivally update the keyboard layout
        self.layout_timer = QTimer()
        self.layout_timer.timeout.connect(self.update_keyboard_layout)
        self.layout_timer.start(1000)  # Update every second

    def get_current_keyboard_layout(self):
        # Get the current keyboard layout
        try:
            if sys.platform == "win32":
                # Windows platform
                user32 = ctypes.WinDLL('user32', use_last_error=True)
                curr_windows = user32.GetForegroundWindow()
                thread_id = user32.GetWindowThreadProcessId(curr_windows, 0)
                
                # Get the active window title for context
                length = user32.GetWindowTextLengthW(curr_windows)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(curr_windows, buff, length + 1)
                window_title = buff.value
                
                # Get keyboard layout after getting window title to ensure it's for the current window
                klid = user32.GetKeyboardLayout(thread_id)

                # Convert to layout ID to a locale identifier
                lid = klid & 0xFFFF

                # Map common layout ID's to names
                layout_names = {
                    0x0409: "English (US)",
                    0x0809: "English (UK)",
                    0x0419: "Russian",
                    0x0491: "Ukrainian",
                    0x040D: "Hebrew",
                }
                layout_name = layout_names.get(lid, f"Layout ID: {hex(lid)}")
                return f"{layout_name} - {window_title}"
            else:
                # Linux and other - simplified approach
                return locale.getlocale()[0] or "Unknown"

        except Exception as e:
            return f"Error detecting layout: {str(e)}"    
    def update_keyboard_layout(self):
        """Update the keyboard layout indicator."""
        layout = self.get_current_keyboard_layout()
        self.layout_label.setText(f"Current keyboard layout: {layout}")

    def add_to_history(self, text):
        """Add text to clipboard history."""
        if not text.strip():
            return
        
        # Remove if this text is already in history
        for i in range(self.history_list.count()):
            if self.history_list.item(i).text() == text:
                self.history_list.takeItem(i)
                break

        # Add to the beginning
        self.history_list.insertItem(0, text)

        # Remove oldest items if we exceed max size
        while self.history_list.count() > self.max_history_size:
            self.history_list.takeItem(self.history_list.count() - 1)

    def history_item_clicked(self, item):
        """Handle click on a history item."""
        # Get the current text and history item text
        current_text = self.input_text.toPlainText()
        history_text = item.text()

        # Replace current text with history item text
        self.input_text.setPlainText(history_text)

        # Remove clicked item from history
        row = self.history_list.row(item)
        self.history_list.takeItem(row)

        # Add previous text to history if not empty
        if current_text.strip():
            self.add_to_history(current_text)

    def paste_from_clipboard(self):
        current_text = self.input_text.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        self.input_text.setPlainText(clipboard_text)
        if current_text.strip():
            self.add_to_history(current_text)
        self.add_to_history(clipboard_text)
        
    def clear_text(self):
        current_text = self.input_text.toPlainText()
        if current_text.strip():
            self.add_to_history(current_text)
        self.input_text.clear()

    def stop_typing(self):
        self.running = False
        self.reset_state("Typing stopped")

    def reset_state(self, status_text):
        self.running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText(status_text)

    def simulate_typing(self):
        if self.running:
            return
                
        text_to_type = self.input_text.toPlainText().strip()
        if not text_to_type:
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text()
            if not clipboard_text:
                QMessageBox.warning(self, "Warning", "Please enter text to type")
                return
            self.paste_from_clipboard()
            return
        
        self.add_to_history(text_to_type)

        sleep_seconds = self.sleep_time.value()
        self.status_label.setText(f"Starting in {sleep_seconds} seconds...")
        self.running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Use QTimer for non-blocking delay
        QTimer.singleShot(sleep_seconds * 1000, lambda: self.start_typing(text_to_type))

    def start_typing(self, text_to_type):
        try:
            self.status_label.setText("Now typing...")
            lines = text_to_type.split('\n')
            
            # Reset keyboard state
            keyboard.release('shift')
            keyboard.release('ctrl')
            keyboard.release('alt')
            time.sleep(0.8)
            
            for i, line in enumerate(lines):
                if not self.running:
                    break
                
                # Force keyboard buffer clear before typing each line
                keyboard.press_and_release('shift')
                
                # Type each character    
                for char in line:
                    if not self.running:
                        break
                            
                    # Force direct character typing instead of write()
                    if char in self.special_characters:
                        keys = self.special_characters[char]
                        if len(keys) == 2:
                            keyboard.press(keys[0])
                            keyboard.press(keys[1])
                            keyboard.release(keys[1])
                            keyboard.release(keys[0])
                        else:
                            keyboard.press_and_release(keys[0])
                    elif char.isupper():
                        keyboard.press('shift')
                        keyboard.press(char.lower())
                        keyboard.release(char.lower())
                        keyboard.release('shift')
                    else:
                        keyboard.press(char)
                        keyboard.release(char)
                        
                    QApplication.processEvents()
                    time.sleep(0.05)
                
                if i < len(lines) - 1:
                    keyboard.press_and_release('enter')
                    time.sleep(0.1)
                
                QApplication.processEvents()
                    
        except Exception as e:
            self.status_label.setText(f"Error typing: {e}")
            self.reset_state("Error occurred")
            return
                
        self.reset_state("Typing complete" if self.running else "Typing stopped")

def main():
    app = QApplication(sys.argv)
    window = ClipboardTyper()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()