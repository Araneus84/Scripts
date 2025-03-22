#!/usr/bin/env python3
"""
Duplicate File Finder - A PyQt6 application to find duplicate files across multiple folders.
"""

import os
import sys
import hashlib
import time
import subprocess
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, 
                            QFileDialog, QMessageBox, QProgressBar, QProgressDialog, QStatusBar, 
                            QListWidget, QListWidgetItem, QComboBox, QGroupBox, 
                            QSpinBox, QSplitter,QTreeWidget, QTreeWidgetItem, QDialog, QRadioButton, 
                            QButtonGroup, QVBoxLayout, QDialogButtonBox, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QSize, QDir
from PyQt6.QtGui import QFont

class DuplicateFinderWorker(QThread):
    """Worker thread for finding duplicate files without freezing the GUI"""
    progress_update = pyqtSignal(int, int, str, str)  # current, total, current_file, eta_str
    status_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str, dict)  # success, message, results
    phase1_complete = pyqtSignal(list) # Potenai duplicate files

    def __init__(self, folder_paths, algorithm, min_size_kb=0, max_size_kb=0, excluded_extensions=None, use_fast_scan=True):
        super().__init__()
        self.folder_paths = folder_paths
        self.algorithm = algorithm
        self.min_size_kb = min_size_kb
        self.max_size_kb = max_size_kb
        self.excluded_extensions = excluded_extensions or []
        self.use_fast_scan = use_fast_scan
        self.running = True
        self.wait_for_continue = False

    def run(self):
        try:
            # Validate folder paths
            for path in self.folder_paths:
                if not os.path.exists(path) or not os.path.isdir(path):
                    self.finished.emit(False, f"Folder path does not exist or is not a directory: {path}", {})
                    return
        
            self.status_update.emit("Scanning for files...")
        
            # Get all files from the specified folders
            all_files = []
            for path in self.folder_paths:
                try:
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            file_extension = os.path.splitext(file_path)[1].lower()
                            if file_extension in self.excluded_extensions:
                                continue
                            file_size = os.path.getsize(file_path)
                            # Check if file meets size requirements
                            if (self.min_size_kb == 0 or file_size >= (self.min_size_kb * 1024)) and (self.max_size_kb == 0 or file_size <= (self.max_size_kb * 1024)):
                                all_files.append(file_path)
                except Exception as e:
                    self.status_update.emit(f"Error scanning {path}: {str(e)}")
        
            total_files = len(all_files)
            self.status_update.emit(f"Found {total_files} files to process")

            # Phase 1: Fast Scan based on file size and last write time
            if self.use_fast_scan and total_files > 0:
                self.status_update.emit("Phase 1: Performing fast scan...")

                # Group files by size
                size_groups = {}
                for file_path in all_files:
                    file_size = os.path.getsize(file_path)
                    if file_size not in size_groups:
                        size_groups[file_size] = []
                    size_groups[file_size].append(file_path)

                # Filter out unique files
                potential_duplicates = []
                for size, files in size_groups.items():
                    if len(files) > 1:
                        # for files of the same size
                        time_groups = {}
                        for file_path in files:
                            try:
                                mod_time = os.path.getmtime(file_path)
                                # Round to nearest second to account for filesystem precision diff
                                mod_time_rounded = round(mod_time)
                                if mod_time_rounded not in time_groups:
                                    time_groups[mod_time_rounded] = []
                                time_groups[mod_time_rounded].append(file_path)
                            except Exception as e:
                                self.status_update.emit(f"Error getting modification time for {file_path}: {str(e)}")
                                # If we can't get mod time, just add to potential dups
                                potential_duplicates.append(file_path)
                            
                        # Add files with the same size and time
                        for time_group in time_groups.values():
                            if len(time_group) > 1:
                                potential_duplicates.extend(time_group)

                # Update list of files to process
                if potential_duplicates:
                    filtered_count = len(potential_duplicates)
                    self.status_update.emit(f"Fast scan found {filtered_count} potential duplicates out of {total_files} files")

                    # Group potential duplicates by size for display
                    size_to_files = {}
                    for file_path in potential_duplicates:
                        file_size = os.path.getsize(file_path)
                        if file_size not in size_to_files:
                            size_to_files[file_size] = []
                        size_to_files[file_size].append(file_path)

                    # Emit a special message
                    self.status_update.emit("--- POTENTIAL DUPLICATES ---")

                    # Show potential duplicates by size
                    for size, files in size_to_files.items():
                        if len(files) > 1:
                            self.status_update.emit(f"Size: {self.format_size(size)}")
                            for file_path in files:
                                try:
                                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                                    self.status_update.emit(f"  {file_path} - Mod Time: {mod_time}")
                                except Exception as e:
                                    self.status_update.emit(f"  {file_path} - Error getting mod time: {str(e)}")
                    self.status_update.emit("--- END POTENTIAL DUPLICATES ---")

                    # Emit a signal for phase 1 completion
                    self.phase1_complete.emit(potential_duplicates)

                    # Pause thread until told to continue
                    self.wait_for_continue = True
                    while self.wait_for_continue and self.running:
                        time.sleep(0.1)

                    # Check if we canceled during the wait
                    if not self.running:
                        self.finished.emit(False, "Operation cancelled by user", {})
                        return

                    # Resume phase 2
                    all_files = potential_duplicates
                    self.status_update.emit(f"Starting Phase 2: Calculating hashes for {filtered_count} files")

                    # Reset the progress to show the filtered list
                    self.progress_update.emit(0, filtered_count, "Starting hash calculation", "Calculating...")
                else:
                    self.status_update.emit(f"Fast scan didn't find any dupes based on size and time")
                    self.finished.emit(True, "No dupes found", {})
                    return
            
            # Phase 2: Calculate hashes
            self.status_update.emit(f"Phase 2: Calculating hashes for {len(all_files)} files")
        
            # Calculate hashes for all files
            file_hashes = {}
            processed_files = 0
            start_time = time.time()
        
            for file_path in all_files:
                if not self.running:
                    self.finished.emit(False, "Operation cancelled by user", {})
                    return
            
                processed_files += 1
            
                # Calculate ETA
                elapsed_time = time.time() - start_time
                if processed_files > 1:
                    estimated_total_time = elapsed_time / processed_files * total_files
                    remaining_time = estimated_total_time - elapsed_time
                    eta_str = self.format_time(remaining_time)
                else:
                    eta_str = "Calculating..."
            
                # Update progress
                self.progress_update.emit(processed_files, len(all_files), file_path, eta_str)
            
                # Calculate hash
                try:
                    file_hash = self.get_file_hash(file_path, self.algorithm)
                    if file_hash:
                        if file_hash not in file_hashes:
                            file_hashes[file_hash] = []
                        file_hashes[file_hash].append(file_path)
                except Exception as e:
                    self.status_update.emit(f"Error hashing {file_path}: {str(e)}")
        
            # Find duplicates
            duplicates = {hash_val: paths for hash_val, paths in file_hashes.items() if len(paths) > 1}
            duplicate_count = len(duplicates)
        
            self.status_update.emit(f"Found {duplicate_count} sets of duplicate files")
            # Prepare results
            self.finished.emit(True, f"Found {duplicate_count} sets of duplicate files", duplicates)
        
        except Exception as e:

            self.finished.emit(False, f"Error: {str(e)}", {})
    def get_file_hash(self, file_path, algorithm):
        """Calculate hash for a file using the specified algorithm"""
        try:
            hash_obj = None
            if algorithm == "MD5":
                hash_obj = hashlib.md5()
            elif algorithm == "SHA1":
                hash_obj = hashlib.sha1()
            elif algorithm == "SHA256":
                hash_obj = hashlib.sha256()
            elif algorithm == "SHA384":
                hash_obj = hashlib.sha384()
            elif algorithm == "SHA512":
                hash_obj = hashlib.sha512()
            else:
                return None
        
            with open(file_path, 'rb') as f:
                # Read the file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
        
            return hash_obj.hexdigest()
        except Exception as e:
            self.status_update.emit(f"Could not hash file: {file_path} - {str(e)}")
            return None

    def format_time(self, seconds):
        """Format seconds into a human-readable time string"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes {int(seconds % 60)} seconds"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours} hours {minutes} minutes"
    def format_size(self, size_bytes):
        """Format file size in bytes to human-readable format"""
        if size_bytes >= 1_000_000_000:
            return f"{size_bytes / 1_000_000_000:.2f} GB"
        elif size_bytes >= 1_000_000:
            return f"{size_bytes / 1_000_000:.2f} MB"
        elif size_bytes >= 1_000:
            return f"{size_bytes / 1_000:.2f} KB"
        else:
            return f"{size_bytes} bytes"
    def stop(self):
        """Stop the worker thread"""
        self.running = False
    
    def continue_to_phase2(self):
        """Resume phase 2 after user confirmation"""
        self.wait_for_continue = False

class DuplicateFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None
        self.duplicates = {}

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Duplicate File Finder")
        self.setMinimumSize(900, 700)
    
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
    
        # Folder selection group
        folder_group = QGroupBox("Folders to Scan")
        folder_layout = QVBoxLayout(folder_group)
    
        # Folder list
        self.folder_list = QListWidget()
        folder_layout.addWidget(self.folder_list)
    
        # Add/Remove buttons
        btn_layout = QHBoxLayout()
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(add_folder_btn)
    
        remove_folder_btn = QPushButton("Remove Folder")
        remove_folder_btn.clicked.connect(self.remove_folder)
        btn_layout.addWidget(remove_folder_btn)
    
        folder_layout.addLayout(btn_layout)
        main_layout.addWidget(folder_group)
    
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QHBoxLayout(options_group)

        # Exclusion list
        exclusion_group = QGroupBox("Extention Exclusions")
        exclusion_layout = QVBoxLayout(exclusion_group)

        exclusion_layout.addWidget(QLabel("Enter file extensions to exclude (e.g. jpg, png, pdf):"))
        self.exclusion_text = QLineEdit()
        self.exclusion_text.setPlaceholderText(".tmp, .log, .bak")
        exclusion_layout.addWidget(self.exclusion_text)
        
        main_layout.addWidget(exclusion_group)
        
        # Hash algorithm
        options_layout.addWidget(QLabel("Hash Algorithm:"))
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["MD5", "SHA1", "SHA256", "SHA384", "SHA512"])
        self.algorithm_combo.setCurrentText("MD5")
        options_layout.addWidget(self.algorithm_combo)
    
        # Minimum file size
        options_layout.addWidget(QLabel("Minimum Size:"))
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 1000000)
        self.min_size_spin.setValue(0)
        options_layout.addWidget(self.min_size_spin)
        
        self.size_unit_combo = QComboBox()
        self.size_unit_combo.addItems(["KB", "MB", "GB"])
        self.size_unit_combo.setCurrentText("KB")
        options_layout.addWidget(self.size_unit_combo)

        # Max file size
        options_layout.addWidget(QLabel("Max Size:"))
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 1000000)
        self.max_size_spin.setValue(0)
        options_layout.addWidget(self.max_size_spin)
    
        self.size_unit_combo = QComboBox()
        self.size_unit_combo.addItems(["KB", "MB", "GB"])
        self.size_unit_combo.setCurrentText("KB")
        options_layout.addWidget(self.size_unit_combo)

        # Fast scan option
        self.fast_scan_check = QCheckBox("Use fast pre-scan (Size & date)")
        self.fast_scan_check.setChecked(True)
        self.fast_scan_check.setToolTip("First group files by size and date to reduce scan time")
        options_layout.addWidget(self.fast_scan_check)
    
        # Save results option
        self.save_results_check = QCheckBox("Save results to file")
        options_layout.addWidget(self.save_results_check)
    
        options_layout.addStretch()
        main_layout.addWidget(options_group)
    
        # Find duplicates and cancel buttons
        button_layout = QHBoxLayout()
        self.find_btn = QPushButton("Find Duplicates")
        self.find_btn.clicked.connect(self.start_finding)
        button_layout.addWidget(self.find_btn)
    
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_finding)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
    
        main_layout.addLayout(button_layout)
    
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
    
        # Current file label
        self.current_file_label = QLabel("Ready")
        self.current_file_label.setWordWrap(True)
        main_layout.addWidget(self.current_file_label)
    
        # Results text area
        main_layout.addWidget(QLabel("Results:"))
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        main_layout.addWidget(self.results_text)
    
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
        # Export and delete buttons
        export_layout = QHBoxLayout()
    
        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_results)
        export_layout.addWidget(export_btn)
    
        main_layout.addLayout(export_layout)

        # Add duplicate management features
        self.add_duplicate_management_features()
    
        # Show the window
        self.show()
    def add_duplicate_management_features(self):
        """Add duplicate management features to the UI"""
        # Add a tree view for duplicate sets
        self.duplicate_tree = QTreeWidget()
        self.duplicate_tree.setHeaderLabels(["File Path", "Size", "Modified Date"])
        self.duplicate_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.duplicate_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.duplicate_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.duplicate_tree.setAlternatingRowColors(True)
        self.duplicate_tree.setVisible(False)  # Hide initially
        
        # Get the main layout from the central widget
        main_layout = self.centralWidget().layout()
        main_layout.addWidget(self.duplicate_tree)
        
        # Add management buttons
        management_layout = QHBoxLayout()
        
        self.browse_btn = QPushButton("Browse to File")
        self.browse_btn.clicked.connect(self.browse_to_file)
        self.browse_btn.setEnabled(False)
        management_layout.addWidget(self.browse_btn)
        
        self.recheck_btn = QPushButton("Recheck Selected")
        self.recheck_btn.clicked.connect(self.recheck_selected)
        self.recheck_btn.setEnabled(False)
        management_layout.addWidget(self.recheck_btn)
        
        self.archive_btn = QPushButton("Archive Duplicates")
        self.archive_btn.clicked.connect(self.archive_duplicates)
        self.archive_btn.setEnabled(False)
        management_layout.addWidget(self.archive_btn)
        
        self.delete_btn = QPushButton("Delete Duplicates")
        self.delete_btn.clicked.connect(self.delete_duplicates)
        self.delete_btn.setEnabled(False)
        management_layout.addWidget(self.delete_btn)
        
        main_layout.addLayout(management_layout)
        
        # Connect tree selection changed signal
        self.duplicate_tree.itemSelectionChanged.connect(self.update_button_states)

    def phase1_completed(self, potential_duplicates):
        """Called when phase 1 is complete"""
        self.potential_duplicates = potential_duplicates
        
        # Create message box for the user to proceed
        msg = QMessageBox()
        msg.setWindowTitle("Phase 1 Complete")
        msg.setText(f"Fast scan found {len(potential_duplicates)} potential duplicates")
        msg.setInformativeText("Fo you want to proceed with hash calculation in phase 2?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        # Add a button to view potential duplicates
        view_button = msg.addButton("View Details", QMessageBox.ButtonRole.ActionRole)

        # Show the message box
        result = msg.exec()

        # Handle the results
        if msg.clickedButton() == view_button:
            # Show the details of potential duplicates
            self.show_potential_duplicates()
            # Ash again after viewing
            self.phase1_completed(potential_duplicates)
        elif result == QMessageBox.StandardButton.Yes:
            # Proceed to phase 2
            self.worker.continue_to_phase2()
        else:
            # Cancel the operation
            self.cancel_finding()
            self.log_message("Operation canceled by user after phase 1.")
        
    def show_potential_duplicates(self):
        """Show a dialog of potential duplicates"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Potential Duplicates")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)

        # Add a label
        layout.addWidget(QLabel(f"Found {len(self.potential_duplicates)} potential duplicates based on size and mod time."))

        # Create a tree widget to display the dupes
        tree = QTreeWidget()
        tree.setHeaderLabels(["File Path", "Size", "Modified Time"])
        layout.addWidget(tree)

        # Group by size
        size_to_files = {}
        for file_path in self.potential_duplicates:
            try:
                file_size = os.path.getsize(file_path)
                if file_size not in size_to_files:
                    size_to_files[file_size] = []
                size_to_files[file_size].append(file_path)
            except Exception as e:
                self.log_message(f"Error getting file size for {file_path}: {e}")

        # Add Items to the tree
        for size, files in size_to_files.items():
            if len(files) > 1:
                size_item = QTreeWidgetItem(tree)
                size_item.setText(0, f"Size: {self.format_size(size)}")
                size_item.setExpanded(True)

                for file_path in files:
                    try:
                        modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                        file_item = QTreeWidgetItem(size_item)
                        file_item.setText(0, file_path)
                        file_item.setText(1, self.format_size(size))
                        file_item.setText(2, modified_time.strftime("%Y-%m-%d %H:%M:%S"))
                    except Exception as e:
                        self.log_message(f"Error adding file {file_path} to tree: {e}")
        # Add OK Button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)    
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        # Show the dialog
        dialog.exec()
    def archive_selected_files(self):
        """Archive only the selected files"""
        selected_items = self.duplicate_tree.selectedItems()
        if not selected_items:
            return
        
        # Get the file paths from the selected items
        file_paths = []
        for item in selected_items:
            # Only include file items (not set headers)
            if item.parent() is not None:
                file_paths.append(item.text(0))
        
        if not file_paths:
            QMessageBox.information(self, "No Files Selected", "No files were selected for archiving.")
            return
        
        # Ask user for archive file path
        archive_path, _ = QFileDialog.getSaveFileName(
            self, "Save Archive", "", "ZIP Files (*.zip);;All Files (*)"
        )
        
        if not archive_path:
            return
        
        # Ensure it has .zip extension
        if not archive_path.lower().endswith('.zip'):
            archive_path += '.zip'
        
        # Create the archive
        try:
            self.log_message(f"Creating archive: {archive_path}")
            self.log_message(f"Archiving {len(file_paths)} files...")
            
            # Create a progress dialog
            progress = QProgressDialog("Archiving files...", "Cancel", 0, len(file_paths), self)
            progress.setWindowTitle("Creating Archive")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Create the ZIP file
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, file_path in enumerate(file_paths):
                    if progress.wasCanceled():
                        break
                    
                    # Update progress
                    progress.setValue(i)
                    progress.setLabelText(f"Archiving: {os.path.basename(file_path)}")
                    
                    # Add the file to the ZIP, preserving the directory structure
                    try:
                        zipf.write(file_path, file_path)
                        self.log_message(f"Archived: {file_path}")
                    except Exception as e:
                        self.log_message(f"Error archiving {file_path}: {str(e)}")
            
            progress.setValue(len(file_paths))
            
            self.log_message(f"Archive created successfully: {archive_path}")
            QMessageBox.information(
                self, 
                "Archive Created", 
                f"Archive created successfully: {archive_path}\n\n"
                f"{len(file_paths)} files were archived."
            )
            
        except Exception as e:
            self.log_message(f"Error creating archive: {str(e)}")
            QMessageBox.critical(self, "Archive Failed", f"Failed to create archive: {str(e)}")

    def delete_duplicates(self):
        """Delete duplicate files, keeping one copy of each"""
        if not self.duplicates:
            QMessageBox.information(self, "No Duplicates", "No duplicate files to delete.")
            return
        
        # Get the selected duplicate set(s)
        selected_items = self.duplicate_tree.selectedItems()
        duplicate_sets_to_process = {}
        
        if selected_items:
            # Process only selected duplicate sets
            for item in selected_items:
                # If a file is selected, get its parent (the duplicate set)
                if item.parent() is not None:
                    parent = item.parent()
                    # Extract the hash from the parent text (format: "Duplicate Set #X (Hash: HASH)")
                    hash_text = parent.text(0)
                    hash_val = hash_text.split("Hash: ")[1].strip(")")
                    if hash_val in self.duplicates:
                        duplicate_sets_to_process[hash_val] = self.duplicates[hash_val]
                else:
                    # Extract the hash from the set header text
                    hash_text = item.text(0)
                    hash_val = hash_text.split("Hash: ")[1].strip(")")
                    if hash_val in self.duplicates:
                        duplicate_sets_to_process[hash_val] = self.duplicates[hash_val]
        else:
            # No selection, process all duplicate sets
            duplicate_sets_to_process = self.duplicates
        
        if not duplicate_sets_to_process:
            QMessageBox.information(self, "No Selection", "Please select at least one duplicate set to process.")
            return
        
        # Create a dialog to select which files to keep and which to delete
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Files to Keep")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("For each set of duplicates, select which file to keep:"))
        
        # Create a tree widget to display duplicate sets
        tree = QTreeWidget()
        tree.setHeaderLabels(["File Path", "Size", "Modified Date", "Action"])
        layout.addWidget(tree)
        
        # Populate the tree with duplicate sets
        button_groups = {}  # Store button groups by hash value
        
        for hash_val, files in duplicate_sets_to_process.items():
            # Check if files still exist
            existing_files = [f for f in files if os.path.exists(f)]
            if len(existing_files) < 2:
                continue  # Skip sets with fewer than 2 existing files
                
            set_item = QTreeWidgetItem(tree)
            set_item.setText(0, f"Duplicate Set (Hash: {hash_val})")
            set_item.setExpanded(True)
            
            # Create radio button group for this set
            button_group = QButtonGroup(dialog)
            button_groups[hash_val] = button_group
            
            # Add each file in the set
            for i, file_path in enumerate(existing_files):
                try:
                    file_size = os.path.getsize(file_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    file_item = QTreeWidgetItem(set_item)
                    file_item.setText(0, file_path)
                    file_item.setText(1, self.format_size(file_size))
                    file_item.setText(2, modified_time.strftime("%Y-%m-%d %H:%M:%S"))
                    
                    # Add a radio button to select which file to keep
                    radio = QRadioButton()
                    if i == 0:  # Select the first file by default
                        radio.setChecked(True)
                    button_group.addButton(radio, i)
                    tree.setItemWidget(file_item, 3, radio)
                except Exception as e:
                    self.log_message(f"Error processing file: {file_path} - {str(e)}")
        
        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show the dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Process the user's selections
        files_to_delete = []
        
        # For each duplicate set, determine which files to delete
        for hash_val, button_group in button_groups.items():
            if hash_val in duplicate_sets_to_process:
                files = [f for f in duplicate_sets_to_process[hash_val] if os.path.exists(f)]
                
                # Get the index of the file to keep
                keep_index = button_group.checkedId()
                
                # Add all other files to the delete list
                for i, file_path in enumerate(files):
                    if i != keep_index and os.path.exists(file_path):
                        files_to_delete.append(file_path)
        
        if not files_to_delete:
            QMessageBox.information(self, "No Files Selected", "No files were selected for deletion.")
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(files_to_delete)} files?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return

    def update_button_states(self):
        """Update button states based on tree selection"""
        selected_items = self.duplicate_tree.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.browse_btn.setEnabled(has_selection)
        self.recheck_btn.setEnabled(has_selection)
        
        # Only enable archive/delete if we have duplicates and at least one set is selected
        has_duplicates = len(self.duplicates) > 0
        self.archive_btn.setEnabled(has_duplicates)
        self.delete_btn.setEnabled(has_duplicates)

    def show_context_menu(self, position):
        """Show context menu for the duplicate tree"""
        selected_items = self.duplicate_tree.selectedItems()
        if not selected_items:
            return
        
        menu = QMenu()
        browse_action = menu.addAction("Browse to File")
        recheck_action = menu.addAction("Recheck with Different Algorithm")
        menu.addSeparator()
        archive_action = menu.addAction("Archive This Duplicate")
        delete_action = menu.addAction("Delete This Duplicate")
        
        # Only enable certain actions for file items (not set headers)
        is_file_item = selected_items[0].parent() is not None
        browse_action.setEnabled(is_file_item)
        recheck_action.setEnabled(is_file_item)
        archive_action.setEnabled(is_file_item)
        delete_action.setEnabled(is_file_item)
        
        action = menu.exec(self.duplicate_tree.mapToGlobal(position))
        
        if action == browse_action:
            self.browse_to_file()
        elif action == recheck_action:
            self.recheck_selected()
        elif action == archive_action:
            self.archive_selected_files()
        elif action == delete_action:
            self.delete_selected_files()

    def browse_to_file(self):
        """Open file explorer at the selected file's location"""
        selected_items = self.duplicate_tree.selectedItems()
        if not selected_items:
            return
        
        # Get the file path from the selected item
        item = selected_items[0]
        file_path = item.text(0)
        
        # If it's a set header, get the first file in the set
        if item.parent() is None and item.childCount() > 0:
            file_path = item.child(0).text(0)
        
        # Open file explorer at the file's location
        if os.path.exists(file_path):
            # Get the directory containing the file
            dir_path = os.path.dirname(file_path)
            
            # Open file explorer and select the file
            if sys.platform == 'win32':
                # Windows
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
            elif sys.platform == 'darwin':
                # macOS
                subprocess.run(['open', '-R', file_path])
            else:
                # Linux (try common file managers)
                try:
                    subprocess.run(['xdg-open', dir_path])
                except:
                    self.log_message(f"Could not open file explorer for: {dir_path}")
        else:
            QMessageBox.warning(self, "File Not Found", f"The file no longer exists: {file_path}")

    def recheck_selected(self):
        """Recheck selected files with a different hash algorithm"""
        selected_items = self.duplicate_tree.selectedItems()
        if not selected_items:
            return
        
        # Get all selected file paths
        file_paths = []
        for item in selected_items:
            # If it's a file item (has a parent)
            if item.parent() is not None:
                parent_item = item.parent()
                for i in range(parent_item.childCount()):
                    file_paths.append(parent_item.child(i).text(0))
            # If it's a set header, add all files in the set
            else:
                for i in range(item.childCount()):
                    file_paths.append(item.child(i).text(0))
        
        # Remove duplicates
        file_paths = list(set(file_paths))
        
        # Check if all files still exist
        missing_files = [path for path in file_paths if not os.path.exists(path)]
        if missing_files:
            QMessageBox.warning(
                self, 
                "Files Not Found", 
                f"The following files no longer exist:\n\n{chr(10).join(missing_files)}"
            )
            return
        
        # Ask user to select a different algorithm
        current_algo = self.algorithm_combo.currentText()
        algorithms = ["MD5", "SHA1", "SHA256", "SHA384", "SHA512"]
        algorithms.remove(current_algo)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Hash Algorithm")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Current algorithm: {current_algo}"))
        layout.addWidget(QLabel("Select a different algorithm to verify duplicates:"))
        
        button_group = QButtonGroup(dialog)
        for i, algo in enumerate(algorithms):
            radio = QRadioButton(algo)
            if i == 0:
                radio.setChecked(True)
            button_group.addButton(radio, i)
            layout.addWidget(radio)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_algo = algorithms[button_group.checkedId()]
            self.log_message(f"Rechecking {len(file_paths)} files with {selected_algo}...")
            
            # Create a new worker thread specifically for rechecking
            self.recheck_worker = DuplicateFinderWorker([os.path.dirname(file_paths[0])], selected_algo)
            
            # Pass the file paths to check as an attribute
            self.recheck_worker.files_to_check = file_paths
            
            # Create a custom run method for the recheck worker
            def custom_run():
                try:
                    # Calculate hashes for the specified files
                    file_hashes = {}
                    total_files = len(file_paths)
                    
                    for i, file_path in enumerate(file_paths):
                        if not self.recheck_worker.running:
                            self.recheck_worker.finished.emit(False, "Operation cancelled by user", {})
                            return
                        
                        # Update progress
                        self.recheck_worker.progress_update.emit(i + 1, total_files, file_path, "Rechecking")
                        
                        # Calculate hash
                        try:
                            file_hash = self.recheck_worker.get_file_hash(file_path, selected_algo)
                            if file_hash:
                                if file_hash not in file_hashes:
                                    file_hashes[file_hash] = []
                                file_hashes[file_hash].append(file_path)
                        except Exception as e:
                            self.recheck_worker.status_update.emit(f"Error hashing {file_path}: {str(e)}")
                    
                    # Find duplicates
                    duplicates = {hash_val: paths for hash_val, paths in file_hashes.items() if len(paths) > 1}
                    duplicate_count = len(duplicates)
                    
                    self.recheck_worker.status_update.emit(f"Found {duplicate_count} sets of duplicate files with {selected_algo}")
                    
                    # Prepare results
                    self.recheck_worker.finished.emit(True, f"Recheck complete: Found {duplicate_count} sets of duplicate files", duplicates)
                    
                except Exception as e:
                    self.recheck_worker.finished.emit(False, f"Error: {str(e)}", {})
            
            # Replace the run method
            self.recheck_worker.run = custom_run
            
            # Connect signals
            self.recheck_worker.progress_update.connect(self.update_progress)
            self.recheck_worker.status_update.connect(self.log_message)
            self.recheck_worker.finished.connect(self.recheck_finished)
            
            # Start the worker
            self.recheck_worker.start()
            
            # Disable UI elements during processing
            self.find_btn.setEnabled(False)
            self.folder_list.setEnabled(False)
            self.algorithm_combo.setEnabled(False)
            self.min_size_spin.setEnabled(False)
            self.max_size_spin.setEnabled(False)
            self.save_results_check.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.browse_btn.setEnabled(False)
            self.recheck_btn.setEnabled(False)
            self.archive_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def recheck_finished(self, success, message, duplicates):
        """Handle completion of the recheck process"""
        # Re-enable UI elements
        self.find_btn.setEnabled(True)
        self.folder_list.setEnabled(True)
        self.algorithm_combo.setEnabled(True)
        self.min_size_spin.setEnabled(True)
        self.max_size_spin.setEnabled(True)
        self.save_results_check.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.update_button_states()
        
        if success:
            # Log results
            self.log_message("-" * 50)
            self.log_message(message)
            
            if duplicates:
                # Display recheck results
                self.log_message("\nRecheck Results:")
                for hash_val, files in duplicates.items():
                    self.log_message(f"Hash: {hash_val}")
                    for file_path in files:
                        self.log_message(f"  {file_path}")
                    self.log_message("")
                
                QMessageBox.information(
                    self, 
                    "Recheck Complete", 
                    f"Recheck complete. Found {len(duplicates)} sets of duplicate files.\n\n"
                    "See the log for details."
                )
            else:
                QMessageBox.information(
                    self, 
                    "Recheck Complete", 
                    "The selected files are not duplicates according to the new algorithm."
                )
        else:
            QMessageBox.warning(self, "Recheck Failed", message)
    
    def refresh_duplicate_list(self):
        """Refresh the duplicate list to remove files that no longer exist"""
        updated_duplicates = {}
        
        for hash_val, files in self.duplicates.items():
            # Filter out files that no longer exist
            existing_files = [f for f in files if os.path.exists(f)]
            
            # Only keep sets with at least 2 files
            if len(existing_files) > 1:
                updated_duplicates[hash_val] = existing_files
        
        # Update the duplicates dictionary
        self.duplicates = updated_duplicates
        
        # Update the duplicate tree
        self.populate_duplicate_tree()

    def delete_duplicates(self):
        """Delete duplicate files, keeping one copy of each"""
        if not self.duplicates:
            QMessageBox.information(self, "No Duplicates", "No duplicate files to delete.")
            return
        
        # Create a dialog to select which files to keep and which to delete
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Files to Keep")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("For each set of duplicates, select which file to keep:"))
        
        # Create a tree widget to display duplicate sets
        tree = QTreeWidget()
        tree.setHeaderLabels(["File Path", "Size", "Modified Date", "Action"])
        layout.addWidget(tree)
        
        # Populate the tree with duplicate sets
        set_number = 1
        button_groups = {}  # Store button groups by set number
        
        for hash_val, files in self.duplicates.items():
            set_item = QTreeWidgetItem(tree)
            set_item.setText(0, f"Duplicate Set #{set_number} (Hash: {hash_val})")
            set_item.setExpanded(True)
            
            # Create radio button group for this set
            button_group = QButtonGroup(dialog)
            button_groups[set_number] = button_group  # Store for later reference
            
            # Add each file in the set
            for i, file_path in enumerate(files):
                try:
                    file_size = os.path.getsize(file_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    file_item = QTreeWidgetItem(set_item)
                    file_item.setText(0, file_path)
                    file_item.setText(1, self.format_size(file_size))
                    file_item.setText(2, modified_time.strftime("%Y-%m-%d %H:%M:%S"))
                    
                    # Add a radio button to select which file to keep
                    radio = QRadioButton()
                    if i == 0:  # Select the first file by default
                        radio.setChecked(True)
                    button_group.addButton(radio, i)
                    tree.setItemWidget(file_item, 3, radio)
                except Exception as e:
                    self.log_message(f"Error processing file: {file_path} - {str(e)}")
            
            set_number += 1
        
        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show the dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Process the user's selections
        files_to_delete = []
        
        # For each duplicate set, determine which files to delete
        set_number = 1
        for hash_val, files in self.duplicates.items():
            # Get the button group for this set
            if set_number in button_groups:
                button_group = button_groups[set_number]
                
                # Get the index of the file to keep
                keep_index = button_group.checkedId()
                
                # Add all other files to the delete list
                for i, file_path in enumerate(files):
                    if i != keep_index and os.path.exists(file_path):
                        files_to_delete.append(file_path)
            
            set_number += 1
        
        if not files_to_delete:
            QMessageBox.information(self, "No Files Selected", "No files were selected for deletion.")
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(files_to_delete)} files?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        # Delete the files
        try:
            self.log_message(f"Deleting {len(files_to_delete)} duplicate files...")
            
            # Create a progress dialog
            progress = QProgressDialog("Deleting files...", "Cancel", 0, len(files_to_delete), self)
            progress.setWindowTitle("Deleting Files")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            deleted_count = 0
            error_count = 0
            cancelled = False
            
            for i, file_path in enumerate(files_to_delete):
                if progress.wasCanceled():
                    cancelled = True
                    break
                
                # Update progress
                progress.setValue(i)
                progress.setLabelText(f"Deleting: {os.path.basename(file_path)}")
                
                # Delete the file
                try:
                    os.remove(file_path)
                    self.log_message(f"Deleted: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    self.log_message(f"Error deleting {file_path}: {str(e)}")
                    error_count += 1
            
            progress.setValue(len(files_to_delete) if not cancelled else i)
            
            # Update the results
            if cancelled:
                self.log_message(f"Operation cancelled. Deleted {deleted_count} files with {error_count} errors.")
                QMessageBox.warning(
                    self,
                    "Operation Cancelled",
                    f"Operation cancelled. {deleted_count} files deleted before cancellation.\n\n"
                    "The duplicate list will be updated to reflect the current state."
                )
            elif error_count == 0:
                self.log_message(f"Successfully deleted {deleted_count} duplicate files.")
                QMessageBox.information(
                    self, 
                    "Deletion Complete", 
                    f"Successfully deleted {deleted_count} duplicate files."
                )
            else:
                self.log_message(f"Deleted {deleted_count} files with {error_count} errors.")
                QMessageBox.warning(
                    self, 
                    "Deletion Completed with Errors", 
                    f"Deleted {deleted_count} files with {error_count} errors.\n\n"
                    "See the log for details."
                )
            
            # Update the duplicate list to remove deleted files
            self.refresh_duplicate_list()
            
        except Exception as e:
            self.log_message(f"Error during deletion: {str(e)}")
            QMessageBox.critical(self, "Deletion Failed", f"An error occurred: {str(e)}")

    def archive_duplicates(self):
        """Archive duplicate files while preserving directory structure"""
        if not self.duplicates:
            QMessageBox.information(self, "No Duplicates", "No duplicate files to archive.")
            return
        
        # Get the selected duplicate set(s)
        selected_items = self.duplicate_tree.selectedItems()
        duplicate_sets_to_process = {}
        if selected_items:
            # Process only selected duplicate sets
            for item in selected_items:
                # If a file is selected, get its parent (the duplicate set)
                if item.parent() is not None:
                    parent = item.parent()
                    # Extract the hash from the parent text (format: "Duplicate Set #X (Hash: HASH)")
                    hash_text = parent.text(0)
                    hash_val = hash_text.split("Hash: ")[1].strip(")")
                    if hash_val in self.duplicates:
                        duplicate_sets_to_process[hash_val] = self.duplicates[hash_val]
                else:
                    # Extract the hash from the set header text
                    hash_text = item.text(0)
                    hash_val = hash_text.split("Hash: ")[1].strip(")")
                    if hash_val in self.duplicates:
                        duplicate_sets_to_process[hash_val] = self.duplicates[hash_val]
        else:
            # No selection, process all duplicate sets
            duplicate_sets_to_process = self.duplicates
        
        if not duplicate_sets_to_process:
            QMessageBox.information(self, "No Selection", "Please select at least one duplicate set to archive.")
            return
        
        # Ask user for archive file path
        archive_path, _ = QFileDialog.getSaveFileName(
            self, "Save Archive", "", "ZIP Files (*.zip);;All Files (*)"
        )
        
        if not archive_path:
            return
        
        # Ensure it has .zip extension
        if not archive_path.lower().endswith('.zip'):
            archive_path += '.zip'
        
        # Create a dialog to select which files to keep and which to archive
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Files to Archive")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("For each set of duplicates, select which file to keep (unarchived):"))
        
        # Create a tree widget to display duplicate sets
        tree = QTreeWidget()
        tree.setHeaderLabels(["File Path", "Size", "Modified Date", "Action"])
        layout.addWidget(tree)
        
        # Populate the tree with duplicate sets
        button_groups = {}  # Store button groups by hash value
        
        for hash_val, files in duplicate_sets_to_process.items():
            # Check if files still exist
            existing_files = [f for f in files if os.path.exists(f)]
            if len(existing_files) < 2:
                continue  # Skip sets with fewer than 2 existing files
                
            set_item = QTreeWidgetItem(tree)
            set_item.setText(0, f"Duplicate Set (Hash: {hash_val})")
            set_item.setExpanded(True)
            
            # Create radio button group for this set
            button_group = QButtonGroup(dialog)
            button_groups[hash_val] = button_group
            
            # Add each file in the set
            for i, file_path in enumerate(existing_files):
                try:
                    file_size = os.path.getsize(file_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    file_item = QTreeWidgetItem(set_item)
                    file_item.setText(0, file_path)
                    file_item.setText(1, self.format_size(file_size))
                    file_item.setText(2, modified_time.strftime("%Y-%m-%d %H:%M:%S"))
                    
                    # Add a radio button to select which file to keep
                    radio = QRadioButton()
                    if i == 0:  # Select the first file by default
                        radio.setChecked(True)
                    button_group.addButton(radio, i)
                    tree.setItemWidget(file_item, 3, radio)
                except Exception as e:
                    self.log_message(f"Error processing file: {file_path} - {str(e)}")
        
        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show the dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Process the user's selections
        files_to_archive = []
        
        # For each duplicate set, determine which files to archive
        for hash_val, button_group in button_groups.items():
            if hash_val in duplicate_sets_to_process:
                files = [f for f in duplicate_sets_to_process[hash_val] if os.path.exists(f)]
                
                # Get the index of the file to keep (not archive)
                keep_index = button_group.checkedId()
                
                # Add all other files to the archive list
                for i, file_path in enumerate(files):
                    if i != keep_index and os.path.exists(file_path):
                        files_to_archive.append(file_path)
        
        if not files_to_archive:
            QMessageBox.information(self, "No Files Selected", "No files were selected for archiving.")
            return
        
        # Create the archive
        try:
            self.log_message(f"Creating archive: {archive_path}")
            self.log_message(f"Archiving {len(files_to_archive)} files...")
            
            # Create a progress dialog
            progress = QProgressDialog("Archiving files...", "Cancel", 0, len(files_to_archive), self)
            progress.setWindowTitle("Creating Archive")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # Create the ZIP file
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                archived_count = 0
                error_count = 0
                cancelled = False
                
                for i, file_path in enumerate(files_to_archive):
                    if progress.wasCanceled():
                        cancelled = True
                        break
                    
                    # Update progress
                    progress.setValue(i)
                    progress.setLabelText(f"Archiving: {os.path.basename(file_path)}")
                    
                    # Add the file to the ZIP, preserving the directory structure
                    try:
                        if os.path.exists(file_path):
                            zipf.write(file_path, file_path)
                            self.log_message(f"Archived: {file_path}")
                            archived_count += 1
                        else:
                            self.log_message(f"File no longer exists: {file_path}")
                            error_count += 1
                    except Exception as e:
                        self.log_message(f"Error archiving {file_path}: {str(e)}")
                        error_count += 1
            
            progress.setValue(len(files_to_archive) if not cancelled else i)
            
            # Show results
            if cancelled:
                self.log_message(f"Operation cancelled. Archived {archived_count} files with {error_count} errors.")
                QMessageBox.warning(
                    self, 
                    "Operation Cancelled", 
                    f"Operation cancelled. {archived_count} files were archived before cancellation."
                )
            elif error_count == 0:
                self.log_message(f"Archive created successfully: {archive_path}")
                QMessageBox.information(
                    self, 
                    "Archive Created", 
                    f"Archive created successfully: {archive_path}\n\n"
                    f"{archived_count} files were archived."
                )
            else:
                self.log_message(f"Archive created with {error_count} errors: {archive_path}")
                QMessageBox.warning(
                    self, 
                    "Archive Created with Errors", 
                    f"Archive created with {error_count} errors: {archive_path}\n\n"
                    f"{archived_count} files were archived successfully.\n"
                    "See the log for details."
                )
            
        except Exception as e:
            self.log_message(f"Error creating archive: {str(e)}")
            QMessageBox.critical(self, "Archive Failed", f"Failed to create archive: {str(e)}")

    def add_folder(self):
        """Add a folder to the list of folders to scan"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            # Check if folder is already in the list
            existing_items = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
            if folder_path not in existing_items:
                self.folder_list.addItem(folder_path)
    
    def remove_folder(self):
        """Remove the selected folder from the list"""
        selected_items = self.folder_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.folder_list.takeItem(self.folder_list.row(item))

    def start_finding(self):
        """Start the duplicate file finding process"""
        # Get the list of folders to scan
        folder_paths = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]

        # Fast scan option
        use_fast_scan = self.fast_scan_check.isChecked()
    
        if not folder_paths:
            QMessageBox.warning(self, "Missing Information", "Please add at least one folder to scan.")
            return
    
        # Get options
        algorithm = self.algorithm_combo.currentText()
        min_size_value = self.min_size_spin.value()
        max_size_value = self.max_size_spin.value()
        size_unit = self.size_unit_combo.currentText()

        # Convert minimum size to KB based on selected unit
        if size_unit == "MB":
            min_size_kb = min_size_value * 1024
            max_size_kb = max_size_value * 1024
        elif size_unit == "GB":
            min_size_kb = min_size_value * 1024 * 1024
            max_size_kb = max_size_value * 1024 * 1024
        else:
            min_size_kb = min_size_value
            max_size_kb = max_size_value
        
        # Exclusion list
        exclusion_text = self.exclusion_text.text().strip()
        excluded_extensions = []
        if exclusion_text:
            extensions = [ext.strip().lower() for ext in exclusion_text.split(',')]
            excluded_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]

        # Clear previous results
        self.results_text.clear()
        self.progress_bar.setValue(0)
        self.current_file_label.setText("Starting scan...")
    
        # Disable UI elements during processing
        self.find_btn.setEnabled(False)
        self.folder_list.setEnabled(False)
        self.algorithm_combo.setEnabled(False)
        self.min_size_spin.setEnabled(False)
        self.max_size_spin.setEnabled(False)
        self.size_unit_combo.setEnabled(False)  # Also disable the unit combo
        self.exclusion_text.setEnabled(False)
        self.save_results_check.setEnabled(False)
        self.cancel_btn.setEnabled(True)
    
        # Log start of operation
        self.log_message("Starting duplicate file search...")
        self.log_message(f"Folders to scan: {', '.join(folder_paths)}")
        self.log_message(f"Hash algorithm: {algorithm}")
        self.log_message(f"Minimum file size: {min_size_value} {size_unit}")
        self.log_message(f"Maximum file size: {max_size_value} {size_unit}")
        if excluded_extensions:
            self.log_message(f"Excluding files with extensions: {', '.join(excluded_extensions)}")
        self.log_message(f"Fast pre-scan: {'Enabled' if use_fast_scan else 'Disabled'}")
        self.log_message("-" * 50)
    
        # Create and start worker thread
        self.worker = DuplicateFinderWorker(folder_paths, algorithm, min_size_kb, max_size_kb, excluded_extensions, use_fast_scan)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.status_update.connect(self.log_message)
        self.worker.finished.connect(self.finding_finished)
        self.worker.phase1_complete.connect(self.phase1_completed)
        self.worker.start()

    def cancel_finding(self):
        """Cancel the duplicate file finding process"""
        if self.worker and self.worker.isRunning():
            self.log_message("Cancelling operation...")
            self.worker.stop()

    @pyqtSlot(int, int, str, str)
    def update_progress(self, current, total, current_file, eta_str):
        """Update the progress bar and current file label"""
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.current_file_label.setText(f"Processing: {current_file}")
        self.status_bar.showMessage(f"Processing file {current} of {total} ({percentage}%) - ETA: {eta_str}")

    @pyqtSlot(str)
    def log_message(self, message):
        """Add a message to the log"""
        # Check for special markers
        if message == "--- POTENTIAL DUPLICATES ---":
            self.results_text.append("\n" + "="*50)
            self.results_text.append("POTENTIAL DUPLICATES:")
            self.results_text.append("These files have the same size and mod time")
            self.results_text.append("="*50 + "\n")
            return
        elif message == "--- END POTENTIAL DUPLICATES ---":
            self.results_text.append("\n" + "="*50)
            self.results_text.append("END OF POTENTIAL DUPLICATES")
            self.results_text.append("="*50 + "\n")
            return

        self.results_text.append(message)
        # Scroll to the bottom
        self.results_text.verticalScrollBar().setValue(
            self.results_text.verticalScrollBar().maximum()
        )
    # @pyqtSlot(bool, str, dict)
    @pyqtSlot(bool, str, dict)
    def finding_finished(self, success, message, duplicates):
        """Handle completion of the duplicate file finding process"""
        # Store duplicates for later use
        self.duplicates = duplicates
        
        # Re-enable UI elements
        self.find_btn.setEnabled(True)
        self.folder_list.setEnabled(True)
        self.algorithm_combo.setEnabled(True)
        self.min_size_spin.setEnabled(True)
        self.max_size_spin.setEnabled(True)
        self.size_unit_combo.setEnabled(True)  # Re-enable the unit combo
        self.exclusion_text.setEnabled(True)  # Re-enable the exclusion text
        self.save_results_check.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # Log completion message
        self.log_message("-" * 50)
        self.log_message(message)
        
        # Display duplicate sets
        if success and duplicates:
            duplicate_count = len(duplicates)
            duplicate_file_count = sum(len(files) - 1 for files in duplicates.values())
            wasted_space = sum(
                (len(files) - 1) * os.path.getsize(files[0]) for files in duplicates.values()
            )
            
            self.log_message("\nDuplicate Files Report")
            self.log_message("=======================")
            self.log_message(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_message(f"Total Files Scanned: {self.progress_bar.value()}")
            self.log_message(f"Duplicate Sets Found: {duplicate_count}")
            self.log_message("")
            
            # Display each duplicate set
            set_number = 1
            for hash_val, files in duplicates.items():
                file_size = os.path.getsize(files[0])
                self.log_message(f"Duplicate Set #{set_number} (Hash: {hash_val})")
                self.log_message("-" * 40)
                for file_path in files:
                    file_obj = Path(file_path)
                    modified_time = datetime.fromtimestamp(file_obj.stat().st_mtime)
                    self.log_message(f"  {file_path} ({self.format_size(file_size)}, Modified: {modified_time})")
                self.log_message("")
                set_number += 1
            
            # Display summary
            self.log_message("Summary:")
            self.log_message(f"  Total duplicate files: {duplicate_file_count}")
            self.log_message(f"  Wasted space: {self.format_size(wasted_space)}")
            
            # Auto-save results if option is checked
            if self.save_results_check.isChecked():
                self.export_results()
                
            # Populate the duplicate tree
            self.populate_duplicate_tree()
        
        elif success:
            self.log_message("No duplicate files found.")
            self.duplicate_tree.clear()
            self.duplicate_tree.setVisible(False)
        
        # Update status bar
        if success:
            self.status_bar.showMessage("Duplicate file search completed successfully")
            self.current_file_label.setText("Ready")
        else:
            self.status_bar.showMessage("Duplicate file search failed or was cancelled")
            self.current_file_label.setText("Operation failed or cancelled")
    
    def populate_duplicate_tree(self):
        """Populate the duplicate tree with the current duplicates"""
        # Clear the tree
        self.duplicate_tree.clear()
        
        if not self.duplicates:
            self.duplicate_tree.setVisible(False)
            return
        
        # Show the tree
        self.duplicate_tree.setVisible(True)
        
        # Add duplicate sets to the tree
        set_number = 1
        for hash_val, files in self.duplicates.items():
            set_item = QTreeWidgetItem(self.duplicate_tree)

            # Check if any files in this set still exist
            existing_files = [f for f in files if os.path.exists(f)]
            if existing_files:
                try:
                    file_size = os.path.getsize(existing_files[0])
                except Exception as e:
                    self.log_message(f"Error getting file size: {str(e)}")

            try:
                file_size = os.path.getsize(existing_files[0])
                set_item.setText(0, f"Duplicate Set #{set_number} (Hash: {hash_val})")
                set_item.setText(1, self.format_size(file_size))
                set_item.setExpanded(True)
            
                # Add each file in the set
                for file_path in existing_files:
                    try:
                        modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        file_item = QTreeWidgetItem(set_item)
                        file_item.setText(0, file_path)
                        file_item.setText(1, self.format_size(file_size))
                        file_item.setText(2, modified_time.strftime("%Y-%m-%d %H:%M:%S"))
                    except Exception as e:
                        self.log_message(f"Error adding file to tree: {file_path} - {str(e)}")
                    
            except Exception as e:
                self.log_message(f"Error processing duplicate set: {hash_val} - {str(e)}")
        set_number += 1
    
        # Resize columns to content
        for i in range(self.duplicate_tree.columnCount()):
            self.duplicate_tree.resizeColumnToContents(i)
        
        # Update button states
        self.update_button_states()

    def format_size(self, size_bytes):
        """Format file size in bytes to human-readable format"""
        if size_bytes >= 1_000_000_000:
            return f"{size_bytes / 1_000_000_000:.2f} GB"
        elif size_bytes >= 1_000_000:
            return f"{size_bytes / 1_000_000:.2f} MB"
        elif size_bytes >= 1_000:
            return f"{size_bytes / 1_000:.2f} KB"
        else:
            return f"{size_bytes} bytes"
    
    def export_results(self):
        """Export the results to a text file"""
        if not self.results_text.toPlainText():
            QMessageBox.information(self, "No Results", "There are no results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())
                QMessageBox.information(self, "Export Successful", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export results: {str(e)}")


if __name__ == "__main__":
            app = QApplication(sys.argv)
            window = DuplicateFinderApp()
            sys.exit(app.exec())
