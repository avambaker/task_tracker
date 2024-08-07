from PyQt5.QtWidgets import QMainWindow, QWidget, QPlainTextEdit, QPushButton, QMessageBox, QLabel, QVBoxLayout
from PyQt5.QtCore import QSize
from pathlib import Path
import json

class OptionsWindow(QMainWindow):
    def __init__(self, title):
        """Create a window to allow user to edit column value options"""
        super().__init__()

        # set up window
        self.setMinimumSize(QSize(440, 280))
        try: self.column = title.split()[1]
        except Exception as e:
            QMessageBox.critical(None, "Couldn't Get Column Name", "Could not find column name from passed data: "+title+". "+str(e))
            return
        self.setWindowTitle(title)

        # create instructions
        instructions = QLabel("Values should be formatted as a comma separated list.")

        # get options from json
        try:
            from src.run import resource_path
            with open(resource_path(Path('data/type_data.json')), 'r') as f:
                self.options = json.load(f)
        except Exception as e:
            QMessageBox.critical(None, 'Error Loading Values', str(e))
            return

        # set up a text field
        self.text_edit = QPlainTextEdit(self)
        try: self.old_values = self.options[self.column]
        except Exception as e:
            QMessageBox.critical(None, 'Error Getting Options', "Couldn't find options for "+self.column+" in "+self.options.keys()+". "+str(e))
            return
        self.text_edit.setPlainText(', '.join(self.old_values))
        self.text_edit.resize(400, 200)

        # add button to save changes
        self.button = QPushButton('Save Changes', self)
        self.button.resize(400, 40)
        self.button.clicked.connect(self.save_txt)

        # create layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(instructions)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.show()

    def save_txt(self):
        """Update relevant field in json with value from text field"""
        text = self.text_edit.toPlainText() # get text from field
        text_list = text.split(',')
        text_list = [t.strip() for t in text_list if (t != '' and t != ',')]
        if text_list == self.old_values: # check if changes were made
            self.hide()
            return
        else:
            self.options[self.column] = text_list # update relevant column

            # save options in json
            try:
                from src.run import resource_path
                with open(resource_path(Path('data/type_data.json')), 'w') as f:
                    json.dump(self.options, f)
            except Exception as e:
                QMessageBox.critical(None, 'Error Saving Changes', str(e))
                return

            # close window and give success message
            self.hide()
            QMessageBox.information(None, 'Successfully Changed '+ self.column +' Values', 'The values for '+ self.column + ' were successfully changed from \n'+ str(self.old_values) + ' to \n'+ str(self.options[self.column]) + '.')
