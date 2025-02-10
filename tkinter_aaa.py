import tkinter as tk
from tkinter import ttk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tkinter GUI")
        self.geometry("400x300")

        frame = ttk.Frame(self)
        frame.pack()

        bottomframe = ttk.Frame(self)
        bottomframe.pack(side=tk.BOTTOM)

        redbutton = ttk.Button(frame, text="Red", fg="red")
        redbutton.pack(side=tk.LEFT)

        greenbutton = ttk.Button(frame, text="Brown", fg="brown")
        greenbutton.pack(side=tk.LEFT)

        bluebutton = ttk.Button(frame, text="Blue", fg="blue")
        bluebutton.pack(side=tk.LEFT)

        blackbutton = ttk.Button(bottomframe, text="Black", fg="black")
        blackbutton.pack(side=tk.BOTTOM)