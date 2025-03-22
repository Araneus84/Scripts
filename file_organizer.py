#!/usr/bin/env python3
"""
File Organizer GUI - A PyQt6 application to organize files into folders based on their last modified year.
"""

import os
import sys
import shutil
import threading
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, 
                            QFileDialog, QMessageBox, QProgressBar, QStatusBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

class FileOrganizerWorker(QThread):
    """Worker thread for organizing files without freezing the GUI"""
    progress_update = pyqtSignal(int, int)  # current, total
    status_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, source_path, destination_path):
        super().__init__()
        self.source_path = source_path
        self.destination_path = destination_path
        self.running = True
    
    def run(self):
        try:
            # Ensure paths end with path separator
            source_path = os.path.join(self.source_path, '')
            destination_path = os.path.join(self.destination_path, '')
            
            # Verify the source path exists
            if not os.path.exists(source_path):
                self.finished.emit(False, f"Error: Source path does not exist: {source_path}")
                return
            
            # Create the destination path if it doesn't exist
            if not os.path.exists(destination_path):
                os.makedirs(destination_path)
                self.status_update.emit(f"Created destination directory: {destination_path}")
            
            # Get all files recursively from the source path
            self.status_update.emit("Scanning for files...")
            files = []
            for root, _, filenames in os.walk(source_path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            total_files = len(files)
            self.status_update.emit(f"Found {total_files} files to process")
            
            # Process each file
            for i, file_path in enumerate(files):
                if not self.running:
                    self.finished.emit(False, "Operation cancelled by user")
                    return
                
                # Update progress
                self.progress_update.emit(i + 1, total_files)
                
                # Get the last modified year
                year = str(datetime.fromtimestamp(os.path.getmtime(file_path)).year)
                
                # Create the year folder if it doesn't exist
                year_folder = os.path.join(destination_path, year)
                if not os.path.exists(year_folder):
                    os.makedirs(year_folder)
                    self.status_update.emit(f"Created year directory: {year_folder}")
                
                # Get the relative path of the file from the source root
                relative_path = os.path.relpath(file_path, source_path)
                relative_dir = os.path.dirname(relative_path)
                
                # If the file is in a subfolder, create the same structure in the year folder
                if relative_dir:
                    target_dir = os.path.join(year_folder, relative_dir)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                        self.status_update.emit(f"Created directory structure: {target_dir}")
                else:
                    target_dir = year_folder
                
                # Construct the destination file path
                dest_file = os.path.join(target_dir, os.path.basename(file_path))
                
                # Check if the destination file already exists
                if os.path.exists(dest_file):
                    self.status_update.emit(f"Warning: File already exists at destination: {dest_file}")
                    continue
                
                # Move the file
                try:
                    shutil.move(file_path, dest_file)
                    self.status_update.emit(f"Moved: {file_path} -> {dest_file}")
                except Exception as e:
                    self.status_update.emit(f"Error: Failed to move file {file_path}: {str(e)}")
            
            self.finished.emit(True, "File organization complete!")
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")
    
    def stop(self):
        """Stop the worker thread"""
        self.running = False


class FileOrganizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("File Organizer")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Source folder selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source Folder:"))
        self.source_edit = QLineEdit()
        source_layout.addWidget(self.source_edit)
        source_browse_btn = QPushButton("Browse...")
        source_browse_btn.clicked.connect(lambda: self.browse_folder(self.source_edit))
        source_layout.addWidget(source_browse_btn)
        main_layout.addLayout(source_layout)
        
        # Destination folder selection
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Destination Folder:"))
        self.dest_edit = QLineEdit()
        dest_layout.addWidget(self.dest_edit)
        self.dest_browse_btn = QPushButton("Browse...")
        self.dest_browse_btn.clicked.connect(lambda: self.browse_folder(self.dest_edit))
        dest_layout.addWidget(self.dest_browse_btn)
        main_layout.addLayout(dest_layout)
        
        # Same location checkbox
        self.same_location_check = QCheckBox("Use source folder as destination")
        self.same_location_check.setChecked(True)
        self.same_location_check.stateChanged.connect(self.toggle_destination)
        main_layout.addWidget(self.same_location_check)
        self.toggle_destination()  # Initialize state
        
        # Organize button
        button_layout = QHBoxLayout()
        self.organize_btn = QPushButton("Organize Files")
        self.organize_btn.clicked.connect(self.start_organizing)
        button_layout.addWidget(self.organize_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_organizing)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Results text area
        main_layout.addWidget(QLabel("Log:"))
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(self.font())
        main_layout.addWidget(self.results_text)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Export log button
        export_btn = QPushButton("Export Log")
        export_btn.clicked.connect(self.export_log)
        main_layout.addWidget(export_btn)
        
        # Show the window
        self.show()
    
    def browse_folder(self, line_edit):
        """Open folder browser dialog and set the selected path to the line edit"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)
            # If this is the source folder and "same location" is checked,
            # update the destination folder too
            if line_edit == self.source_edit and self.same_location_check.isChecked():
                self.dest_edit.setText(folder)
    
    def toggle_destination(self):
        """Enable/disable destination folder controls based on checkbox state"""
        is_same_location = self.same_location_check.isChecked()
        self.dest_edit.setEnabled(not is_same_location)
        self.dest_browse_btn.setEnabled(not is_same_location)
        
        if is_same_location:
            self.dest_edit.setText(self.source_edit.text())
    
    def start_organizing(self):
        """Start the file organization process"""
        source_path = self.source_edit.text()
        destination_path = self.dest_edit.text()
        
        if not source_path:
            QMessageBox.warning(self, "Missing Information", "Please select a source folder.")
            return
        
        if not os.path.exists(source_path):
            QMessageBox.critical(self, "Error", f"Source folder does not exist: {source_path}")
            return
        
        # Clear previous results
        self.results_text.clear()
        self.progress_bar.setValue(0)
        
        # Disable UI elements during processing
        self.organize_btn.setEnabled(False)
        self.source_edit.setEnabled(False)
        self.dest_edit.setEnabled(False)
        self.source_browse_btn.setEnabled(False)
        self.dest_browse_btn.setEnabled(False)
        self.same_location_check.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        # Log start of operation
        self.log_message("Starting file organization...")
        self.log_message(f"Source: {source_path}")
        self.log_message(f"Destination: {destination_path}")
        self.log_message("-" * 50)
        
        # Create and start worker thread
        self.worker = FileOrganizerWorker(source_path, destination_path)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.status_update.connect(self.log_message)
        self.worker.finished.connect(self.organizing_finished)
        self.worker.start()
    
    def cancel_organizing(self):
        """Cancel the file organization process"""
        if self.worker and self.worker.isRunning():
            self.log_message("Cancelling operation...")
            self.worker.stop()
    
    @pyqtSlot(int, int)
    def update_progress(self, current, total):
        """Update the progress bar"""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.status_bar.showMessage(f"Processing file {current} of {total} ({percentage}%)")
    
    @pyqtSlot(str)
    def log_message(self, message):
        """Add a message to the log"""
        self.results_text.append(message)
        # Scroll to the bottom
        self.results_text.verticalScrollBar().setValue(
            self.results_text.verticalScrollBar().maximum()
        )
    
    @pyqtSlot(bool, str)
    def organizing_finished(self, success, message):
        """Handle completion of the file organization process"""
        # Re-enable UI elements
        self.organize_btn.setEnabled(True)
        self.source_edit.setEnabled(True)
        self.source_browse_btn.setEnabled(True)
        self.same_location_check.setEnabled(True)
        self.toggle_destination()  # Reset destination field state
        self.cancel_btn.setEnabled(False)
        
        # Log completion message
        self.log_message("-" * 50)
        self.log_message(message)
        
        # Update status bar
        if success:
            self.status_bar.showMessage("File organization completed successfully")
        else:
            self.status_bar.showMessage("File organization failed or was cancelled")
        
        # Show message box
        if success:
            QMessageBox.information(self, "Complete", message)
        else:
            QMessageBox.warning(self, "Error", message)
    
    def export_log(self):
        """Export the log to a text file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Log File", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())
                QMessageBox.information(self, "Export Successful", f"Log exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export log: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileOrganizerApp()
    sys.exit(app.exec())
