import sys
import os
import json
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox, 
                            QTextEdit, QFileDialog, QComboBox, QGroupBox, QMessageBox,
                            QFormLayout, QScrollArea)
from PyQt6.QtCore import Qt, QProcess

# Constants
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robo_config.json")

class RobocopyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robocopy GUI")
        self.setGeometry(100, 100, 800, 600)
        self.saved_configs = self.load_configs()

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Source and dest selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        self.source_entry = QLineEdit()
        source_layout.addWidget(self.source_entry)
        source_button = QPushButton("Browse")
        source_button.clicked.connect(self.browse_source)
        source_layout.addWidget(source_button)
        main_layout.addLayout(source_layout)

        # Destination selection
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Destination:"))
        self.dest_entry = QLineEdit()
        dest_layout.addWidget(self.dest_entry)
        dest_button = QPushButton("Browse")
        dest_button.clicked.connect(self.browse_dest)
        dest_layout.addWidget(dest_button)
        main_layout.addLayout(dest_layout)

        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)

        # Copy Options group
        copy_group = QGroupBox("Copy Options")
        copy_layout = QHBoxLayout(copy_group)

        # Copy options
        copy_options = QVBoxLayout()
        copy_options.addWidget(QLabel("Copy options:"))
        self.mirror_checkbox = QCheckBox("Mirror (/MIR)")
        self.mirror_checkbox.stateChanged.connect(self.update_command)
        self.move_checkbox = QCheckBox("Move (/MOV)")
        self.move_checkbox.stateChanged.connect(self.update_command)
        self.copyall_checkbox = QCheckBox("Copy All (/COPYALL)")
        self.copyall_checkbox.setChecked(True)
        self.copyall_checkbox.stateChanged.connect(self.update_command)
        
        copy_options.addWidget(self.mirror_checkbox)
        copy_options.addWidget(self.move_checkbox)
        copy_options.addWidget(self.copyall_checkbox)
        
        copy_layout.addLayout(copy_options)

        # Exclude items options
        exclude_options = QVBoxLayout()
        exclude_options.addWidget(QLabel("Exclude options:"))
        self.exclude_older = QCheckBox("Exclude older files (/XO)")
        self.exclude_newer = QCheckBox("Exclude newer files (/XN)")
        exclude_options.addWidget(self.exclude_older)
        exclude_options.addWidget(self.exclude_newer)

        copy_layout.addLayout(exclude_options)

        # Retry Options
        retry_container = QWidget()
        retry_layout = QVBoxLayout(retry_container)
        retry_layout.setContentsMargins(0, 0, 0, 0)
        retry_layout.addWidget(QLabel("Retry Options:"))

        retry_options = QHBoxLayout()
        retry_options.addWidget(QLabel("Retry Failed Copies (/R:n)"))
        self.retries_spinbox= QSpinBox()
        self.retries_spinbox.setRange(1, 10)
        self.retries_spinbox.setValue(3)
        self.retries_spinbox.valueChanged.connect(self.update_command)
        retry_options.addWidget(self.retries_spinbox)

        wait_options = QHBoxLayout()
        wait_options.addWidget(QLabel("Wait time (sec)"))
        self.wait_spinbox= QSpinBox()
        self.wait_spinbox.setRange(1, 60)
        self.wait_spinbox.setValue(10)
        self.wait_spinbox.valueChanged.connect(self.update_command)
        wait_options.addWidget(self.wait_spinbox)

        retry_layout.addLayout(retry_options)
        retry_layout.addLayout(wait_options)

        copy_layout.addWidget(retry_container)
        settings_layout.addWidget(copy_group)

        # File selection options
        file_group = QGroupBox("File Selection Options")
        file_layout = QHBoxLayout(file_group)


        file_layout.addWidget(QLabel("File pattern (comma separated):"))
        self.file_pattern_entry = QLineEdit()
        file_layout.addWidget(self.file_pattern_entry)

        settings_layout.addWidget(file_group)

        main_layout.addWidget(settings_group)

        # Command preview
        main_layout.addWidget(QLabel("Command Preview:"))
        self.command_text = QTextEdit()
        self.command_text.setMaximumHeight(80)
        self.command_text.setReadOnly(True)
        main_layout.addWidget(self.command_text)

        # Results
        main_layout.addWidget(QLabel("Results:"))
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(120)
        self.results_text.setReadOnly(True)
        main_layout.addWidget(self.results_text)

        # Action buttons
        button_layout = QHBoxLayout()
        update_button = QPushButton("Update Command")
        update_button.clicked.connect(self.update_command)
        button_layout.addWidget(update_button)

        run_button = QPushButton("Run Command")
        run_button.clicked.connect(self.run_robocopy)
        button_layout.addWidget(run_button)

        clear_button = QPushButton("Clear Results")
        clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(clear_button)

        main_layout.addLayout(button_layout)

        # Initialize command preview
        self.process = None
        self.update_command()

    def browse_source(self):
        source_folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if source_folder:
            self.source_entry.setText(source_folder)
            self.update_command()
    
    def browse_dest(self):
        dest_folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if dest_folder:
            self.dest_entry.setText(dest_folder)
            self.update_command()
    
    def update_command(self):
        source = self.source_entry.text()
        dest = self.dest_entry.text()

        if not source or not dest:
            self.command_text.setText("Please select both source and destination folders.")
            return

        cmd = ["robocopy", f'"{source}"', f'"{dest}"']

        # Add File patterns if any
        if self.file_pattern_entry.text():
            patterns = self.file_pattern_entry.text().split(",")
            cmd.extend([pattern.strip() for pattern in patterns])
        
        # Add Options
        if self.mirror_checkbox.isChecked():
            cmd.append("/MIR")
        
        if self.move_checkbox.isChecked():
            cmd.append("/MOVE")
        
        if self.copyall_checkbox.isChecked():
            cmd.append("/COPYALL")
        
        cmd.append("/e")

        # Add retry and wait options
        cmd.append(f"/R:{self.retries_spinbox.value()}")
        cmd.append(f"/W:{self.wait_spinbox.value()}")

        # Display command
        self.command_text.setText(" ".join(cmd))

    def run_robocopy(self):
        command = self.command_text.toPlainText()

        if not command or "Please specify" in command:
            QMessageBox.critical(self, "Error", "Please provide source and destination folders.")
            return
        
        self.results_text.clear()
        self.results_text.append(f"Running command: {command}\n")
        
        # Create a QProcess to run the command
        if self.process is not None and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
        
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        self.process.finished.connect(self.handle_finished)
        
        # Run the command
        self.process.start(command)

    def handle_output(self):
        """Handle the output from the robocopy process."""
        output = self.process.readAllStandardOutput()
        self.results_text.append(output.data().decode())
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def handle_error(self):
        """Handle errors from the robocopy process."""
        error = self.process.readAllStandardError()
        self.results_text.append(error.data().decode())
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def handle_finished(self, exit_code, exit_status):
        """Handle the completion of the robocopy process."""
        self.results_text.append(f"Robocopy finished with exit code {exit_code} and status {exit_status}.")
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_results(self):
        """Clear the results text."""
        self.results_text.clear()

    def load_configs(self):
        """Load the list of configurations from a JSON file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as file:
                    return json.load(file)
            except Exception as e:
                print(f"Error loading configurations: {e}")
        return {}
    
    def save_configs(self):
        """Save the list of configurations to a JSON file."""
        try:
            with open(CONFIG_FILE, "w") as file:
                json.dump(self.saved_configs, file, indent=4)
        except Exception as e:
            print(f"Error saving configurations: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RobocopyGUI()
    window.show()
    sys.exit(app.exec())