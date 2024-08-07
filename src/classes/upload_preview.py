from PyQt5.QtWidgets import QTableView, QMainWindow, QHeaderView, QWidget, QPushButton, QMessageBox, QVBoxLayout
from PyQt5.QtCore import QSize
from pathlib import Path
import json

class DataPreview(QMainWindow):
    def __init__(self, joined_data, new_data, model, options):
        """Create a preview window of data to be uploaded"""
        super().__init__()

        # set up variables
        self.joined_data = joined_data
        self.new_data = new_data
        self.main_model = model
        self.options = options

        # configure window size and title
        self.setMinimumSize(QSize(990, 630)) 
        self.setWindowTitle('New Data Preview')

        # create a mini model for display
        try:
            from src.classes.pandas_model import PandasModel
            self.new_model = PandasModel(joined_data)
            view = QTableView()
            view.verticalHeader().hide()
            view.setModel(self.new_model)
            for i in range(view.horizontalHeader().count()):
                view.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(None, 'Error Creating Display Model', str(e))
            return

        # Add a button to save changes
        save_button = QPushButton('Save Changes', self)
        save_button.resize(100, 20)
        save_button.clicked.connect(self.save)

        # add a cancel button
        cancel_button = QPushButton('Cancel', self)
        cancel_button.resize(100, 20)
        cancel_button.clicked.connect(self.close)

        # set up layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(view)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.show()

    def save(self):
        """Save the new rows in dataframe and update json files"""
        # confirm with user that they want to complete action
        reply = QMessageBox.critical(self, 'Confirm Submit New Data', 
                        "Are you sure you want to append the uploaded data to the database?", QMessageBox.Yes, QMessageBox.Cancel)

        # check reply
        if reply == QMessageBox.Yes:
            self.hide() # close window

            # replace data in current model
            try: self.main_model.addRows(self.new_data)
            except Exception as e:
                QMessageBox.critical(None, 'Error Adding Rows', str(e))
                return

            # update json files
            try:
                from src.run import resource_path
                with open(resource_path(Path('data/type_data.json')), 'w') as f:
                    json.dump(self.options, f)
            except Exception as e:
                QMessageBox.critical(None, 'Error Saving Column Options', str(e))
                return
            
            try: self.main_model.saveToJson()
            except Exception as e:
                QMessageBox.critical(None, 'Error Saving Data to JSON', str(e))
                return

            # give success message
            QMessageBox.information(self, 'Successfully Added Data', "The data has been added to the database.")
            
        else:
            self.hide() # hide window
            # give exit message
            QMessageBox.information(self, 'Data Not Added', "You did not upload the data.")
