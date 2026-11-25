import random
import tkinter as tk

TOTAL_QUESTIONS = 10 # Game settings: number of questions, points per attempt and feedback delay
POINTS_FIRST_ATTEMPT = 10
POINTS_SECOND_ATTEMPT = 5
FEEDBACK_DELAY_MS = 1300

DIFFICULTY_RANGES = { # Lowest and highest number used for each difficulty level
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

BG = "#1e1e2e" # Colour palette used across the whole interface
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

DIFFICULTY_COLOURS = { # Button colour and hover colour for each difficulty
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

def randomInt(difficulty): # Return a random number within the range for the chosen difficulty
   low, high = DIFFICULTY_RANGES[difficulty]
   return random.randint(low, high)

def decideOperation():
   return random.choice(["+", "-"])

def gradeFor(score): # Convert a score out of 100 into a letter grade
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

def blend(colour_a, colour_b, t): # Mix two hex colours; t=0 gives the first colour, t=1 gives the second
   a = [int(colour_a[i:i + 2], 16) for i in (1, 3, 5)]
   b = [int(colour_b[i:i + 2], 16) for i in (1, 3, 5)]
   mixed = [int(a[i] + (b[i] - a[i]) * t) for i in range(3)]
   return "#%02x%02x%02x" % tuple(mixed)

class FlatButton(tk.Label): # Custom button built from a Label so colours and hover work on every operating system

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

   def setEnabled(self, enabled): # Grey the button out or restore its normal colours
      self.enabled = enabled
      self.config(
         bg=self.base if enabled else DISABLED,
         fg=self.base_fg if enabled else MUTED,
         cursor="hand2" if enabled else "arrow",
      )

class MathsQuiz:

   def __init__(self, root): # Set up the window, container frame and game state, then show the menu
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

   def displayMenu(self): # Show the title and one button per difficulty level
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

   def startQuiz(self, difficulty): # Reset score and question count, then start the first question
      self.difficulty = difficulty
      self.score = 0
      self.question_number = 0
      self.buildQuizScreen()
      self.nextQuestion()

   def buildQuizScreen(self): # Create the header, progress bar, problem card, answer box, submit button and feedback label
      self.clearScreen()
      self.progress_current = 0.0
      self.progress_target = 0.0
      self.progress_running = False
      header = tk.Frame(self.container, bg=BG)
      header.pack(fill="x", pady=(0, 8))
      self.header_label = tk.Label(
         header, bg=BG, fg=MUTED, font=(FONT, 11)
      )
      self.header_label.pack(side="left")
      self.score_label = tk.Label(
         header, bg=CARD, fg=ACCENT, font=(FONT, 11, "bold"), padx=12, pady=3
      )
      self.score_label.pack(side="right")
      self.progress = tk.Canvas(
         self.container, width=PROGRESS_W, height=8, bg=CARD, highlightthickness=0
      )
      self.progress.pack(pady=(0, 18))
      self.progress_fill = self.progress.create_rectangle(
         0, 0, 0, 8, fill=ACCENT, width=0
      )
      card = tk.Frame(self.container, bg=CARD, padx=30, pady=18)
      card.pack(fill="x")
      self.problem_label = tk.Label(
         card, bg=CARD, fg=TEXT, font=(FONT, 36, "bold")
      )
      self.problem_label.pack()
      self.entry_frame = tk.Frame(self.container, bg=BG)
      self.entry_frame.pack(pady=18, padx=20)
      tk.Label(
         self.entry_frame, text="Your answer:", bg=BG, fg=MUTED, font=(FONT, 12)
      ).pack(side="left", padx=(0, 10))
      self.answer_entry = tk.Entry(
         self.entry_frame,
         width=10,
         font=(FONT, 18),
         justify="center",
         bg=ENTRY_BG,
         fg=TEXT,
         insertbackground=TEXT,
         disabledbackground=ENTRY_BG,
         disabledforeground=TEXT,
         relief="flat",
         highlightthickness=2,
         highlightbackground=ENTRY_BORDER,
         highlightcolor=ACCENT,
      )
      self.answer_entry.pack(side="left")
      self.answer_entry.bind("<Return>", lambda event: self.submitAnswer())
      self.submit_button = FlatButton(
         self.container,
         text="Submit",
         command=self.submitAnswer,
         bg=ACCENT,
         hover=ACCENT_HOVER,
         width=18,
      )
      self.submit_button.pack(pady=4)
      self.feedback_label = tk.Label(
         self.container,
         bg=BG,
         fg=TEXT,
         font=(FONT, 12),
         wraplength=420,
         height=2,
      )
      self.feedback_label.pack(pady=8)

   def setProgress(self, fraction):
      self.progress_target = PROGRESS_W * fraction
      if not self.progress_running:
         self.progress_running = True
         self.stepProgress()

   def stepProgress(self):
      if not self.progress.winfo_exists():
         self.progress_running = False
         return
      difference = self.progress_target - self.progress_current
      if abs(difference) < 1:
         self.progress_current = self.progress_target
         self.progress_running = False
      else:
         self.progress_current += difference * 0.3
         self.root.after(16, self.stepProgress)
      self.progress.coords(self.progress_fill, 0, 0, self.progress_current, 8)

   def setEntryColour(self, colour):
      self.answer_entry.config(bg=colour, disabledbackground=colour)

   def flashEntry(self, colour):
      self.setEntryColour(colour)
      self.root.after(350, self.resetEntryColour)

   def resetEntryColour(self):
      if self.answer_entry.winfo_exists():
         self.setEntryColour(ENTRY_BG)

   def shakeEntry(self, step=0): # Move the answer row left and right to show a wrong answer
      offsets = [-10, 10, -8, 8, -5, 5, -2, 2, 0]
      if not self.entry_frame.winfo_exists():
         return
      offset = offsets[step]
      self.entry_frame.pack_configure(padx=(20 + offset, 20 - offset))
      if step + 1 < len(offsets):
         self.root.after(30, lambda: self.shakeEntry(step + 1))

   def floatPoints(self, points): # Show the points earned floating upwards while fading out
      label = tk.Label(
         self.container, text=f"+{points}", bg=BG, fg=GREEN, font=(FONT, 22, "bold")
      )
      total_steps = 14
      def animate(step=0):
         if not label.winfo_exists():
            return
         t = step / total_steps
         label.place(relx=0.86, y=170 - 50 * t, anchor="center")
         label.config(fg=blend(GREEN, BG, t))
         if step < total_steps:
            self.root.after(30, lambda: animate(step + 1))
         else:
            label.destroy()
      animate()

   def nextQuestion(self): # Create a new problem, or show the results after the last question
      self.question_number += 1
      if self.question_number > TOTAL_QUESTIONS:
         self.displayResults()
         return
      self.attempt = 1
      self.locked = False
      self.num1 = randomInt(self.difficulty)
      self.num2 = randomInt(self.difficulty)
      self.operator = decideOperation()
      if self.operator == "+": # Work out the correct answer for the chosen operation
         self.correct_answer = self.num1 + self.num2
      else:
         self.correct_answer = self.num1 - self.num2
      self.displayProblem()

   def displayProblem(self): # Update the labels, clear the answer box and move the progress bar
      self.header_label.config(
         text=f"Question {self.question_number} of {TOTAL_QUESTIONS}   |   {self.difficulty}"
      )
      self.score_label.config(text=f"Score: {self.score}")
      self.problem_label.config(text=f"{self.num1} {self.operator} {self.num2} = ?")
      self.feedback_label.config(text="")
      self.answer_entry.config(state="normal")
      self.resetEntryColour()
      self.answer_entry.delete(0, tk.END)
      self.answer_entry.focus_set()
      self.submit_button.setEnabled(True)
      self.setProgress((self.question_number - 1) / TOTAL_QUESTIONS)

   def isCorrect(self, user_answer): # Return True if the player's answer matches the correct answer
      return user_answer == self.correct_answer

   def submitAnswer(self): # Check the answer and apply scoring rules
      if self.locked:
         return
      text = self.answer_entry.get().strip()
      try: # Make sure the input is a whole number
         user_answer = int(text)
      except ValueError:
         self.feedback_label.config(text="Please enter a whole number.", fg=AMBER)
         self.shakeEntry()
         return
      if self.isCorrect(user_answer): # Correct answer: 10 points on the first try, 5 on the second
         points = POINTS_FIRST_ATTEMPT if self.attempt == 1 else POINTS_SECOND_ATTEMPT
         self.score += points
         self.score_label.config(text=f"Score: {self.score}")
         self.flashEntry("#2f5d45")
         self.floatPoints(points)
         self.finishQuestion(f"✓ Correct! +{points} points.", GREEN)
      elif self.attempt == 1: # First wrong answer: allow a second attempt
         self.attempt = 2
         self.answer_entry.delete(0, tk.END)
         self.feedback_label.config(text="✗ Not quite. Try once more!", fg=RED)
         self.flashEntry("#6b2f3d")
         self.shakeEntry()
      else: # Second wrong answer: show the correct answer and move on
         self.flashEntry("#6b2f3d")
         self.shakeEntry()
         self.finishQuestion(
            f"✗ Wrong. The correct answer was {self.correct_answer}.", RED
         )

   def finishQuestion(self, message, colour): # Lock input, show feedback, then move to the next question after a short delay
      self.locked = True
      self.submit_button.setEnabled(False)
      self.answer_entry.config(state="disabled")
      self.feedback_label.config(text=message, fg=colour)
      self.setProgress(self.question_number / TOTAL_QUESTIONS)
      self.root.after(FEEDBACK_DELAY_MS, self.nextQuestion)

   def displayResults(self): # Show the final score out of 100, the grade and the play again buttons
      self.clearScreen()
      grade = gradeFor(self.score)
      maximum = TOTAL_QUESTIONS * POINTS_FIRST_ATTEMPT
      self.confetti = tk.Canvas(self.container, bg=BG, highlightthickness=0)
      self.confetti.place(x=0, y=0, relwidth=1, relheight=1)
      tk.Label(
         self.container, text="Quiz Complete!", bg=BG, fg=TEXT, font=(FONT, 24, "bold")
      ).pack(pady=(20, 4))
      tk.Frame(self.container, bg=ACCENT, width=90, height=3).pack()
      self.result_score = tk.Label(
         self.container, text=f"0 / {maximum}", bg=BG, fg=TEXT, font=(FONT, 40, "bold")
      )
      self.result_score.pack(pady=(22, 4))
      self.result_grade = tk.Label(
         self.container, text="", bg=BG, fg=GRADE_COLOURS[grade], font=(FONT, 30, "bold")
      )
      self.result_grade.pack(pady=4)
      tk.Label(
         self.container,
         text="Would you like to play again?",
         bg=BG,
         fg=MUTED,
         font=(FONT, 12),
      ).pack(pady=(24, 10))
      button_frame = tk.Frame(self.container, bg=BG)
      button_frame.pack()
      FlatButton(
         button_frame,
         text="Yes",
         command=self.displayMenu,
         bg=ACCENT,
         hover=ACCENT_HOVER,
         width=10,
      ).pack(side="left", padx=8)
      FlatButton(
         button_frame,
         text="No",
         command=self.root.destroy,
         bg=ENTRY_BORDER,
         hover="#585878",
         fg=TEXT,
         width=10,
      ).pack(side="left", padx=8)
      self.countUp(0, grade, maximum)

   def countUp(self, shown, grade, maximum): # Animate the score counting up from 0
      if not self.result_score.winfo_exists():
         return
      shown = min(self.score, shown + max(1, self.score // 30))
      self.result_score.config(text=f"{shown} / {maximum}")
      if shown < self.score:
         self.root.after(25, lambda: self.countUp(shown, grade, maximum))
      else:
         self.result_grade.config(text=f"Grade: {grade}")
         if grade == "A+":
            self.launchConfetti()

   def launchConfetti(self): # Create falling confetti pieces and animate them
      width = WINDOW_W - 40
      pieces = []
      for _ in range(60):
         x = random.randint(0, width)
         y = random.randint(-200, -10)
         size = random.randint(5, 9)
         item = self.confetti.create_rectangle(
            x, y, x + size, y + size, fill=random.choice(CONFETTI_COLOURS), width=0
         )
         pieces.append((item, random.uniform(3, 7), random.uniform(-1.5, 1.5)))
      def fall(frame=0):
         if not self.confetti.winfo_exists():
            return
         for item, speed, drift in pieces:
            self.confetti.move(item, drift, speed)
         if frame < 70:
            self.root.after(30, lambda: fall(frame + 1))
         else:
            self.confetti.delete("all")
      fall()

def main(): # Create the window and start the app
   root = tk.Tk()
   MathsQuiz(root)
   root.mainloop()

if __name__ == "__main__": # Run the quiz only when this file is executed directly
   main()