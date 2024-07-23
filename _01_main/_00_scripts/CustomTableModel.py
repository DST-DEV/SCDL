import sys
import pandas as pd
import PyQt6.QtWidgets as QTW
import PyQt6.QtCore as QTC
import PyQt6.QtGui as QTG
from abc import ABC, abstractmethod

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
        super().__init__()
        # super(CustomTableModel, self).__init__()
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
        
        if role == QTC.Qt.ItemDataRole.DisplayRole or role == QTC.Qt.ItemDataRole.EditRole:
            if index.column() == self.columnCount()-1:
                return "Yes" if self._data.iloc[index.row(), index.column()] == True else "No"
            else:
                return str(self._data.iloc[index.row(), index.column()])
        elif role == QTC.Qt.ItemDataRole.CheckStateRole and index.column() == self.columnCount()-1:
            return QTC.Qt.CheckState.Checked \
                    if self._data.iloc[index.row(), index.column()] \
                    else QTC.Qt.CheckState.Unchecked
            
        
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
        if orientation == QTC.Qt.Orientation.Horizontal and role == QTC.Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]
        return None

    def setData(self, index, value, role=QTC.Qt.ItemDataRole.EditRole):
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
        
        if not index.isValid():
            return False
        
        if role == QTC.Qt.ItemDataRole.EditRole:
            if index.column() == self.columnCount()-1:
                value = True if value in ["Yes", "Y", "y"] else False
            
            self._data.iat[index.row(),index.column()] = value
            self.dataChanged.emit(index, index, [QTC.Qt.ItemDataRole.EditRole])
            return True
        if role == QTC.Qt.ItemDataRole.CheckStateRole and index.column() == self.columnCount()-1:
            self._data.iat[index.row(),index.column()] = (value == QTC.Qt.CheckState.Checked)
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
            return QTC.Qt.ItemFlag.NoItemFlags
        
        if index.column() == self.columnCount()-1:
            # return QTC.Qt.ItemFlag.ItemIsEnabled | QTC.Qt.ItemFlag.ItemIsUserCheckable
            return QTC.Qt.ItemFlag.ItemIsSelectable | QTC.Qt.ItemFlag.ItemIsEnabled \
                | QTC.Qt.ItemFlag.ItemIsUserCheckable | QTC.Qt.ItemFlag.ItemIsEditable
        
            # return QTC.Qt.ItemFlag.ItemIsEnabled | QTC.Qt.ItemFlag.ItemIsUserCheckable
        else:
            return super().flags(index) | QTC.Qt.ItemFlag.ItemIsEditable

    
    def change_data(self, data, insert_checkboxes = True):
        """Change the data of the table
        
        Parameters:
        data: pandas Dataframe with the new data
            
        Returns:
        None    
        """
        
        self.beginResetModel()
        if insert_checkboxes and "include" not in data.columns:
            data.insert(data.shape[1], "include", True)
        self._data = data.copy(deep=True)
        self.endResetModel()
 

#%%

class CustomTableView(QTW.QTableView):
    selectionIndexChanged = QTC.pyqtSignal(QTC.QModelIndex)

    def __init__(self):
        super().__init__()
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        indexes = self.selectionModel().selectedIndexes()
        if indexes:
            self.selectionIndexChanged.emit(indexes[0])

#%% Class for implementation of Checkboxes (apparently needed to make them user-checkable)

class CheckBoxDelegate(QTW.QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() == index.model().columnCount() - 1:
            value = index.model().data(index, QTC.Qt.ItemDataRole.CheckStateRole)
            check_box_style_option = QTW.QStyleOptionButton()
            check_box_style_option.state |= QTW.QStyle.StateFlag.State_Enabled
            if value == QTC.Qt.CheckState.Checked:
                check_box_style_option.state |= QTW.QStyle.StateFlag.State_On
            else:
                check_box_style_option.state |= QTW.QStyle.StateFlag.State_Off

            check_box_rect = QTW.QApplication.style().subElementRect(
                QTW.QStyle.SubElement.SE_CheckBoxIndicator, 
                check_box_style_option, 
                None)
            check_box_style_option.rect = check_box_rect
            check_box_style_option.rect.moveCenter(option.rect.center())

            QTW.QApplication.style().drawControl(QTW.QStyle.ControlElement.CE_CheckBox, 
                                                 check_box_style_option, 
                                                 painter)
        else:
            super().paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if index.column() == model.columnCount() - 1 \
            and event.type() == QTC.QEvent.Type.MouseButtonRelease:
                
            if event.button() == QTC.Qt.MouseButton.LeftButton:
                model.setData(index, QTC.Qt.CheckState.Checked
                              if model.data(index,QTC.Qt.ItemDataRole.CheckStateRole) \
                                  == QTC.Qt.CheckState.Unchecked 
                              else QTC.Qt.CheckState.Unchecked, 
                                   QTC.Qt.ItemDataRole.CheckStateRole)
                return True
        return super().editorEvent(event, model, option, index)


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
        
        # self.view = CustomTableView()
        self.view = QTW.QTableView()
        self.pm = CustomTableModel(self.df1)
        self.view.setModel(self.pm)
        # self.pm._data = self.df1
        
        delegate = CheckBoxDelegate(self.view)
        self.view.setItemDelegate(delegate)
        
        self.btn1 = QTW.QPushButton("Add row")
        self.btn1.clicked.connect(self.add_row)
        
        self.btn2 = QTW.QPushButton("Del rows")
        self.btn2.clicked.connect(self.del_rows)
        
        self.btn3 = QTW.QPushButton("Print")
        self.btn3.clicked.connect(self.print_df)
        
        #Connect a change in the selction of the table to a function
        #Note: currently this function is just a placeholder. in the future this 
        #should trigger the content of another table to change
        self.selectionModel = self.view.selectionModel() 
        self.selectionModel.selectionChanged.connect(self.print_change)

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
    
    def print_change(self, selected, deselected):
        if len(selected.indexes())>0:
            row = selected.indexes()[0].row()
            print(row)


#%%

class TblBlueprint():
    def del_rows(self, view, TableWidget):
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()), reverse=True)
        if rows:
            for row in rows:
                TableWidget.removeRow(row)
    
    def add_rows(self, view, TableWidget):
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()))
        if rows and rows[0]<TableWidget.rowCount():
            TableWidget.insertRows(rows[0]+1, 1)
        else:
            TableWidget.insertRows(TableWidget.rowCount(), 1)
    
    # @abstractmethod
    # def print_change(self, selected, deselected):
    #     if len(selected.indexes())>0:
    #         row = selected.indexes()[0].row()
    #         print(row)




#%%

if __name__ == '__main__':

    app = QTW.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())