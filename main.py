import sys
import os
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer
from view.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
