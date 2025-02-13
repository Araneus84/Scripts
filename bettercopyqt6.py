from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                            QSpinBox, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
import keyboard
import time
import sys

class ClipboardTyper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyboard Typing Simulator")
        self.running = False
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
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
        
        # Add widgets to layout
        layout.addWidget(QLabel("Text to type:"))
        layout.addWidget(self.input_text)
        
        button_layout1 = QHBoxLayout()
        button_layout1.addWidget(self.Paste_from_clipboard_button)
        button_layout1.addWidget(self.clear_button)
        layout.addLayout(button_layout1)
        layout.addWidget(QLabel("Delay before typing (seconds):"))
        layout.addWidget(self.sleep_time)
        
        button_layout2 = QHBoxLayout()
        button_layout2.addWidget(self.start_button)
        button_layout2.addWidget(self.stop_button)
        layout.addLayout(button_layout2)        
        layout.addWidget(self.status_label)
        
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
        
    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        self.input_text.setPlainText(clipboard_text)
        
    def clear_text(self):
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
            first_char = True
            for i, line in enumerate(lines):
                if not self.running:
                    break
                    
                for char in line:
                    if not self.running:
                        break
                    if first_char:
                        time.sleep(0.8)
                        first_char = False
                        
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
                        keyboard.write(char)
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