import os
import random
import tkinter as tk
from tkinter import messagebox

JOKES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "randomJokes.txt") # Look for randomJokes.txt in the same folder as this script

WINDOW_W = 620
WINDOW_H = 430

BG = "#1e1e2e" # Colour palette used across the whole interface
CARD = "#2a2a3d"
TEXT = "#e6e6f0"
MUTED = "#9aa0b8"
ACCENT = "#7aa2f7"
ACCENT_HOVER = "#93b4ff"
GREEN = "#4caf7d"
GREEN_HOVER = "#63c593"
AMBER = "#e0af68"
AMBER_HOVER = "#f0c27f"
GREY = "#44445f"
GREY_HOVER = "#585878"
DISABLED = "#3a3a52"

FONT = "Helvetica"

def loadJokes(path): # Read the jokes file and return a list of (setup, punchline) pairs
   jokes = []
   with open(path, "r", encoding="utf-8") as file:
      for line in file:
         line = line.strip()
         if not line or "?" not in line:
            continue
         setup, punchline = line.split("?", 1) # Split on the first question mark only, so the setup keeps its question mark
         jokes.append((setup.strip() + "?", punchline.strip()))
   return jokes

def blend(colour_a, colour_b, t): # Mix two hex colours; t=0 gives the first colour, t=1 gives the second
   a = [int(colour_a[i:i + 2], 16) for i in (1, 3, 5)]
   b = [int(colour_b[i:i + 2], 16) for i in (1, 3, 5)]
   mixed = [int(a[i] + (b[i] - a[i]) * t) for i in range(3)]
   return "#%02x%02x%02x" % tuple(mixed)

class FlatButton(tk.Label): # Custom button built from a Label so colours and hover work on every operating system

   def __init__(self, parent, text, command, bg, hover, fg=BG, width=20):
      super().__init__(
         parent,
         text=text,
         bg=bg,
         fg=fg,
         width=width,
         pady=9,
         font=(FONT, 12, "bold"),
         cursor="hand2",
      )
      self.command = command
      self.base = bg
      self.hover = hover
      self.base_fg = fg
      self.enabled = True
      self.bind("<Enter>", self.onEnter)
      self.bind("<Leave>", self.onLeave)
      self.bind("<ButtonRelease-1>", self.onClick)

   def onEnter(self, event):
      if self.enabled:
         self.config(bg=self.hover)

   def onLeave(self, event):
      self.config(bg=self.base if self.enabled else DISABLED)

   def onClick(self, event):
      if self.enabled and self.command:
         self.command()

   def setEnabled(self, enabled):
      self.enabled = enabled
      self.config(
         bg=self.base if enabled else DISABLED,
         fg=self.base_fg if enabled else MUTED,
         cursor="hand2" if enabled else "arrow",
      )

class AlexaJokeApp: # Main application window

   def __init__(self, root, jokes): # Build the window, joke card and buttons
      self.root = root
      self.jokes = jokes
      self.current_joke = None
      self.root.title("Alexa Tell Me a Joke")
      self.root.configure(bg=BG)
      self.root.resizable(False, False)
      self.centreWindow()
      container = tk.Frame(self.root, bg=BG, padx=24, pady=20)
      container.pack(fill="both", expand=True)
      tk.Label(
         container, text="Alexa Joke Time", bg=BG, fg=TEXT, font=(FONT, 26, "bold")
      ).pack(pady=(6, 4))
      tk.Frame(container, bg=ACCENT, width=90, height=3).pack()
      card = tk.Frame(container, bg=CARD, padx=24, pady=20) # Card that holds the setup and punchline
      card.pack(fill="x", pady=(22, 20))
      self.setup_label = tk.Label( # Label that shows the joke setup
         card,
         text="Ask Alexa for a joke to get started",
         bg=CARD,
         fg=MUTED,
         font=(FONT, 15),
         wraplength=500,
         justify="center",
         height=3,
      )
      self.setup_label.pack()
      self.punchline_label = tk.Label( # Punchline starts in the card colour so it is invisible until revealed
         card,
         text="",
         bg=CARD,
         fg=CARD,
         font=(FONT, 15, "italic"),
         wraplength=500,
         justify="center",
         height=2,
      )
      self.punchline_label.pack()
      button_frame = tk.Frame(container, bg=BG) # Two by two grid of buttons
      button_frame.pack()
      self.tell_button = FlatButton(
         button_frame,
         text="Alexa tell me a Joke",
         command=self.tellJoke,
         bg=ACCENT,
         hover=ACCENT_HOVER,
      )
      self.tell_button.grid(row=0, column=0, padx=8, pady=6)
      self.punchline_button = FlatButton(
         button_frame,
         text="Show Punchline",
         command=self.showPunchline,
         bg=GREEN,
         hover=GREEN_HOVER,
      )
      self.punchline_button.grid(row=0, column=1, padx=8, pady=6)
      self.punchline_button.setEnabled(False)
      self.next_button = FlatButton(
         button_frame,
         text="Next Joke",
         command=self.tellJoke,
         bg=AMBER,
         hover=AMBER_HOVER,
      )
      self.next_button.grid(row=1, column=0, padx=8, pady=6)
      self.quit_button = FlatButton(
         button_frame,
         text="Quit",
         command=self.root.destroy,
         bg=GREY,
         hover=GREY_HOVER,
         fg=TEXT,
      )
      self.quit_button.grid(row=1, column=1, padx=8, pady=6)
      self.fadeWindow()

   def centreWindow(self):
      self.root.update_idletasks()
      x = (self.root.winfo_screenwidth() - WINDOW_W) // 2
      y = (self.root.winfo_screenheight() - WINDOW_H) // 2
      self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

   def fadeWindow(self, step=0):
      alpha = min(1.0, step / 8)
      try:
         self.root.attributes("-alpha", alpha)
      except tk.TclError:
         return
      if alpha < 1.0:
         self.root.after(20, lambda: self.fadeWindow(step + 1))

   def fadeText(self, label, colour, step=0): # Fade a label's text in by blending from the card colour to its final colour
      if not label.winfo_exists():
         return
      label.config(fg=blend(CARD, colour, step / 10))
      if step < 10:
         self.root.after(30, lambda: self.fadeText(label, colour, step + 1))

   def tellJoke(self): # Pick a random joke and show only its setup, hiding the previous punchline
      choice = random.choice(self.jokes)
      while len(self.jokes) > 1 and choice == self.current_joke: # Pick again so the same joke never appears twice in a row
         choice = random.choice(self.jokes)
      self.current_joke = choice
      self.setup_label.config(text=choice[0], fg=TEXT)
      self.punchline_label.config(text="", fg=CARD)
      self.punchline_button.setEnabled(True)
      self.fadeText(self.setup_label, TEXT)

   def showPunchline(self): # Reveal the punchline below the setup and disable the button until the next joke
      if self.current_joke:
         self.punchline_label.config(text=self.current_joke[1])
         self.punchline_button.setEnabled(False)
         self.fadeText(self.punchline_label, ACCENT)

def main(): # Load the jokes, then create the window and start the app
   try: # Load the jokes before opening the main window
      jokes = loadJokes(JOKES_FILE)
   except FileNotFoundError:
      jokes = None
      message = f"Could not find:\n{JOKES_FILE}"
      title = "File not found"
   else:
      message = "randomJokes.txt contains no valid jokes."
      title = "No jokes"
   if not jokes: # Show an error and exit if the file is missing or contains no valid jokes
      root = tk.Tk()
      root.withdraw()
      messagebox.showerror(title, message)
      root.destroy()
      return
   root = tk.Tk()
   AlexaJokeApp(root, jokes)
   root.mainloop()

if __name__ == "__main__": # Run the app only when this file is executed directly
   main()