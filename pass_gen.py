import tkinter
import string
import random

class Window():
    MAX_CHARS = 15
    MIN_CHARS = 3
    CHARS_OPTIONS = ["Alphanumeric", "Numeric", "Alpha"]
    GRID_PADY = (18, 18)
    def __init__(self):
        self.initUI()


def initUI(self):
    # Construction of the root element
    self.master = tkinter.Tk()
    self.master.title("Password Generator")
    self.master.geometry("580x250")

    self.ptype = tkinter.StringVar(self.master, value=Window.CHARS_OPTIONS[0])
    self.n_chars = tkinter.IntVar(self.master, value=Window.MIN_CHARS)

