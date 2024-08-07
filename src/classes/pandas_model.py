from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt5.QtWidgets import QMessageBox
import pandas as pd
from pathlib import Path

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        """Create object to hold dataframe info and interact with view"""
        QAbstractTableModel.__init__(self)
        # set up variables
        self._data = data
        self.dirty = False
        self.editable = False

    def rowCount(self, parent=None):
        """return amount of rows"""
        return self._data.shape[0]

    def columnCount(self, parent = None):
        """return amount of columns"""
        return self._data.shape[1]

    def setData(self, index, value, role):
        """Update a cell"""
        if role == Qt.EditRole:
            self._data.iloc[index.row(),index.column()] = value
            self.dirty = True
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Set up headers and their attributes (colors, fonts, etc)"""
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                try:
                    return self._data.columns.tolist()[section]
                except (IndexError,):
                    return QVariant()
        elif orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                try:
                    return self._data.index.tolist()[section]
                except (IndexError,):
                    return QVariant()
        return QVariant()
    
    def flags(self, index):
        "Set data to editable or view only"
        # if editable from main_window is false or cell is in a column with predefined values
        if self.editable == False or self.getColumnNames()[index.column()] in ['Category', 'Priority', 'Status']:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        # otherwise, data can be edited
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
    
    def data(self, index, role=Qt.DisplayRole):
        """Return a cell's value as str"""
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                value = self._data.iloc[index.row(), index.column()]
                return str(value)
            
    def getRow(self, index):
        """Return a row as a string"""
        value = self._data.iloc[index]
        return str(value)
    
    def getRowObj(self, index):
        """Return row as an object"""
        return self._data.iloc[index]
    
    def getItem(self, row, col):
        """Return a cell as a string"""
        value=self._data.iloc[row, col]
        return str(value)

    def toDataFrame(self):
        """Return data as a dataframe"""
        return self._data.copy()
    
    def getColumnNames(self):
        """Return the column names as a list"""
        return self._data.columns.values.tolist()
    
    def saveToJson(self):
        """Save current model data to json"""
        from src.run import resource_path
        self._data.to_json(resource_path(Path('data/task_data.json')))
        self.dirty = False

    def makeViewable(self):
        """Change editable to False"""
        self.editable = False
    
    def makeEditable(self):
        """Change editable to True"""
        self.editable = True
    
    def clearAllData(self):
        """Drop all rows"""
        self._data = self._data.drop(self._data.index)
        self.headerDataChanged.emit(Qt.Horizontal, 0, self.columnCount())
        self.layoutChanged.emit()
    
    def addRows(self, df):
        """Add rows to the end of the dataframe"""
        # check for validity
        if not isinstance(df, pd.DataFrame) or df.shape[1] != self._data.shape[1]:
            return False
        
        # Start inserting rows
        orig_rows = self.rowCount()
        self.beginInsertRows(QModelIndex(), orig_rows, orig_rows+df.shape[0]-1)  # Notify the model about the upcoming row insertion

        # Append the rows
        try:
            self._data = self._data._append(df, ignore_index=True)
            self._data = self._data.reset_index(drop=True)
        except Exception as e:
            QMessageBox.critical(None, 'Error Appending Rows', str(e))
            return

        # End inserting rows
        self.endInsertRows()  # Notify the model that the rows have been inserted

        # mark as dirty
        self.dirty = True

        # return successful
        return True
    
    def getIndex(self):
        """Return the data index information"""
        return self._data.index
    
    def isDirty(self):
        """Return if dirty is True or False"""
        return self.dirty
