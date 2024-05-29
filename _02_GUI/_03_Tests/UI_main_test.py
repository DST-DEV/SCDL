import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QFile
import PyQt6.QtWidgets as QTW
from Main import Ui_MainWindow

class MainWindow(QTW.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())















































# class MainWindow(Ui_MainWindow):
#     def __init__(self):
#         # super().__init__()
#         super(Ui_MainWindow, self).__init__()

#         MW = QTW.QMainWindow()
#         self.setupUi(MW)
        
        
#         # # Set geometry and window color
#         # self.setGeometry(100, 100, 1000, 500)
#         # #self.setStyleSheet("background-color: #000000;")
        
#         # self.cw = QTW.QWidget()
#         # self.setCentralWidget(self.cw)
#         # self.main_layout = QTW.QVBoxLayout(self)        
        
#         # self.btn = QTW.QPushButton("Change")
        
#         # self.main_layout.addWidget(self.btn)
        
#         # #Set the main Layout
#         # self.cw.setLayout(self.main_layout)
 
    
 

# if __name__ == "__main__":
#     app = QTW.QApplication(sys.argv)
#     MainWindow = QTW.QMainWindow()
#     ui = Ui_MainWindow()
#     ui.setupUi(MainWindow)
#     MainWindow.show()
#     sys.exit(app.exec())
    
    

