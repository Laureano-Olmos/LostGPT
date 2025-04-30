import sys
import os
import json
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QTabWidget, QShortcut, QLabel, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QKeySequence, QIcon, QMouseEvent

FAVORITOS_PATH = os.path.abspath("assets/favoritos.json")

FAVORITOS_INICIALES = [
    {"nombre": "YouTube", "url": "https://www.youtube.com", "icono": "🌐"},
    {"nombre": "Twitch", "url": "https://www.twitch.tv", "icono": "🌐"},
    {"nombre": "Kick", "url": "https://www.kick.com", "icono": "🌐"},
    {"nombre": "Optijuegos", "url": "https://www.optijuegos.net", "icono": "🌐"},
    {"nombre": "ChatGPT", "url": "https://chat.openai.com", "icono": "🌐"},
]

class BotonFavorito(QPushButton):
    def __init__(self, favorito, parent=None):
        super().__init__(f"{favorito['icono']} {favorito['nombre']}", parent)
        self.favorito = favorito
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            mimeData = QMimeData()
            mimeData.setText(json.dumps(self.favorito))

            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec_(Qt.MoveAction)
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        favorito_arrastrado = json.loads(event.mimeData().text())
        parent = self.parentWidget().parent()
        parent.reordenar_favoritos(favorito_arrastrado, self.favorito)
        event.acceptProposedAction()

class Navegador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LostGPT")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #121212; color: white;")

        self.pagina_inicio_url = QUrl.fromLocalFile(os.path.abspath("assets/inicio.html"))

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.cerrar_pestana)
        self.tabs.currentChanged.connect(self.actualizar_barra_direccion)

        self.barra_direccion = QLineEdit()
        self.barra_direccion.setPlaceholderText("Buscar o ingresar URL")
        self.barra_direccion.returnPressed.connect(self.cargar_url_actual)
        self.boton_agregar_favorito = QPushButton("★")
        self.boton_agregar_favorito.clicked.connect(self.agregar_a_favoritos)

        barra_url_layout = QHBoxLayout()
        barra_url_layout.addWidget(self.barra_direccion)
        barra_url_layout.addWidget(self.boton_agregar_favorito)

        self.boton_retroceder = QPushButton("←")
        self.boton_retroceder.clicked.connect(self.retroceder_pagina)

        self.boton_recargar = QPushButton("⟳")
        self.boton_recargar.clicked.connect(self.recargar_pagina)

        self.boton_inicio = QPushButton("🏠")
        self.boton_inicio.clicked.connect(self.ir_a_inicio)

        self.boton_historial = QPushButton("🕘 Historial")

        for boton in (self.boton_retroceder, self.boton_recargar, self.boton_inicio, self.boton_historial):
            boton.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                }
            """)

        self.barra_navegacion = QHBoxLayout()
        self.barra_navegacion.addWidget(self.boton_retroceder)
        self.barra_navegacion.addWidget(self.boton_recargar)
        self.barra_navegacion.addWidget(self.boton_inicio)
        self.barra_navegacion.addLayout(barra_url_layout)
        self.barra_navegacion.addWidget(self.boton_historial)

        self.barra_favoritos = QWidget()
        self.barra_favoritos_layout = QHBoxLayout()
        self.barra_favoritos.setLayout(self.barra_favoritos_layout)

        self.historial = []
        self.favoritos = []
        self.cargar_favoritos()
        self.actualizar_barra_favoritos()

        self.barra_titulo = QLabel("  LostGPT")
        self.barra_titulo.setStyleSheet("background-color: black; color: white; font-size: 16px; padding: 8px;")

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.barra_titulo)
        self.main_layout.addLayout(self.barra_navegacion)
        self.main_layout.addWidget(self.barra_favoritos)
        self.main_layout.addWidget(self.tabs)

        contenedor = QWidget()
        contenedor.setLayout(self.main_layout)
        self.setCentralWidget(contenedor)

        QShortcut(QKeySequence("Ctrl+N"), self, self.nueva_pestana)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.siguiente_pestana)
        QShortcut(QKeySequence("F5"), self, self.recargar_pagina)

        self.nueva_pestana()

    def nueva_pestana(self):
        navegador = QWebEngineView()
        navegador.load(self.pagina_inicio_url)
        navegador.urlChanged.connect(self.actualizar_barra_direccion)
        indice = self.tabs.addTab(navegador, "Nueva Pestaña")
        self.tabs.setCurrentIndex(indice)

    def cerrar_pestana(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def cargar_url_actual(self):
        url = self.barra_direccion.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://www.google.com/search?q=' + url
        navegador = self.tabs.currentWidget()
        navegador.load(QUrl(url))
        self.historial.append(url)

    def actualizar_barra_direccion(self, index_or_url):
        navegador = self.tabs.currentWidget()
        if isinstance(index_or_url, int):
            url = navegador.url()
        else:
            url = index_or_url
        if url == self.pagina_inicio_url:
            self.barra_direccion.setText("")
        else:
            self.barra_direccion.setText(url.toString())
        self.tabs.setTabText(self.tabs.currentIndex(), navegador.title())

    def recargar_pagina(self):
        navegador = self.tabs.currentWidget()
        navegador.reload()

    def retroceder_pagina(self):
        navegador = self.tabs.currentWidget()
        if navegador.history().canGoBack():
            navegador.back()

    def ir_a_inicio(self):
        navegador = self.tabs.currentWidget()
        navegador.load(self.pagina_inicio_url)

    def agregar_a_favoritos(self):
        url = self.barra_direccion.text()
        if not url:
            return
        nombre = self.tabs.tabText(self.tabs.currentIndex()) or url
        favorito = {"nombre": nombre, "url": url, "icono": "🌐"}

        reply = QMessageBox.question(self, "Agregar a Favoritos",
            f"¿Deseas agregar '{nombre}' a tus favoritos?",
            QMessageBox.Yes | QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.favoritos.append(favorito)
            self.guardar_favoritos()
            self.actualizar_barra_favoritos()

    def actualizar_barra_favoritos(self):
        for i in reversed(range(self.barra_favoritos_layout.count())):
            widget = self.barra_favoritos_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for favorito in self.favoritos:
            boton = BotonFavorito(favorito, parent=self)
            boton.clicked.connect(lambda _, url=favorito['url']: self.tabs.currentWidget().load(QUrl(url)))
            boton.setContextMenuPolicy(Qt.CustomContextMenu)
            boton.customContextMenuRequested.connect(lambda pos, f=favorito: self.confirmar_eliminar_favorito(f))
            self.barra_favoritos_layout.addWidget(boton)
            
    def reordenar_favoritos(self, fuente, destino):
        if fuente == destino:
            return
        self.favoritos.remove(fuente)
        index = self.favoritos.index(destino)
        self.favoritos.insert(index, fuente)
        self.guardar_favoritos()
        self.actualizar_barra_favoritos()


    def confirmar_eliminar_favorito(self, favorito):
        reply = QMessageBox.question(self, "Eliminar Favorito",
            f"¿Estás seguro de eliminar '{favorito['nombre']}' de tus favoritos?",
            QMessageBox.Yes | QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.favoritos.remove(favorito)
            self.guardar_favoritos()
            self.actualizar_barra_favoritos()

    def guardar_favoritos(self):
        os.makedirs(os.path.dirname(FAVORITOS_PATH), exist_ok=True)
        with open(FAVORITOS_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.favoritos, f, indent=2, ensure_ascii=False)

    def cargar_favoritos(self):
        if os.path.exists(FAVORITOS_PATH):
            with open(FAVORITOS_PATH, 'r', encoding='utf-8') as f:
                self.favoritos = json.load(f)
        else:
            self.favoritos = FAVORITOS_INICIALES.copy()
            self.guardar_favoritos()

    def siguiente_pestana(self):
        indice = (self.tabs.currentIndex() + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(indice)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.XButton1:
            self.retroceder_pagina()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = Navegador()
    ventana.show()
    sys.exit(app.exec_())
