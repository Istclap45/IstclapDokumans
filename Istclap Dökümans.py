import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QLabel, QTextEdit, QFileDialog, QToolBar, QAction, QInputDialog, QMessageBox
)
from PyQt5.QtGui import QIcon, QTextCursor, QPixmap
from PyQt5.QtCore import Qt

DB_FILE = "database.db"

# --- Veritabanı ---
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                content TEXT,
                images TEXT
            )
        ''')
        conn.commit()

def save_document(title, content, images):
    images_str = ";".join(images)
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO documents (title, content, images)
            VALUES (?, ?, ?)
        ''', (title, content, images_str))
        conn.commit()

def load_document(title):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('SELECT content, images FROM documents WHERE title = ?', (title,))
        row = c.fetchone()
        if row:
            content, images = row
            images_list = images.split(";") if images else []
            return content, images_list
        else:
            return "", []

def list_documents():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('SELECT title FROM documents')
        return [row[0] for row in c.fetchall()]

def delete_document(title):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM documents WHERE title = ?', (title,))
        conn.commit()

# --- Döküman Editörü Penceresi ---
class DocumentEditor(QMainWindow):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Istclap Dökümans - {title}")
        self.title = title
        self.images = []
        self.init_ui()
        self.load_content()

    def init_ui(self):
        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        save_action = QAction("Kaydet", self)
        save_action.triggered.connect(self.save_content)
        toolbar.addAction(save_action)

        add_image_action = QAction("Resim Ekle", self)
        add_image_action.triggered.connect(self.add_image)
        toolbar.addAction(add_image_action)

        close_action = QAction("Kaydet ve Çık", self)
        close_action.triggered.connect(self.save_and_close)
        toolbar.addAction(close_action)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #eeeeee;
                font: 12pt "Arial";
            }
            QToolBar {
                background-color: #2c2c2c;
            }
            QPushButton {
                background-color: #2c2c2c;
                color: #eeeeee;
                padding: 6px;
            }
        """)

    def load_content(self):
        content, images = load_document(self.title)
        self.text_edit.setPlainText(content)
        self.images = images
        cursor = self.text_edit.textCursor()
        for img_path in self.images:
            if os.path.exists(img_path):
                cursor.insertImage(img_path)

    def save_content(self):
        text = self.text_edit.toPlainText()
        save_document(self.title, text, self.images)
        QMessageBox.information(self, "Istclap Dökümans", "Döküman kaydedildi!")

    def add_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Resim Seç", "", "Images (*.png *.jpg *.bmp)")
        if fname:
            self.images.append(fname)
            cursor = self.text_edit.textCursor()
            cursor.insertImage(fname)

    def save_and_close(self):
        self.save_content()
        self.close()

# --- Ana Menü ---
class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Istclap Dökümans - Ana Menü")
        self.init_ui()
        self.refresh_list()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        title = QLabel("📄 Istclap Dökümans")
        title.setStyleSheet("font-size: 20pt; color: #eeeeee;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.doc_list = QListWidget()
        self.doc_list.setStyleSheet("background-color: #1e1e1e; color: #eeeeee;")
        layout.addWidget(self.doc_list)

        btn_new = QPushButton("Yeni Döküman")
        btn_new.clicked.connect(self.new_document)
        layout.addWidget(btn_new)

        btn_open = QPushButton("Seçili Dökümanı Aç")
        btn_open.clicked.connect(self.open_document)
        layout.addWidget(btn_open)

        btn_delete = QPushButton("Seçili Dökümanı Sil")
        btn_delete.clicked.connect(self.delete_document)
        layout.addWidget(btn_delete)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QPushButton {
                background-color: #2c2c2c;
                color: #eeeeee;
                padding: 6px;
                font-size: 10pt;
            }
        """)

    def refresh_list(self):
        self.doc_list.clear()
        docs = list_documents()
        self.doc_list.addItems(docs)

    def new_document(self):
        text, ok = QInputDialog.getText(self, "Yeni Döküman", "Döküman Adı:")
        if ok and text:
            save_document(text, "", [])
            self.refresh_list()
            self.open_editor(text)

    def open_document(self):
        selected = self.doc_list.currentItem()
        if selected:
            self.open_editor(selected.text())

    def open_editor(self, title):
        self.editor = DocumentEditor(title)
        self.editor.show()

    def delete_document(self):
        selected = self.doc_list.currentItem()
        if selected:
            confirm = QMessageBox.question(
                self, "Sil", f"{selected.text()} dökümanını silmek istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                delete_document(selected.text())
                self.refresh_list()

# --- Ana Uygulama ---
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainMenu()
    window.show()
    sys.exit(app.exec_())
