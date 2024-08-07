from PyQt5.QtWidgets import QLineEdit, QFormLayout, QVBoxLayout, QLabel, QDialog, QDialogButtonBox, QMessageBox, QComboBox
from datetime import date
import pandas as pd
import json
from pathlib import Path


class NewTask(QDialog):
    def __init__(self, model):
        """Create a form that creates a new row from user input"""
        super(NewTask, self).__init__()

        # set up variables
        self.model = model

        # configure window details
        self.setWindowTitle("Add New Task")
        self.setGeometry(100, 100, 300, 400)

        # get options from json
        from src.run import resource_path
        with open(resource_path(Path('data/type_data.json')), 'r') as f:
            options = json.load(f)

        # set up widgets
        self.title = QLineEdit()
        title_label = QLabel("Title:")
        self.description = QLineEdit()
        description_label = QLabel("Description:")
        self.category = QComboBox()
        self.category.addItem("")
        self.category.addItems(options['Category'])
        category_label = QLabel("Category:")
        self.subtasks = QLineEdit()
        subtasks_label = QLabel("Subtasks:")
        self.priority = QComboBox()
        self.priority.addItem("")
        self.priority.addItems(options['Priority'])
        priority_label = QLabel("Priority:")
        self.timeline = QLineEdit()
        timeline_label = QLabel("Timeline:")
        self.notes = QLineEdit()
        notes_label = QLabel("Notes:")


        # set up widget layout
        inputs = [self.title, self.description, self.category, self.subtasks, self.priority, self.timeline, self.notes]
        labels = [title_label, description_label, category_label, subtasks_label, priority_label, timeline_label, notes_label]
        layout = QFormLayout()
        for i in range(len(inputs)):
            layout.addRow(labels[i], inputs[i])
        layout.setSpacing(20)
 
        # creating a dialog button for ok and cancel
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
 
        # connect to methods on button click
        self.buttonBox.accepted.connect(self.getInfo)
        self.buttonBox.rejected.connect(self.reject)
 
        # set a vertical layout with widgets and dialog buttons
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(layout)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)

        self.show()

    def getInfo(self):
        """Create a new row from input"""
        # set up variables
        title = self.title.text()
        description = self.description.text()
        category = self.category.currentText()
        subtasks = self.subtasks.text()
        priority = self.priority.currentText()
        date_created = str(date.today())
        status = 'Active'
        timeline = self.timeline.text()
        notes = self.notes.text()

        # format the inputs
        if title != title.upper(): title = title.title()

        # check if user left title blank but inputted description, and set title to first word of description
        if title == '' and description != '': title = description.split()[0]

        # create a new row
        results = [title, description, category, subtasks, priority, date_created, status, timeline, notes]
        new_record = pd.DataFrame([results], columns=self.model.getColumnNames())

        self.close()
        
        # add the new row to dataframe and reindex
        try:
            if self.model.addRows(new_record):
                QMessageBox.information(None, 'Successfully Added', title+' was successfully added.')
        except Exception as e:
            QMessageBox.critical(None, 'Failed Add Rows', str(e))
            return
