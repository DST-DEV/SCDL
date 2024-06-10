import sys
import pandas as pd
import PyQt6.QtWidgets as QTW
import PyQt6.QtCore as QTC
import PyQt6.QtGui as QTG

class CustomTableModel (QTC.QAbstractTableModel):
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
        super(CustomTableModel, self).__init__()
        # QTC.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=QTC.Qt.ItemDataRole.DisplayRole):
        """Returns data at index
        Note: the last Column has checkboxes included automatically
        
        Parameters:
        index: QModelIndex of which data should be returned
        role: No idea what this is used for
            
        Returns:
        Value at index in the form of a string or None if the index is not valid
        """
        
        if not index.isValid():
            return QTC.QVariant()
        
        if role == QTC.Qt.ItemDataRole.DisplayRole:
            if index.column() == self.columnCount()-1:
                return "Yes" if self._data.iloc[index.row(), index.column()] == True else "No"
            else:
                return str(self._data.iloc[index.row(), index.column()])
        elif role == QTC.Qt.ItemDataRole.CheckStateRole and index.column() == self.columnCount()-1:
            return QTC.Qt.Checked if self._data.iloc[index.row(), index.column()] else QTC.Qt.Unchecked
            
        
        return QTC.QVariant()

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
        if orientation == QTC.Qt.Horizontal and role == QTC.Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]
        return None

    def setData(self, index, value, role):
        """Sets the value in the _data at the specified index (Sets the role 
        data for the item at index to value)
        
        Parameters:
        index: QModelIndex of which data should be inserted
        value: the value to insert
        role: to determine if an edit is currently being made
            
        Returns:
        bool: After making the edit, returns true if successful; otherwise 
              returns false
        
        
        """
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
        
        if not index.isValid():
            return False
        
        if role == QTC.Qt.EditRole:
            self._data.iat[index.row(),index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        if role == QTC.Qt.ItemDataRole.CheckStateRole and index.column() == self.columnCount()-1:
            self._data.iat[index.row(),index.column()] = (value == QTC.Qt.Checked)
            self.dataChanged.emit(index, index, [QTC.Qt.ItemDataRole.CheckStateRole])
            return True
        
        return False

    
    def insertRows(self, row, count, parent=QTC.QModelIndex()):
        if row <= self.rowCount():
            self.beginInsertRows(parent, 
                                 row, 
                                 row+count-1)
            
            new_rows = pd.DataFrame(columns=self._data.columns,
                                    data = [[""]*(self.columnCount()-1) + [False]]*count,
                                    index=[row-1+i/100 for i in range(count)])
            self._data = pd.concat([self._data, new_rows])
            self._data = self._data.sort_index().reset_index(drop=True)
            
            self.endInsertRows()
            return True
        return False
    
    def removeRow(self, row, parent=QTC.QModelIndex()):
        if 0 <= row < self.rowCount(None):
            self.beginRemoveRows(parent, row, row)
            self._data.drop(index=row, inplace=True)
            self.endRemoveRows()
            return True
        return False
    
    def flags(self, index):
        if not index.isValid():
            return QTC.Qt.NoItemFlags
        
        if index.column() == self.columnCount()-1:
            return QTC.Qt.ItemIsEnabled | QTC.Qt.ItemIsUserCheckable
        else:
            return super().flags(index) | QTC.Qt.ItemIsEditable

    
    def change_data(self, data, insert_checkboxes = True):
        """Change the data of the table
        
        Parameters:
        data: pandas Dataframe with the new data
            
        Returns:
        None    
        """
        
        self.beginResetModel()
        if insert_checkboxes and "include" not in data.columns:
            data = pd.concat([data, 
                              pd.DataFrame({"include":
                                            [False]*data.shape[0]})
                              ])
        self._data = data.copy(deep=True)
        self.endResetModel()
 

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
                           'c': [False, False, False]})
        self.df2 = pd.DataFrame({"col1":[0,0,0,0], "col2":[1,2,3,4]})
        
        
        self.view = QTW.QTableView()
        self.pm = CustomTableModel(self.df1)
        self.view.setModel(self.pm)
        # self.pm._data = self.df1
        
        self.btn1 = QTW.QPushButton("Add row")
        self.btn1.clicked.connect(self.add_row)
        
        self.btn2 = QTW.QPushButton("Del rows")
        self.btn2.clicked.connect(self.del_rows)
        
        self.btn3 = QTW.QPushButton("Print")
        self.btn3.clicked.connect(self.print_df)

        self.main_layout.addWidget(self.view)
        self.main_layout.addWidget(self.btn1)
        self.main_layout.addWidget(self.btn2)
        self.main_layout.addWidget(self.btn3)
        
        #Set the main Layout
        self.cw.setLayout(self.main_layout)
    
    def print_df(self):
        print(self.pm._data)
    
    def del_rows(self):
        self.dr(self.view, self.pm)
        
    def add_row(self):
        self.ar(self.view, self.pm)
    
    
    def dr(self, view, TableWidget):
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()), reverse=True)
        if rows:
            for row in rows:
                TableWidget.removeRow(row)
    
    def ar(self, view, TableWidget):
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()))
        if rows and rows[0]<TableWidget.rowCount():
            TableWidget.insertRows(rows[0]+1, 1)
        else:
            TableWidget.insertRows(TableWidget.rowCount(), 1)
    
    # def del_rows(self):
    #     rows = sorted(set(index.row() for index in
    #                   self.view.selectedIndexes()), reverse=True)
    #     if rows:
    #         for row in rows:
    #             self.pm.removeRow(row)
    
    # def add_row(self):
    #     rows = sorted(set(index.row() for index in
    #                   self.view.selectedIndexes()))
    #     if rows and rows[0]<self.pm.rowCount():
    #         self.pm.insertRows(rows[0]+1, 1)
    #     else:
    #         self.pm.insertRows(self.pm.rowCount(), 1)

#%%

if __name__ == '__main__':

    app = QTW.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())