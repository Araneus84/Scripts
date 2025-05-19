import sys
import random
import string
from PyQt6.QtGui import QClipboard
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox, QListWidget

class PasswordGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Password Generator")
        self.history = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Options
        options_layout = QHBoxLayout()
        self.length_label = QLabel("Length:")
        self.length_spin = QSpinBox()
        self.length_spin.setRange(4, 64)
        self.length_spin.setValue(12)
        options_layout.addWidget(self.length_label)
        options_layout.addWidget(self.length_spin)

        self.uppercase_cb = QCheckBox("Uppercase")
        self.uppercase_cb.setChecked(True)
        self.lowercase_cb = QCheckBox("Lowercase")
        self.lowercase_cb.setChecked(True)
        self.digits_cb = QCheckBox("Digits")
        self.digits_cb.setChecked(True)
        self.symbols_cb = QCheckBox("Symbols")
        self.symbols_cb.setChecked(True)
        

        options_layout.addWidget(self.uppercase_cb)
        options_layout.addWidget(self.lowercase_cb)
        options_layout.addWidget(self.digits_cb)
        options_layout.addWidget(self.symbols_cb)

        layout.addLayout(options_layout)

        # Password display
        self.password_list = QListWidget()
        layout.addWidget(self.password_list)
        # self.password_edit = QLineEdit()
        # self.password_edit.setReadOnly(True)
        # layout.addWidget(self.password_edit)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.copy_btn = QPushButton("Copy")
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addWidget(self.copy_btn)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Signals
        self.generate_btn.clicked.connect(self.generate_password)
        self.copy_btn.clicked.connect(self.copy_password)

    def generate_password(self):
        length = self.length_spin.value()
        chars = ""
        if self.uppercase_cb.isChecked():
            chars += string.ascii_uppercase
        if self.lowercase_cb.isChecked():
            chars += string.ascii_lowercase
        if self.digits_cb.isChecked():
            chars += string.digits
        if self.symbols_cb.isChecked():
            chars += string.punctuation

        if not chars:
            self.password_list.clear()
            self.password_list.addItem("Select at least one option!")
            return

        password = [''.join(random.choice(chars) for _ in range(length)) for _ in range(5)]
        self.password_list.clear()
        self.password_list.addItems(password)

        self.history.append(password)
        if len(self.history) > 10:
            self.history.pop(0)

    def copy_password(self):
        selected_items = self.password_list.currentItem()
        if selected_items:
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(selected_items.text())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PasswordGenerator()
    window.show()
    sys.exit(app.exec())