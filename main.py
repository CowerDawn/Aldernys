import os
import sys
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileSystemModel, QListView, QSplitter,
    QToolBar, QAction, QLineEdit, QStatusBar, QMessageBox, QMenu, 
    QDockWidget, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtGui import QIcon, QKeySequence, QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QDir, QSize, QMimeData, QTimer, QFileInfo


class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aldernys File Manager")
        self.setGeometry(100, 100, 1024, 768)
        
        self.setWindowIcon(QIcon.fromTheme("system-file-manager"))
        self.set_kde_style()
        
        self.create_menu()
        self.config_file = os.path.join(QDir.homePath(), ".aldernys_config.json")
        self.pinned_folders = self.load_pinned_folders()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden)

        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setRootIndex(self.model.index(QDir.homePath()))
        self.list_view.setViewMode(QListView.IconMode)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setIconSize(QSize(64, 64))
        self.list_view.setGridSize(QSize(100, 80))
        self.list_view.setSelectionMode(QListView.ExtendedSelection)
        self.list_view.doubleClicked.connect(self.on_item_double_clicked)
        self.list_view.setDragEnabled(True)
        self.list_view.setAcceptDrops(True)
        self.list_view.setDropIndicatorShown(True)
        self.list_view.dragEnterEvent = self.dragEnterEvent
        self.list_view.dragMoveEvent = self.dragMoveEvent
        self.list_view.dropEvent = self.dropEvent

        self.sidebar = QDockWidget("Places", self)
        self.sidebar.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.sidebar_widget = QListWidget()
        self.sidebar_widget.itemClicked.connect(self.on_sidebar_item_clicked)
        self.sidebar_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sidebar_widget.customContextMenuRequested.connect(self.show_sidebar_context_menu)
        self.sidebar.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.update_sidebar()

        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)

        self.back_action = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        self.back_action.setShortcut(QKeySequence("Backspace"))
        self.back_action.triggered.connect(self.go_back)
        self.toolbar.addAction(self.back_action)

        self.forward_action = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        self.forward_action.setShortcut(QKeySequence("Ctrl+F"))
        self.forward_action.triggered.connect(self.go_forward)
        self.toolbar.addAction(self.forward_action)

        self.home_action = QAction(QIcon.fromTheme("go-home"), "Home", self)
        self.home_action.setShortcut(QKeySequence("Ctrl+H"))
        self.home_action.triggered.connect(self.go_home)
        self.toolbar.addAction(self.home_action)

        self.toolbar.addSeparator()

        self.refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        self.refresh_action.setShortcut(QKeySequence("F5"))
        self.refresh_action.triggered.connect(self.refresh)
        self.toolbar.addAction(self.refresh_action)

        self.pin_action = QAction(QIcon.fromTheme("bookmark-new"), "Pin Folder", self)
        self.pin_action.triggered.connect(self.pin_current_folder)
        self.toolbar.addAction(self.pin_action)

        self.toolbar.addSeparator()

        self.path_edit = QLineEdit()
        self.path_edit.setMinimumWidth(300)
        self.path_edit.returnPressed.connect(self.navigate_to_path)
        self.toolbar.addWidget(self.path_edit)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.setCentralWidget(self.list_view)

        self.history = []
        self.history_index = -1
        self.current_path = QDir.homePath()
        self.update_path(self.model.index(self.current_path))

        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)

    def set_kde_style(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(239, 239, 239))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(233, 231, 227))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(227, 227, 227))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(61, 174, 233))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setPalette(palette)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #eaeaea;
                font: 11px;
            }
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f6f6f6, stop:1 #d4d4d4);
                border: 1px solid #a0a0a0;
                border-radius: 4px;
                padding: 2px;
                spacing: 3px;
            }
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f6f6f6, stop:1 #e0e0e0);
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 3px;
                min-width: 24px;
                min-height: 24px;
            }
            QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e8e8, stop:1 #d0d0d0);
            }
            QToolButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d0d0d0, stop:1 #b0b0b0);
            }
            QListView {
                background-color: white;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                font: 11px;
            }
            QListView::item {
                padding: 5px;
                border: 1px solid transparent;
                border-radius: 3px;
            }
            QListView::item:hover {
                background-color: #e0e0e0;
                border: 1px solid #a0a0a0;
            }
            QListView::item:selected {
                background-color: #3daee9;
                color: white;
            }
            QDockWidget {
                background: #eaeaea;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                titlebar-close-icon: url(none);
                titlebar-normal-icon: url(none);
            }
            QDockWidget::title {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f6f6f6, stop:1 #d4d4d4);
                padding: 3px;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                font: 11px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f6f6f6, stop:1 #d4d4d4);
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                font: 11px;
            }
            QLineEdit {
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 3px;
                background: white;
            }
        """)

    def load_pinned_folders(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return [
            QDir.homePath(),
            os.path.join(QDir.homePath(), "Documents"),
            os.path.join(QDir.homePath(), "Downloads"),
        ]

    def save_pinned_folders(self):
        with open(self.config_file, "w") as f:
            json.dump(self.pinned_folders, f)

    def update_sidebar(self):
        self.sidebar_widget.clear()
        self.pinned_folders = [folder for folder in self.pinned_folders if os.path.exists(folder)]
        self.save_pinned_folders()

        for folder in self.pinned_folders:
            item = QListWidgetItem(QIcon.fromTheme("folder-bookmark"), os.path.basename(folder))
            item.setData(Qt.UserRole, folder)
            self.sidebar_widget.addItem(item)

        self.sidebar_widget.addItem(QListWidgetItem(QIcon.fromTheme("user-home"), "Home"))
        self.sidebar_widget.item(self.sidebar_widget.count()-1).setData(Qt.UserRole, QDir.homePath())

        drives = QDir.drives()
        for drive in drives:
            drive_path = drive.absolutePath()
            item = QListWidgetItem(QIcon.fromTheme("drive-harddisk"), drive_path)
            item.setData(Qt.UserRole, drive_path)
            self.sidebar_widget.addItem(item)

    def pin_current_folder(self):
        if self.current_path not in self.pinned_folders:
            self.pinned_folders.append(self.current_path)
            self.update_sidebar()
            self.save_pinned_folders()

    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.list_view.setRootIndex(index)
            self.add_to_history(path)
        else:
            self.open_file(path)

    def open_file(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def on_sidebar_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        self.list_view.setRootIndex(self.model.index(path))
        self.add_to_history(path)

    def navigate_to_path(self):
        path = self.path_edit.text()
        if os.path.exists(path):
            self.list_view.setRootIndex(self.model.index(path))
            self.add_to_history(path)
        else:
            QMessageBox.warning(self, "Error", "The specified path does not exist.")

    def update_path(self, index):
        self.current_path = self.model.filePath(index)
        self.path_edit.setText(self.current_path)
        self.status_bar.showMessage(f"Files: {self.model.rowCount(index)}")

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(self.create_file)
        file_menu.addAction(new_file_action)

        new_folder_action = QAction("New Folder", self)
        new_folder_action.triggered.connect(self.create_directory)
        file_menu.addAction(new_folder_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("&Edit")
        copy_action = QAction("Copy", self)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        edit_menu.addAction(paste_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_item)
        edit_menu.addAction(delete_action)

        view_menu = menubar.addMenu("&View")
        self.toggle_hidden_action = QAction("Show Hidden", self)
        self.toggle_hidden_action.setCheckable(True)
        self.toggle_hidden_action.toggled.connect(self.toggle_hidden_files)
        view_menu.addAction(self.toggle_hidden_action)

        go_menu = menubar.addMenu("&Go")
        back_action = QAction("Back", self)
        back_action.triggered.connect(self.go_back)
        go_menu.addAction(back_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self.go_forward)
        go_menu.addAction(forward_action)

        home_action = QAction("Home", self)
        home_action.triggered.connect(self.go_home)
        go_menu.addAction(home_action)

        bookmarks_menu = menubar.addMenu("&Bookmarks")
        add_bookmark_action = QAction("Add Bookmark", self)
        add_bookmark_action.triggered.connect(self.pin_current_folder)
        bookmarks_menu.addAction(add_bookmark_action)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def create_file(self):
        file_name, ok = QInputDialog.getText(self, "Create File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(self.current_path, file_name)
            try:
                with open(file_path, "w") as f:
                    pass
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {e}")

    def create_directory(self):
        dir_name, ok = QInputDialog.getText(self, "Create Directory", "Enter directory name:")
        if ok and dir_name:
            dir_path = os.path.join(self.current_path, dir_name)
            try:
                os.mkdir(dir_path)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create directory: {e}")

    def delete_item(self, index=None):
        if index is None:
            index = self.list_view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            reply = QMessageBox.question(
                self, "Delete", f"Are you sure you want to delete {path}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate_to_history()

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.navigate_to_history()

    def go_home(self):
        self.list_view.setRootIndex(self.model.index(QDir.homePath()))
        self.add_to_history(QDir.homePath())

    def refresh(self):
        self.list_view.setRootIndex(self.model.index(self.current_path))

    def add_to_history(self, path):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(path)
        self.history_index += 1

    def navigate_to_history(self):
        path = self.history[self.history_index]
        self.list_view.setRootIndex(self.model.index(path))
        self.path_edit.setText(path)

    def toggle_hidden_files(self, checked):
        if checked:
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden)
        else:
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)

    def show_context_menu(self, position):
        index = self.list_view.indexAt(position)
        menu = QMenu()

        if index.isValid():
            path = self.model.filePath(index)
            if os.path.isdir(path):
                open_action = menu.addAction(QIcon.fromTheme("folder-open"), "Open")
                open_with_action = menu.addAction(QIcon.fromTheme("system-run"), "Open With...")
                rename_action = menu.addAction(QIcon.fromTheme("edit-rename"), "Rename")
                delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Delete")
                pin_action = menu.addAction(QIcon.fromTheme("bookmark-new"), "Pin")

                open_action.triggered.connect(lambda: self.on_item_double_clicked(index))
                open_with_action.triggered.connect(lambda: self.open_with(path))
                rename_action.triggered.connect(lambda: self.rename_item(index))
                delete_action.triggered.connect(lambda: self.delete_item(index))
                pin_action.triggered.connect(lambda: self.pin_folder(path))
            else:
                open_action = menu.addAction(QIcon.fromTheme("document-open"), "Open")
                open_with_action = menu.addAction(QIcon.fromTheme("system-run"), "Open With...")
                rename_action = menu.addAction(QIcon.fromTheme("edit-rename"), "Rename")
                delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Delete")

                open_action.triggered.connect(lambda: self.open_file(path))
                open_with_action.triggered.connect(lambda: self.open_with(path))
                rename_action.triggered.connect(lambda: self.rename_item(index))
                delete_action.triggered.connect(lambda: self.delete_item(index))
        else:
            create_file_action = menu.addAction(QIcon.fromTheme("document-new"), "Create File")
            create_dir_action = menu.addAction(QIcon.fromTheme("folder-new"), "Create Directory")
            open_terminal_action = menu.addAction(QIcon.fromTheme("utilities-terminal"), "Open Terminal Here")

            create_file_action.triggered.connect(self.create_file)
            create_dir_action.triggered.connect(self.create_directory)
            open_terminal_action.triggered.connect(self.open_terminal)

        menu.exec_(self.list_view.mapToGlobal(position))

    def open_terminal(self):
        try:
            if sys.platform == "win32":
                subprocess.Popen(["start", "cmd"], shell=True, cwd=self.current_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Terminal", self.current_path])
            else:
                subprocess.Popen(["xfce4-terminal", "--working-directory", self.current_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open terminal: {e}")

    def show_sidebar_context_menu(self, position):
        item = self.sidebar_widget.itemAt(position)
        if item:
            path = item.data(Qt.UserRole)
            menu = QMenu()

            if path in self.pinned_folders:
                unpin_action = menu.addAction(QIcon.fromTheme("bookmark-remove"), "Unpin")
                unpin_action.triggered.connect(lambda: self.unpin_folder(path))

            menu.exec_(self.sidebar_widget.mapToGlobal(position))

    def unpin_folder(self, path):
        if path in self.pinned_folders:
            self.pinned_folders.remove(path)
            self.update_sidebar()
            self.save_pinned_folders()

    def open_with(self, path):
        program, ok = QInputDialog.getText(self, "Open With", "Enter the program to open the file:")
        if ok and program:
            try:
                subprocess.Popen([program, path])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def rename_item(self, index):
        old_path = self.model.filePath(index)
        new_name, ok = QInputDialog.getText(
            self, "Rename", "Enter new name:", text=os.path.basename(old_path)
        )
        if ok and new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                destination = self.current_path
                try:
                    os.rename(file_path, os.path.join(destination, os.path.basename(file_path)))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to move file: {e}")

    def show_about_dialog(self):
        about_text = """
        <h2>Aldernys File Manager</h2>
        <p>Version alpha 1.2</p>
        <p>A file manager inspired by classic KDE 3.0 applications</p>
        <p>Part of the AMNY Project</p>
        <p>License: GNU GPL 3.0</p>
        """
        QMessageBox.about(self, "About Aldernys", about_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    file_manager = FileManager()
    file_manager.show()
    sys.exit(app.exec_())
