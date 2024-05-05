

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QFile
import PyQt5.QtWidgets as QTW
from UI_main_window import Ui_MainWindow

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super(MainWindow, self).__init__()
        # self.ui = Ui_MainWindow()
        # self.ui.setupUi(self)

# if __name__ == "__main__":
    # app = QApplication(sys.argv)

    # window = MainWindow()
    # window.show()

    # sys.exit(app.exec())


class MainWindow(Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # super(Ui_MainWindow, self).__init__()

        # MW = QTW.QMainWindow()
        # self.setupUi(MW)
        
        
        # # Set geometry and window color
        # self.setGeometry(100, 100, 1000, 500)
        # #self.setStyleSheet("background-color: #000000;")
        
        # self.cw = QTW.QWidget()
        # self.setCentralWidget(self.cw)
        # self.main_layout = QTW.QVBoxLayout(self)        
        
        # self.btn = QTW.QPushButton("Change")
        
        # self.main_layout.addWidget(self.btn)
        
        # #Set the main Layout
        # self.cw.setLayout(self.main_layout)
 
    
 

if __name__ == "__main__":

    
    
    app = QTW.QApplication(sys.argv)
    MW = QTW.QMainWindow()
    ui = MainWindow()
    ui.setupUi(MW)
    MW.show()
    
    # ui = MainWindow()
    # ui.show()
    # sys.exit(app.exec())

