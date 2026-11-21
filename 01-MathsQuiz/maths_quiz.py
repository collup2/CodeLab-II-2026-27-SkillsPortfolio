import random
import tkinter as tk

TOTAL_QUESTIONS = 10    # Game settings: number of questions, points per attemp and feedback delay
POINTS_FIRST_ATTEMPT = 10
POINTS_SECOND_ATTEMPT = 5
FEEDBACK_DELAY_MS = 1300

DIFFICULTY_RANGES = {  # Lowest and highest numbers for each difficulty level.
   "Easy": (0, 9),
   "Moderate": (10, 99),
   "Advanced": (1000, 9999),
}

DIFFICULTY_DESCRIPTIONS = {
   "Easy": "single digit numbers",
   "Moderate": "double digit numbers",
   "Advanced": "4 digit numbers",
}

WINDOW_W = 520
WINDOW_H = 440
PROGRESS_W = 440

BG = "#1e1e2e"   # Color palette for the application
CARD = "#2a2a3d"
ENTRY_BG = "#33334d"
ENTRY_BORDER = "#44445f"
TEXT = "#e6e6f0"
MUTED = "#9aa0b8"
ACCENT = "#7aa2f7"
ACCENT_HOVER = "#93b4ff"
GREEN = "#7ed99b"
RED = "#f7768e"
AMBER = "#e0af68"
DISABLED = "#3a3a52"

FONT = "Helvetica"

DIFFICULTY_COLOURS = {   # Background and hover colors for each difficulty level
   "Easy": ("#4caf7d", "#63c593"),
   "Moderate": ("#e0af68", "#f0c27f"),
   "Advanced": ("#f7768e", "#ff90a4"),
}

GRADE_COLOURS = {
   "A+": "#ffd75e",
   "A": GREEN,
   "B": GREEN,
   "C": AMBER,
   "D": AMBER,
   "F": RED,
}

CONFETTI_COLOURS = ["#ffd75e", "#7aa2f7", "#f7768e", "#7ed99b", "#bb9af7", "#e0af68"]

def randomInt(difficulty):   # Returns a random integer within the range for the given difficulty level.
   low, high = DIFFICULTY_RANGES[difficulty]
   return random.randint(low, high)

def decideOperation():
   return random.choice(["+", "-"])

def gradeFor(score):  # Returns a letter grade based on the score percentage.
   if score >= 90:
      return "A+"
   if score >= 80:
      return "A"
   if score >= 70:
      return "B"
   if score >= 60:
      return "C"
   if score >= 50:
      return "D"
   return "F"

def blend(colour_a, colour_b, t):  # Blends two hex colors based on a ratio t (0.0 to 1.0) and returns the resulting color.
   a = [int(colour_a[i:i + 2], 16) for i in (1, 3, 5)]
   b = [int(colour_b[i:i + 2], 16) for i in (1, 3, 5)]
   mixed = [int(a[i] + (b[i] - a[i]) * t) for i in range(3)]
   return "#%02x%02x%02x" % tuple(mixed)

class FlatButton(tk.Label):  # A custom button widget that changes color on hover and can be enabled or disabled.

   def __init__(self, parent, text, command, bg, hover, fg=BG, width=30, font=None):
      super().__init__(
         parent,
         text=text,
         bg=bg,
         fg=fg,
         width=width,
         pady=9,
         font=font or (FONT, 12, "bold"),
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

   def setEnabled(self, enabled):  # Enables or disables the button, changing its appearance and cursor accordingly.
      self.enabled = enabled
      self.config(
         bg=self.base if enabled else DISABLED,
         fg=self.base_fg if enabled else MUTED,
         cursor="hand2" if enabled else "arrow",
      )

class MathsQuiz:

   def __init__(self, root):  # Set up the window, container frame and game state, then show the menu.
      self.root = root
      self.root.title("Maths Quiz")
      self.root.configure(bg=BG)
      self.root.resizable(False, False)
      self.centreWindow()
      self.container = tk.Frame(self.root, bg=BG, padx=20, pady=20)
      self.container.pack(fill="both", expand=True)
      self.difficulty = None
      self.score = 0
      self.question_number = 0
      self.attempt = 1
      self.num1 = 0
      self.num2 = 0
      self.operator = "+"
      self.correct_answer = 0
      self.locked = False
      self.progress_current = 0.0
      self.progress_target = 0.0
      self.progress_running = False
      self.displayMenu()

   def centreWindow(self):
      self.root.update_idletasks()
      x = (self.root.winfo_screenwidth() - WINDOW_W) // 2
      y = (self.root.winfo_screenheight() - WINDOW_H) // 2
      self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

   def fadeIn(self, step=0):
      alpha = min(1.0, step / 8)
      try:
         self.root.attributes("-alpha", alpha)
      except tk.TclError:
         return
      if alpha < 1.0:
         self.root.after(20, lambda: self.fadeIn(step + 1))

   def clearScreen(self):
      for widget in self.container.winfo_children():
         widget.destroy()
      self.fadeIn()

   def displayMenu(self):  # Displays the main menu with difficulty level options.
      self.clearScreen()
      tk.Label(
         self.container, text="Maths Quiz", bg=BG, fg=TEXT, font=(FONT, 28, "bold")
      ).pack(pady=(20, 4))
      tk.Frame(self.container, bg=ACCENT, width=90, height=3).pack()
      tk.Label(
         self.container,
         text="Select a difficulty level",
         bg=BG,
         fg=MUTED,
         font=(FONT, 12),
      ).pack(pady=(14, 20))
      for level in DIFFICULTY_RANGES:
         base, hover = DIFFICULTY_COLOURS[level]
         FlatButton(
            self.container,
            text=f"{level}: {DIFFICULTY_DESCRIPTIONS[level]}",
            command=lambda lvl=level: self.startQuiz(lvl),
            bg=base,
            hover=hover,
            width=34,
         ).pack(pady=6)

   def startQuiz(self, difficulty):  # Starts the quiz by initializing the game state and displaying the first question. 
      self.difficulty = difficulty
      self.score = 0
      self.question_number = 0
      tk.Label(
         self.container,
         text=f"Starting {difficulty} mode...",
         bg=BG,  # Create the header along with the progress bar and question label, then show the first question.
         fg=ACCENT,
         font=(FONT, 14, "bold"),
      ).pack(pady=40)

if __name__ == "__main__":
   root = tk.Tk()
   MathsQuiz(root)
   root.mainloop()