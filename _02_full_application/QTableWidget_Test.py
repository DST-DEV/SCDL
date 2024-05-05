# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 21:32:47 2024

@author: davis
"""

import sys
import pandas as pd
import PyQt5.QtWidgets as QTW
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
import sys
import os
import numpy as np
import PyQt5.QtWidgets as QTW
import PyQt5.QtGui as QTG
import PyQt5.QtCore as QTC
import PyQt5.QtMultimedia as QTM
import PyQt5.QtMultimediaWidgets as QTMW






    
    
class MainWindow(QTW.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set geometry and window color
        self.setGeometry(100, 100, 1000, 500)
        #self.setStyleSheet("background-color: #000000;")

        df_display = QTW.QTableWidget()
        
        df = pd.DataFrame({"col1":[0,0,0,0], "col2":[1,2,3,4]})
        
        # df_display.setColumnCount(df.shape[1])
        # df.setRowCount(df.shape[0])
        df_display._data = df

        pm = PandasModel(data=df)



        mainLayout = QTW.QVBoxLayout()

        mainLayout.addWidget(pm)
        
        
        
        
        
        self.setLayout(mainLayout)
# class FloatDelegate(QItemDelegate):
#     def __init__(self, parent=None):
#         super().__init__()

#     def createEditor(self, parent, option, index):
#         editor = QLineEdit(parent)
#         editor.setValidator(QDoubleValidator())
#         return editor

# class TableWidget(QTableWidget):
#     def __init__(self, df):
#         super().__init__()
#         self.df = df
#         self.setStyleSheet('font-size: 35px;')

#         # set table dimension
#         nRows, nColumns = self.df.shape
#         self.setColumnCount(nColumns)
#         self.setRowCount(nRows)

#         self.setHorizontalHeaderLabels(('Col X', 'Col Y'))
#         self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
#         self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

#         self.setItemDelegateForColumn(1, FloatDelegate())

#         # data insertion
#         for i in range(self.rowCount()):
#             for j in range(self.columnCount()):
#                 self.setItem(i, j, QTableWidgetItem(str(self.df.iloc[i, j])))

#         self.cellChanged[int, int].connect(self.updateDF)   

#     def updateDF(self, row, column):
#         text = self.item(row, column).text()
#         self.df.iloc[row, column] = text

# class DFEditor(QWidget):
#     data = {
#         'Col X': list('ABCD'),
#         'col Y': [10, 20, 30, 40]
#     }

#     df = pd.DataFrame(data)

#     def __init__(self):
#         super().__init__()
#         self.resize(1200, 800)

#         mainLayout = QVBoxLayout()

#         self.table = TableWidget(DFEditor.df)
#         mainLayout.addWidget(self.table)

#         button_print = QPushButton('Display DF')
#         button_print.setStyleSheet('font-size: 30px')
#         button_print.clicked.connect(self.print_DF_Values)
#         mainLayout.addWidget(button_print)

#         button_export = QPushButton('Export to CSV file')
#         button_export.setStyleSheet('font-size: 30px')
#         button_export.clicked.connect(self.export_to_csv)
#         mainLayout.addWidget(button_export)     

#         self.setLayout(mainLayout)
        
#     def print_DF_Values(self):
#         print(self.table.df)

#     def export_to_csv(self):
#         self.table.df.to_csv('Data export.csv', index=False)
#         print('CSV file exported.')

if __name__ == '__main__':

    app = QTW.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())