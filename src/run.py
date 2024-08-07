# imports
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from pathlib import Path
import socket
from random import randrange

# create a unique app id for exec file
try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'ise.it_database.pc_and_laptops'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

# get a unique key for this run
SESSION_KEY = socket.gethostname() + ' ' + ''.join([str(randrange(10)) for _ in range(8)])

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def clearSessionData():
    reset_message = QMessageBox()
    reset_message.setIcon(QMessageBox.Critical)
    reset_message.setWindowTitle('Clear Session Data')
    reset_message.setText('Are you sure you want to clear session data? This could cause data conflicts if another user is actively editing.')
    reset_message.setStandardButtons(QMessageBox.Yes | QMessageBox.Abort)
    reset_message.setDefaultButton(QMessageBox.Abort)
    clear = reset_message.exec()
    if clear == QMessageBox.Yes:
        with open(resource_path(Path('data/active_session.txt')), 'w') as f:
            f.truncate(0)
        return True
    else:
        return False

def regQuit():
    with open(resource_path(Path('data/active_session.txt')), 'r+') as f:
            active_session = f.readlines()
            if SESSION_KEY in active_session:
                f.truncate(0)

def checkUsers():
    """Create and run a window, only if the data file is not open"""
    with open(resource_path(Path('data/active_session.txt')), 'r') as f:
        active_session = f.readlines()
    if active_session != []:
        view_message = QMessageBox()
        view_message.setIcon(QMessageBox.Information)
        view_message.setWindowTitle('Edit Session Active')
        view_message.setText(active_session[0].split()[0] + ' is running an active editing session, so the application will open in view-only mode. Press "Reset" button to clear all session data and open in editing mode **could cause data conflicts**.')
        view_message.setStandardButtons(QMessageBox.Open | QMessageBox.Cancel | QMessageBox.Reset)
        view_message.setDefaultButton(QMessageBox.Open)
        response = view_message.exec()
        if response == QMessageBox.Open:
            return False
        elif response == QMessageBox.Reset and clearSessionData() == True:
            return True
        else: sys.exit()
    return True

def runApp(edit_on):
        if edit_on:
            with open(resource_path(Path('data/active_session.txt')), 'w') as f:
                f.writelines(SESSION_KEY)
        from src.classes.main_window import MainWindow
        window = MainWindow(edit_on)
        app.exec_()


if __name__ == '__main__':
    # run the app
    try:
        app = QApplication(sys.argv)
        sys.exit(runApp(checkUsers()))
    except Exception as e:
        print(e)
    finally:
        regQuit()