
# imports
import os, sys, traceback

from PyQt5.QtCore import Qt, QSortFilterProxyModel, QModelIndex
from PyQt5.QtWidgets import QMainWindow, QCheckBox, QToolButton, QWidget, QHBoxLayout, QFileDialog, QVBoxLayout, QLabel, QToolBar, QMessageBox, QHeaderView, QAction, QActionGroup, QMenu, QInputDialog, QTableView, QLineEdit
from PyQt5.QtGui import QCursor, QIcon
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import json

from src.classes.pandas_model import PandasModel

class MainWindow(QMainWindow):
    def __init__(self, edit_on):
        """Build window with task table"""
        super().__init__()
        # set up window
        self.setWindowTitle("Task Tracker")
        from src.run import resource_path
        self.setWindowIcon(QIcon(resource_path(Path('data/computer.ico'))))

        # create data model and save column names
        task_data = pd.read_json(resource_path(Path('data/task_data.json')))
        self.model = PandasModel(task_data)
        self.columns = self.model.getColumnNames()

        # create proxy models (used for filtering)
        self.status_proxy = QSortFilterProxyModel()
        self.status_proxy.setSourceModel(self.model)
        self.status_proxy.setFilterKeyColumn(self.columns.index('Status'))
        self.status_proxy.setFilterFixedString('Active')
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.status_proxy)
        self.proxy.setFilterKeyColumn(-1) # set the column to filter by as all
        self.proxy.setFilterCaseSensitivity(False)

        # create view model
        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.installEventFilter(self)
        self.view.verticalHeader().hide() # don't show indexes
        self.view.setSortingEnabled(True)
        self.view.setTextElideMode(Qt.ElideRight)
        self.view.setWordWrap(True)

        # resize columns and hide certain columns
        for i in range(self.view.horizontalHeader().count()):
            self.view.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            if self.columns[i] in ['Details']:
                self.view.setColumnHidden(i, True)

        # create menu bar widgets
        view_action = QAction("View Mode", self)
        self.edit_action = QAction("Edit Mode", self)
        save_action = QAction("Save Changes", self)
        new_action = QAction("New", self)
        export_action = QAction("Export Data", self)
        upload_action = QAction("Import Data", self)
        clear_action = QAction("Clear Data", self)
        val_options_button = QToolButton()
        val_options_button.setText("Edit Column Values")
        val_options_menu = QMenu()
        hide_columns_button = QToolButton()
        hide_columns_button.setText("Hide Columns")
        visible_columns_menu = QMenu()
        hide_completed_box = QCheckBox(self)
        hide_completed_label = QLabel("Hide Completed")

        # create search bar
        search_label = QLabel("Search: ")
        self.search_bar = QLineEdit()

        # make mode actions checkable and put in group (only one checkable at a time)
        view_action.setCheckable(True)
        view_action.setChecked(True)
        self.edit_action.setCheckable(True)
        group = QActionGroup(self)
        group.addAction(view_action)
        group.addAction(self.edit_action)

        # check hide completed
        hide_completed_box.setChecked(True)

        # get data validation columns
        with open(resource_path(Path('data/type_data.json')), 'r') as f:
            options = json.load(f)

        # dynamically add actions to val_options_menu
        for col in options.keys():
            val_options_menu.addAction(QAction("Edit "+ col +" Values", self))

        # dynamically add actions to visible_columns_menu
        for i, column in enumerate(self.columns): # add a qaction to menu per column
            temp = QAction(column, self)
            temp.setCheckable(True)
            if self.view.isColumnHidden(i) == True:
                temp.setChecked(False)
            else:
                temp.setChecked(True)
            visible_columns_menu.addAction(temp)

        # attach menus to qtoolbuttons
        val_options_button.setMenu(val_options_menu)
        val_options_button.setPopupMode(QToolButton.InstantPopup)
        hide_columns_button.setMenu(visible_columns_menu)
        hide_columns_button.setPopupMode(QToolButton.InstantPopup)

        # connect actions
        view_action.triggered.connect(self.model.makeViewable)
        self.edit_action.triggered.connect(self.model.makeEditable)
        save_action.triggered.connect(self.save)
        export_action.triggered.connect(self.export)
        upload_action.triggered.connect(self.uploadData)
        new_action.triggered.connect(self.add)
        clear_action.triggered.connect(self.clearData)
        val_options_menu.triggered.connect(self.editOptions)
        self.search_bar.textChanged.connect(self.proxy.setFilterFixedString)
        visible_columns_menu.triggered.connect(self.columnsChange)
        hide_completed_box.stateChanged.connect(self.toggleShowCompleted)

        # add actions and widgets to a menu bar
        menubar = QToolBar()
        if edit_on:
            menu_actions = [view_action, self.edit_action, save_action, new_action, export_action, upload_action, clear_action]
            menu_widgets = [val_options_button, hide_columns_button, hide_completed_box, hide_completed_label]
        else:
            menu_actions = [view_action, export_action]
            menu_widgets = [hide_columns_button, hide_completed_box, hide_completed_label]
        for action in menu_actions:
            menubar.addAction(action)
        for widget in menu_widgets:
            menubar.addWidget(widget)

        # create horizontal search bar layout
        search_layout = QHBoxLayout()
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_bar)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_layout.setSpacing(10)

        # vertically stack search bar with menubar and view
        vbox = QVBoxLayout()
        vbox.addWidget(menubar)
        vbox.addLayout(search_layout)
        vbox.addWidget(self.view)
        vbox.setContentsMargins(0,0,0,0)

        # put layout in widget and place widget on window
        container = QWidget()
        container.setLayout(vbox)
        self.setCentralWidget(container)
        self.model.layoutChanged.emit()
        self.showMaximized()

        # locate user's download folder
        if os.name == "nt":
            self.DOWNLOAD_FOLDER = f"{os.getenv('USERPROFILE')}\\Downloads"
        else:  # PORT: For *Nix systems
            self.DOWNLOAD_FOLDER = f"{os.getenv('HOME')}/Downloads"

    def save(self):
        """Save model to json"""
        # clear current selection
        self.view.selectionModel().clear()
        # download to json
        try:
            self.model.saveToJson()
            # deliver success message
            QMessageBox.information(None, "Saved", "Your changes have been successfully saved.")
        except Exception as e:
            self.showError('Saving JSON', e)
            return

    def add(self):
        """Open new task window"""
        # create a NewTask object
        from src.classes.add_row import NewTask
        self.taskWindow = NewTask(self.model)

    def getConfirmation(self, action, task_name, message):
        """Ask user if they would like to complete the action"""
        # create message box
        reply = QMessageBox.critical(self, 'Confirm '+action.title(), 
                        "Are you sure you want to " + action  +" " + task_name + "?"+message, QMessageBox.Yes, QMessageBox.Cancel)

        # return reply
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def closeEvent(self, event):
        """Ask user if they would like to save unsaved changes"""
        # check if model is dirty or not
        if self.model.isDirty() == False:
            # close
            event.accept()
        else:
            # ask user if they want to save changes
            reply = QMessageBox.question(self, 'Unsaved Changes', 
                            "Would you like to save your changes before exiting?", QMessageBox.Yes, QMessageBox.No)
            # save if yes accepted
            if reply == QMessageBox.Yes:
                self.save()
            else:
                second_confirmation = QMessageBox.question(self, 'Discard Changes', 
                            "Are you sure you want to delete all changes and exit?", QMessageBox.Yes, QMessageBox.Cancel)
                if second_confirmation == QMessageBox.Cancel:
                    event.ignore()
                else: event.accept()

    def export(self):
        """Export the database to .xlsx"""
        # get new path name for file
        filename = 'task_tracker_on_'+datetime.now().strftime('%m%d%Y_%H%M%S')+'.xlsx'
        path = (os.path.join(self.DOWNLOAD_FOLDER, filename))
        # give confirmation message
        if QMessageBox.information(None, "Export Database", "Exporting to: \n"+path.__str__(), QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Ok:
            # save to path
            try:
                # save to JSON
                self.model.toDataFrame().to_excel(path)
                # give success message
                QMessageBox.information(self, 'Successfully Downloaded', "You can find the database in your downloads folder. It is named '"+filename+"'.")
            except Exception as e:
                # give failure message
                self.showError('Exporting Data', e)
                return
    
    def markCompleted(self, row, row_obj):
        """Mark a task as completed"""
        # ask for confirmation
        if self.getConfirmation('mark complete', self.model.index(row, 0).data(), " This cannot be undone."):
            # mark as completed
            try:
                # delete the row from the model and reindex model
                self.model.setData(self.model.index(row, self.columns.index('Status'), QModelIndex()), 'Completed '+str(date.today()), Qt.ItemIsEditable)
                # give success message
                message = str(row_obj.iloc[0])+' has been successfully marked as completed.'
                QMessageBox.information(None, "Marked Completed", message)
            # give failure message
            except Exception as e:
                self.showError('Changing Cell Data', e)
                return

    def cloneTask(self, row_obj):
        """Clone a task into a new row"""
        # ask user if they want to clone
        if self.getConfirmation('clone', row_obj.iloc[0], ''):
            # create a new copy of the row, update Ownership Start Day
            cloned_row = row_obj.copy()
            cloned_row['Date Created'] = str(date.today())
            try:
                # insert the new row into the model
                self.model.addRows(cloned_row.to_frame().T)
                # delete the row instance
                del cloned_row
                # give success message
                QMessageBox.critical(None, "Success Cloning", row_obj.iloc[0]+" was successfully cloned.")
            except Exception as e:
                # give failure message
                self.showError('Cloning', e)
                return
    
    def editMenu(self, qindex, options):
        """Pop up context menu to change a data value from a dropdown menu"""
        # create menu
        menu = QMenu()
        menu.setTitle('Change Cell Value')
        # add options
        for option in options:
            menu.addAction(option)
        # show menu
        action = menu.exec_(QCursor.pos())
        # connect actions to data changes
        for val in menu.actions():
            if action == val:
                try: self.model.setData(qindex, val.text(), Qt.EditRole)
                except Exception as e:
                    self.showError('Changing Data', e)
                    return
    
    def regMenu(self, row):
        """Context menu allows you to clone a task or mark it as completed"""
        # create menu
        menu = QMenu()
        # add actions
        mark_completed_action = menu.addAction("Mark Completed")
        cloneAction = menu.addAction("Clone")
        # show menu
        action = menu.exec_(QCursor.pos())
            
        # if user selects mark completed
        if action == mark_completed_action:
            try: self.markCompleted(row, self.model.getRowObj(row))
            except Exception as e:
                self.showError('Marking Completed', e)
                return

        if action == cloneAction:
            try: self.cloneTask(self.model.getRowObj(row))
            except Exception as e:
                self.showError('Cloning', e)
                return
    
    def contextMenuEvent(self, event):
        """Handles right click events"""
        # check if edit mode is active
        if self.edit_action.isChecked():
            # get row clicked on
            view_index = self.view.selectionModel().currentIndex()
            # map row to proxy
            proxy_index = self.proxy.index(view_index.row(), view_index.column())
            # check validity of proxy index
            if not proxy_index.isValid():
                QMessageBox.critical(None, 'Error', 'The index clicked was invalid.')
                return
            # map row to status_proxy
            status_qindex = self.proxy.mapToSource(proxy_index)
            # check validity of status_qindex
            if not status_qindex.isValid():
                QMessageBox.critical(None, 'Error', 'The index clicked was invalid.')
                return
            # map row to model
            model_qindex = self.status_proxy.mapToSource(status_qindex)
            # check validity of model index
            if not model_qindex.isValid():
                QMessageBox.critical(None, 'Error', 'The index clicked was invalid.')
                return

            # get row index and column name
            row = model_qindex.row()
            col_name = self.columns[model_qindex.column()]

            # get options data
            try:
                from src.run import resource_path
                with open(resource_path(Path('data/type_data.json')), 'r') as f:
                    options = json.load(f)
            except Exception as e:
                self.showError('Loading Options', e)
                return

            # check if column is an editable column
            if col_name in options.keys():
                # show editMenu
                self.editMenu(self.model.index(row, model_qindex.column(), QModelIndex()), options[col_name])
            # if column was first one, show regMenu
            elif col_name == self.columns[0]: self.regMenu(row)

    def editOptions(self, action):
        """Create a OptionsWindow widget and show"""
        from src.classes.edit_options import OptionsWindow
        self.options_window = OptionsWindow(action.text())
        self.options_window.show()
    
    def columnsChange(self, checkbox):
        """Toggle if a column is hidden or shown"""
        index = self.columns.index(checkbox.text())
        self.view.setColumnHidden(index, checkbox.isChecked()==False)
    
    def uploadData(self):
        """Select a file for upload.

        Prompt user to choose a file to upload for translation.
        Ensure that file chosen is valid.
        """

        # have the user choose a file to upload
        try: filepath = QFileDialog.getOpenFileName(self,
                                     "Select a file to open", None,
                                     'Excel (*.xlsx)')
        except Exception as e:
            self.showError('Getting Filepath', e)
            return
        
        # if file is null (user x'ed out), break
        if filepath[0] == '':
            return
        
        # load data
        try: new_data = pd.read_excel(filepath[0], sheet_name=0)
        except Exception as e:
            self.showError('Reading File', e)
            return

        # get rid of null values and format as str
        new_data = new_data.dropna(how='all') # get rid of null values
        new_data = new_data.fillna('') # use '' as placeholder
        new_data = new_data.astype(str) # set everything to str

        # get rid of unknown columns
        for col in new_data.columns:
            # get rid of unknown columns
            if col not in self.columns:
                new_data.drop(col, axis = 1)
        
        # add in missing columns
        for col in self.columns:
            if col not in new_data.columns:
                new_data[col] = ['' for _ in range(new_data.shape[0])]

        # format data
        new_data = new_data[self.columns] # order columns
        new_data['Status'] = new_data['Status'].replace('', 'Active') # put null statuses as Active

        # capitalize values as necessary
        for col in new_data.columns.tolist():
            if col in ['Title', 'Category', 'Priority']:
                new_data[col] = new_data[col].str.title()

        # get type contents
        try:
            from src.run import resource_path
            with open(resource_path(Path('data/type_data.json')), 'r') as f:
                    options = json.load(f)
        except Exception as e:
            self.showError('Getting Options', e)
            return

        # process new data into a new options dict
        for col in self.columns:
            if col in options:
                new_options = new_data[col].values.tolist()
                if len(options[col]) != 0: new_options += options[col]
                new_options = list(set(new_options))
                # get rid of null values
                if '' in new_options: new_options.remove('')
                options[col] = new_options
    
        # join old and new data for display
        try: joined_data = self.model.toDataFrame()._append(new_data, ignore_index = True)
        except Exception as e:
            self.showError('Joining Data', e)
            return

        # create a DataPreview widget and show
        try:
            from src.classes.upload_preview import DataPreview
            self.preview_data = DataPreview(joined_data, new_data, self.model, options)
        except Exception as e:
            self.showError('Showing Preview', e)
            return
        # get rid of DataFrame instances
        del joined_data
        del new_data
    
    def clearData(self):
        """Get rid of all"""
        # confirm from user
        psswd, input = QInputDialog.getText(
                self, 'Confirm Clear All Data', "Enter password:", QLineEdit.Normal)
        # if input is successful
        if input:
            # check password
            if psswd == 'CLEAR ALL DATA':
                # confirm again
                if self.getConfirmation('clear', 'all data', ' This action is irreversible.'):
                    # save a copy
                    self.export()
                    # remove all data from model
                    try: self.model.clearAllData()
                    except Exception as e:
                        self.showError('Clearing Model Data', e)
                        return
                    # remove all data from json
                    try:
                        from src.run import resource_path
                        with open(resource_path(Path('data/type_data.json')), 'r') as f:
                            options = json.load(f)
                        # clear type_data
                        for col in options:
                            options[col] = []
                        # save edit options to json
                        with open(resource_path(Path('data/type_data.json')), 'w') as f:
                            json.dump(options, f)
                    except Exception as e:
                        self.showError('Clearing Column Options', e)
                        return
                    # save empty model data to json
                    try: self.model.saveToJson()
                    except Exception as e:
                        self.showError('Saving Model Data to JSON', e)
                        return
                    # give success message
                    QMessageBox.information(None, "Successfully Cleared", "The database is empty.")
            else:
                # if something failed, give failure message
                QMessageBox.critical(None, "Wrong Password", "The password inputted was incorrect, try again.")
    
    def toggleShowCompleted(self, state):
        """Change if completed tasks are shown or not"""
        # check checkbox state
        if state == Qt.Unchecked:
            # set filter string to nothing (accepts all)
            self.status_proxy.setFilterFixedString("")
        # set filter string to 'Active' tasks only
        else: self.status_proxy.setFilterFixedString("Active")

    def showError(self, action, e):
        """Print an error message"""
        # get name of function which caused the error
        try: 
            tb = sys.exc_info()[-1]
            stk = traceback.extract_tb(tb, 1)
            fname = stk[0][2]
        except: fname = 'Could not locate function'

        # format message with traceback and function name
        template = "Function Called: {0} \n \n {1}"
        try:
            message = template.format(fname, traceback.format_exc())
        except: 
            message = template.format(fname, 'Error: \n' + str(e))

        QMessageBox.critical(None, 'Error ' + action, message)
