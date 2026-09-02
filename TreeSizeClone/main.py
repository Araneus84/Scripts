import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QToolBar, QFileDialog, QProgressBar, QLineEdit, QPushButton, QCompleter
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import os
import time

class FolderScanner(QThread):
    progress = pyqtSignal(int)
    item_scanned = pyqtSignal(str, str, int, float, float)  # Added full path

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        total_items = sum(len(files) + len(dirs) for _, dirs, files in os.walk(self.folder_path))
        scanned_items = 0

        for root, dirs, files in os.walk(self.folder_path):
            for name in dirs + files:
                item_path = os.path.join(root, name)
                try:
                    size = os.path.getsize(item_path)
                    date_modified = os.path.getmtime(item_path)
                    date_created = os.path.getctime(item_path)

                    self.item_scanned.emit(name, item_path, size, date_modified, date_created)
                except (FileNotFoundError, PermissionError):
                    # Skip files that can't be accessed
                    pass
                
                scanned_items += 1
                progress = int((scanned_items / total_items) * 100)
                self.progress.emit(progress)
                time.sleep(0.01)  # Simulate delay for demonstration

class TreeSizeClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TreeSize Clone")
        self.setGeometry(100, 100, 800, 600)

        # Toolbar for selecting folder
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        select_folder_action = toolbar.addAction("Select Folder")
        select_folder_action.triggered.connect(self.select_folder)

        # Tree widget to display folder details
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Name", "Size", "Date Modified", "Date Created"])
        self.tree.setItemsExpandable(True)  # Enable tree-like expansion
        self.tree.setRootIsDecorated(True)  # Show tree structure decorations
        self.tree.setSortingEnabled(True)  # Re-enable sorting
        self.tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)  # Default sort by Size in descending order
        
        # Connect header clicks to custom sorting
        self.tree.header().sectionClicked.connect(self.on_header_clicked)
        
        # Store raw size values for proper sorting
        self.parent_items = {}  # Dictionary to track parent items by their full paths

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Input field and button for folder selection
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Enter folder path...")
        self.folder_button = QPushButton("Scan")
        self.folder_button.clicked.connect(self.manual_folder_select)

        # Set up auto-completion for the folder input field
        file_system_model = QFileSystemModel()
        file_system_model.setRootPath("")
        completer = QCompleter(file_system_model, self.folder_input)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.folder_input.setCompleter(completer)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.folder_input)
        layout.addWidget(self.folder_button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.scan_folder(folder_path)

    def manual_folder_select(self):
        folder_path = self.folder_input.text()
        if os.path.isdir(folder_path):
            self.scan_folder(folder_path)
        else:
            self.statusBar().showMessage("Invalid folder path", 5000)

    def scan_folder(self, folder_path):
        self.tree.clear()  # Clear existing items
        self.parent_items = {}  # Clear parent items
        self.progress_bar.setValue(0)

        # Explicitly add the root folder as a top-level item
        root_item = QTreeWidgetItem(self.tree, [os.path.basename(folder_path)])
        root_item.setIcon(0, QIcon.fromTheme("folder"))
        self.parent_items[folder_path] = root_item

        self.scanner = FolderScanner(folder_path)
        self.scanner.item_scanned.connect(self.add_item)
        self.scanner.finished.connect(lambda: self.expand_all_and_calculate(root_item))
        self.scanner.start()

    def on_header_clicked(self, column):
        order = self.tree.header().sortIndicatorOrder()
        self.custom_sort(column, order)

    def find_or_create_parent_item(self, parent_path):
        if parent_path in self.parent_items:
            return self.parent_items[parent_path]

        # If no parent exists, create a new top-level item for the root folder
        if parent_path == self.scanner.folder_path:
            parent_item = self.parent_items[parent_path]
        else:
            grandparent_path = os.path.dirname(parent_path)
            grandparent_item = self.find_or_create_parent_item(grandparent_path)

            # Check if the parent item already exists as a child of the grandparent
            for i in range(grandparent_item.childCount()):
                child = grandparent_item.child(i)
                if child.text(0) == os.path.basename(parent_path):
                    self.parent_items[parent_path] = child
                    return child

            # Create the current folder as a child of its parent
            parent_item = QTreeWidgetItem(grandparent_item, [os.path.basename(parent_path)])
            parent_item.setIcon(0, QIcon.fromTheme("folder"))
            self.parent_items[parent_path] = parent_item

        return parent_item

    def add_item(self, name, full_path, size, date_modified, date_created):
        human_readable_size = self.format_size(size)
        formatted_date_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(date_modified))
        formatted_date_created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(date_created))

        # Create or find the parent item
        parent_item = self.find_or_create_parent_item(os.path.dirname(full_path))
        item = QTreeWidgetItem(parent_item, [name, human_readable_size, formatted_date_modified, formatted_date_created])

        # Store raw size directly in the tree item using Qt's data role system
        item.setData(1, Qt.ItemDataRole.UserRole, size)  # Store raw size in column 1

        # Add an icon based on whether it's a file or folder
        if os.path.isdir(full_path):
            item.setIcon(0, QIcon.fromTheme("folder"))
        else:
            item.setIcon(0, QIcon.fromTheme("text-x-generic"))

        if parent_item != self.tree:
            parent_item.addChild(item)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @staticmethod
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024

    @staticmethod
    def parse_size(size_str):
        units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        size, unit = size_str.split()
        return float(size) * units[unit]

    def calculate_folder_size(self, parent_item):
        total_size = 0
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child_size = child.data(1, Qt.ItemDataRole.UserRole) or 0
            if child.childCount() > 0:  # If the child is a folder
                child_size = self.calculate_folder_size(child)
            total_size += child_size
        parent_item.setText(1, self.format_size(total_size))  # Update displayed size
        parent_item.setData(1, Qt.ItemDataRole.UserRole, total_size)  # Store folder size
        return total_size

    def recursive_sort(self, parent_item, column, order):
        children = [parent_item.child(i) for i in range(parent_item.childCount())]

        if column == 1:  # Size column
            children.sort(key=lambda item: item.data(1, Qt.ItemDataRole.UserRole) or 0, 
                         reverse=(order == Qt.SortOrder.DescendingOrder))

        for i in range(len(children)):
            parent_item.takeChild(0)  # Remove child without losing reference

        for i, child in enumerate(children):
            parent_item.insertChild(i, child)  # Reinsert child at the correct position
            self.recursive_sort(child, column, order)  # Recursively sort children

    def custom_sort(self, column, order):
        if column == 1:  # Size column
            for i in range(self.tree.topLevelItemCount()):
                top_item = self.tree.topLevelItem(i)
                self.calculate_folder_size(top_item)  # Ensure folder sizes are calculated
                self.recursive_sort(top_item, column, order)
        else:
            self.tree.sortItems(column, order)  # Use default sorting for other columns

    def expand_all_and_calculate(self, parent_item):
        self.calculate_folder_size(parent_item)  # Calculate sizes for all items
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            self.expand_all_and_calculate(child)  # Recursively expand and calculate sizes
        parent_item.setExpanded(True)  # Expand the current item

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TreeSizeClone()
    window.show()
    sys.exit(app.exec())
