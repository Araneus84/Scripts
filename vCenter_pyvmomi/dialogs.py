import tkinter as tk

class PasswordDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Enter Password")
        self.top.geometry("300x100")
        self.top.resizable(False, False)

        tk.Label(self.top)

        tk.Label(self.top, text="Password:").pack(pady=10)

        
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.password_entry.pack(padx=10)
        self.password_entry.focus_set()

        self.button = tk.Button(self.top, text="OK", command=self.on_ok)
        self.button.pack(pady=10)

        self.password = None

        # Bind the Enter key to the OK button
        self.password_entry.bind("<Return>", lambda event: self.on_ok())

        # Wait for user input
        self.top.grab_set()
        parent.wait_window(self.top)

    def on_ok(self):
        self.password = self.password_entry.get()
        self.top.destroy()
