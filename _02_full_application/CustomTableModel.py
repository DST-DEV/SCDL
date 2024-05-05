import sys
import pandas as pd
import PyQt5.QtWidgets as QTW
import PyQt5.QtCore as QTC
import PyQt5.QtGui as QTG



class PandasTableModel (QTC.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe and make it editable
    
    Usage example:
        
        df = pd.DataFrame({'a': ['Mary', 'Jim', 'John'],
                           'b': [100.1, 200.2, 300.3],
                           'c': ['a', 'b', 'c']})
        
        self.tableview = QTableView()
        self.PTM = PandasTableModel(data = self.df)
        self.view.setModel(self.PTM)
    """

    def __init__(self, data, parent=None):
        QTC.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=QTC.Qt.DisplayRole):
        """Returns data at index
        
        Parameters:
        index: QModelIndex of which data should be returned
        role: No idea what this is used for
            
        Returns:
        Value at index in the form of a string or None if the index is not valid
        """
        
        if index.isValid():
            if role == QTC.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role):
        """Returns column name at column index (col)
        
        Parameters:
        index: index (integer) of column for which the name should be returned
        orientation: No idea what this is used for
        role: No idea what this is used for
            
        Returns:
        Name of column with the index "col" or None if orientation is not 
          horizontal or role is not DisplayRole
        """
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
    
    def insertRows(self, row, count):
        if row <= self.rowCount():
            self.beginInsertRows(QTC.QModelIndex(), 
                                 row, 
                                 row+count-1)
            
            new_rows = pd.DataFrame(columns=self._data.columns,
                                    data = [[""]*self.columnCount()]*count,
                                    index=[row-1+i/100 for i in range(count)])
            self._data = pd.concat([self._data, new_rows])
            self._data = self._data.sort_index().reset_index(drop=True)
            
            self.endInsertRows()
            return True
        return False
    
    
    def flags(self, index):
        return super().flags(index) | QTC.Qt.ItemIsEditable
        
        #Alternative code:
        # flags = super(self.__class__,self).flags(index)
        # flags |= QTC.Qt.ItemIsEditable
        # flags |= QTC.Qt.ItemIsSelectable
        # flags |= QTC.Qt.ItemIsEnabled
        # flags |= QTC.Qt.ItemIsDragEnabled
        # flags |= QTC.Qt.ItemIsDropEnabled
        # return flags
    
    def change_data(self, data):
        """Change the data of the table
        
        Parameters:
        data: pandas Dataframe with the new data
            
        Returns:
        None    
        """
        
        self.beginResetModel()
        self._data = data
        self.endResetModel()
    
#%%

# import sys
# from PyQt5.QtWidgets import (QApplication, QWidget, QTableView, QVBoxLayout)
# from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex

# class TableModel(QAbstractTableModel):
# 	def __init__(self, data):
# 		super().__init__()
# 		self._data = data

# 	def rowCount(self, parent=QModelIndex()):
# 		return self._data.shape[0]

# 	def columnCount(self, parent=QModelIndex()):
# 		return self._data.shape[1]

# 	def data(self, index, role=Qt.DisplayRole):
# 		# display data
# 		if role == Qt.DisplayRole:
# 			print('Display role:', index.row(), index.column())
# 			try:
# 				return self._data[index.row()][index.column()]
# 			except IndexError:
# 				return ''

# 	def setData(self, index, value, role=Qt.EditRole):		
# 		if role in (Qt.DisplayRole, Qt.EditRole):
# 			print('Edit role:', index.row(), index.column())
# 			# if value is blank
# 			if not value:
# 				return False	
# 			self._data[index.row()][index.column()] = value
# 			self.dataChanged.emit(index, index)
# 		return True

# 	def flags(self, index):
# 		return super().flags(index) | Qt.ItemIsEditable

# class MainApp(QWidget):
# 	def __init__(self):
# 		super().__init__()
# 		self.window_width, self.window_height = 1600, 1200
# 		self.setMinimumSize(self.window_width, self.window_height)
# 		self.setStyleSheet('''
# 			QWidget {
# 				font-size: 30px;
# 			}
# 		''')		

# 		self.layout = {}
# 		self.layout['main'] = QVBoxLayout()
# 		self.setLayout(self.layout['main'])

# 		self.table = QTableView()
# 		self.layout['main'].addWidget(self.table)

# 		data_model = TableModel(data)
# 		self.table.setModel(data_model)


# if __name__ == '__main__':
# 	data = [
# 		['A1', 'A2', 'A3'],
# 		['B1', 'B2', 'B3', 'B4'],
# 		['C1', 'C2', 'C3', 'C4', 'C5']
# 	]

# 	# row count
# 	# print(len(data))

# 	# column count
# 	# print(len(max(data, key=len)))

# 	app = QApplication(sys.argv)
# 	
# 	myApp = MainApp()
# 	myApp.show()

# 	try:
# 		sys.exit(app.exec_())
# 	except SystemExit:
# 		print('Closing Window...')

#%%


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
        
        self.view = QTW.QTableView()
        self.pm = PandasTableModel(data=self.df1)
        self.view.setModel(self.pm)
        
        self.btn1 = QTW.QPushButton("Add row")
        self.btn1.clicked.connect(self.add_row)
        
        self.btn2 = QTW.QPushButton("Print")
        self.btn2.clicked.connect(self.print_df)

        self.main_layout.addWidget(self.view)
        self.main_layout.addWidget(self.btn1)
        self.main_layout.addWidget(self.btn2)
        
        #Set the main Layout
        self.cw.setLayout(self.main_layout)
    
    def print_df(self):
        print(self.pm._data)
    
    def add_row(self):
        self.pm.insertRows(self.pm.rowCount(), 1)


#%%

if __name__ == '__main__':

    app = QTW.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())