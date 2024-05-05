# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 09:07:55 2024

@author: davis

Sources
-  https://learndataanalysis.org/create-a-pandas-dataframe-editor-with-pyqt5/
-  https://stackoverflow.com/questions/41192293/make-qtableview-editable-when-model-is-pandas-dataframe?rq=3
"""

import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QTableView
import PyQt5.QtWidgets as QTW
import PyQt5.QtCore as QTC
import PyQt5.QtGui as QTG

df = pd.DataFrame({'a': ['Mary', 'Jim', 'John'],
                   'b': [100.1, 200.2, 300.3],
                   'c': ['a', 'b', 'c']})

class PandasModel(QTC.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """

    def __init__(self, data, parent=None):
        QTC.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=QTC.Qt.DisplayRole):
        if index.isValid():
            if role == QTC.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QTC.Qt.Horizontal and role == QTC.Qt.DisplayRole:
            return self._data.columns[col]
        return None

    def setData(self, index, value, role):
        # if not index.isValid():
        #     return False
        # if role != QTC.Qt.EditRole:
        #     return False
        # row = index.row()
        # if row < 0 or row >= len(self._data.values):
        #     return False
        # column = index.column()
        # if column < 0 or column >= self._data.columns.size:
        #     return False
        # self._data.values[row][column] = value
        # self.dataChanged.emit(index, index)
        # return True
        
        if index.isValid():
            if role == QTC.Qt.EditRole:
                if index.column() == 1:
                    value = int(value)
                self._data.iat[index.row(),index.column()] = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def flags(self, index):
        flags = super(self.__class__,self).flags(index)
        flags |= QTC.Qt.ItemIsEditable
        flags |= QTC.Qt.ItemIsSelectable
        flags |= QTC.Qt.ItemIsEnabled
        flags |= QTC.Qt.ItemIsDragEnabled
        flags |= QTC.Qt.ItemIsDropEnabled
        return flags
    

class MainWindow(QTW.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set geometry and window color
        self.setGeometry(100, 100, 1000, 500)
        #self.setStyleSheet("background-color: #000000;")
        
        self.cw = QTW.QWidget()
        self.setCentralWidget(self.cw)
        self.main_layout = QTW.QVBoxLayout(self)        
        
        self.df1 = pd.DataFrame({'a': ['Mary', 'Jim', 'John'],
                           'b': [100.1, 200.2, 300.3],
                           'c': ['a', 'b', 'c']})
        self.df2 = pd.DataFrame({"col1":[0,0,0,0], "col2":[1,2,3,4]})
        
        self.view = QTableView()
        self.pm = PandasModel(data=self.df1)
        self.view.setModel(self.pm)
        
        self.btn = QTW.QPushButton("Change")
        self.btn.clicked.connect(self.changedf)

        self.main_layout.addWidget(self.view)
        self.main_layout.addWidget(self.btn)
        
        #Set the main Layout
        self.cw.setLayout(self.main_layout)
    
    def changedf(self):
        # self.pm.beginResetModel()
        # self.pm._data = self.df2
        # self.pm.endResetModel()
        # self.view.setModel(self.pm)
        
        print(self.pm._data)
        
if __name__ == '__main__':

    app = QTW.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     model = PandasModel(df)
#     view = QTableView()
#     view.setModel(model)
#     view.resize(800, 600)
#     view.show()
#     sys.exit(app.exec_())