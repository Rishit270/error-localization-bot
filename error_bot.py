import subprocess
import re
import linecache
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import os
from datetime import datetime

ERROR_MAP = {
    "SyntaxError": "Syntax", "IndentationError": "Syntax",
    "NameError": "Name", "TypeError": "Type", "ValueError": "Value",
    "ZeroDivisionError": "Runtime", "RuntimeError": "Runtime",
    "ImportError": "Dependency", "ModuleNotFoundError": "Dependency",
    "FileNotFoundError": "IO", "IndexError": "Index", "KeyError": "Key",
    "AttributeError": "Attribute", "RecursionError": "Runtime",
}

SYSTEM_MARKERS = ["site-packages", "lib/python", "Lib\\", "importlib", "_bootstrap", "<frozen"]


def is_user_file(path):
    if not path or path.startswith("<"):
        return False
    for marker in SYSTEM_MARKERS:
        if marker in path:
            return False
    return True


def classify(name):
    return ERROR_MAP.get(name, "General")


def get_suspect_description(exc_name, msg, code_line):
    code = code_line.strip()
    if not code:
        return ""
    desc = f'Suspect Line: "{code}"\n'

    if exc_name == "ZeroDivisionError":
        desc += "Reason: Division by zero happens on this line.\n"
        desc += "Fix: Add a check - if divisor != 0 before dividing."
    elif exc_name == "NameError":
        m = re.search(r"name '(\w+)' is not defined", msg)
        if m:
            desc += f'Reason: Variable "{m.group(1)}" is not defined.\n'
            desc += f'Fix: Define "{m.group(1)}" before this line.'
        else:
            desc += "Reason: A variable on this line does not exist.\nFix: Check spelling."
    elif exc_name == "TypeError":
        desc += "Reason: Wrong data type used in operation.\nFix: Check types of variables."
    elif exc_name == "IndexError":
        desc += "Reason: List index is out of range.\nFix: Check length before accessing."
    elif exc_name == "KeyError":
        desc += "Reason: Dictionary key does not exist.\nFix: Use .get() method."
    elif exc_name == "AttributeError":
        m = re.search(r"has no attribute '(\w+)'", msg)
        if m:
            desc += f'Reason: Object has no attribute "{m.group(1)}".\nFix: Check object type.'
        else:
            desc += "Reason: Attribute access failed.\nFix: Verify object type."
    elif exc_name in ("ImportError", "ModuleNotFoundError"):
        m = re.search(r"No module named '(\w+)'", msg)
        if m:
            desc += f'Reason: Module "{m.group(1)}" not installed.\nFix: pip install {m.group(1)}'
        else:
            desc += "Reason: Import failed.\nFix: Check module name."
    elif exc_name == "SyntaxError":
        desc += "Reason: Python cannot parse this line.\nFix: Check colons, brackets, quotes."
    elif exc_name == "IndentationError":
        desc += "Reason: Wrong indentation.\nFix: Use 4 spaces consistently."
    else:
        desc += f"Reason: This line caused {exc_name}.\nFix: Review the logic."
    return desc


def get_surrounding_lines(filepath, lineno, context=3):
    lines = []
    for i in range(max(1, lineno - context), lineno + context + 1):
        line = linecache.getline(filepath, i)
        if line:
            marker = ">>>" if i == lineno else "   "
            lines.append((i, marker, line.rstrip()))
    return lines


def parse_stderr(stderr):
    frame_re = re.compile(r'File "(.+?)", line (\d+)(?:, in (.+))?')
    exc_re = re.compile(r'^(\w+Error|\w+Exception):\s*(.+)$', re.MULTILINE)
    bare_re = re.compile(r'^(\w+Error|\w+Exception)$', re.MULTILINE)

    frames = frame_re.findall(stderr)
    errors = []
    for m in exc_re.finditer(stderr):
        errors.append((m.group(1), m.group(2).strip()))
    if not errors:
        for m in bare_re.finditer(stderr):
            errors.append((m.group(1), ""))

    results = []
    for exc_name, msg in errors:
        user_frames = [(f, int(l), fn) for f, l, fn in frames if is_user_file(f)]
        if user_frames:
            filepath, lineno, funcname = user_frames[-1]
        elif frames:
            filepath, lineno, funcname = frames[-1][0], int(frames[-1][1]), frames[-1][2]
        else:
            filepath, lineno, funcname = "<unknown>", 0, ""

        code = ""
        if filepath and lineno:
            code = linecache.getline(filepath, lineno).strip()

        context_lines = []
        if filepath and lineno and os.path.exists(filepath):
            context_lines = get_surrounding_lines(filepath, lineno)

        suspect = get_suspect_description(exc_name, msg, code)

        results.append({
            "type": classify(exc_name),
            "exception": exc_name,
            "file": filepath,
            "line": lineno,
            "function": funcname or "<module>",
            "message": msg,
            "code": code,
            "context": context_lines,
            "suspect": suspect,
        })

    for i, r in enumerate(results):
        r["root_cause"] = (i == 0)
    return results


def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TimeoutError: Command timed out", 1
    except Exception as e:
        return "", str(e), 1


class ErrorBotApp:
    def __init__(self, root):
        self.root = root
        root.title("Error Localization Bot")
        root.geometry("950x700")
        root.minsize(700, 500)
        root.configure(bg="#1e1e2e")

        self.c = {
            "bg": "#1e1e2e", "bg2": "#181825", "bg3": "#313244",
            "fg": "#cdd6f4", "fg2": "#a6adc8", "fg3": "#6c7086",
            "red": "#f38ba8", "green": "#a6e3a1", "yellow": "#f9e2af",
            "blue": "#89b4fa", "orange": "#fab387", "pink": "#f5c2e7",
        }
        self.build_ui()

    def build_ui(self):
        # Title
        tf = tk.Frame(self.root, bg=self.c["bg"])
        tf.pack(fill="x", padx=15, pady=(10, 5))
        tk.Label(tf, text="Error Localization Bot", font=("Arial", 20, "bold"),
                 bg=self.c["bg"], fg=self.c["fg"]).pack(side="left")
        tk.Label(tf, text="Subprocess + Stack Trace Analysis", font=("Arial", 9),
                 bg=self.c["bg"], fg=self.c["fg3"]).pack(side="right", pady=8)

        # Command
        cf = tk.Frame(self.root, bg=self.c["bg"])
        cf.pack(fill="x", padx=15, pady=5)
        tk.Label(cf, text="Command:", font=("Arial", 11, "bold"),
                 bg=self.c["bg"], fg=self.c["fg2"]).pack(side="left")
        self.cmd_entry = tk.Entry(cf, font=("Consolas", 12), bg=self.c["bg3"],
                                  fg=self.c["fg"], insertbackground=self.c["fg"],
                                  relief="flat", width=45)
        self.cmd_entry.pack(side="left", padx=8, fill="x", expand=True, ipady=4)
        self.cmd_entry.insert(0, "python main.py")
        self.cmd_entry.bind("<Return>", lambda e: self.analyse())

        # Buttons
        bf = tk.Frame(self.root, bg=self.c["bg"])
        bf.pack(fill="x", padx=15, pady=(0, 5))
        for text, color, cmd in [
            ("Analyse", self.c["green"], self.analyse),
            ("Browse", self.c["blue"], self.browse),
            ("Clear", self.c["red"], self.clear),
            ("Save", self.c["yellow"], self.save_report),
            ("Help", self.c["orange"], self.show_help),
        ]:
            tk.Button(bf, text=text, font=("Arial", 10, "bold"), bg=color,
                      fg="#1e1e2e", relief="flat", cursor="hand2",
                      command=cmd, padx=12, pady=3).pack(side="left", padx=4)

        # Split panels
        self.paned = tk.PanedWindow(self.root, orient="horizontal",
                                     bg=self.c["bg"], sashwidth=4)
        self.paned.pack(fill="both", expand=True, padx=15, pady=5)

        # Left - Output
        left = tk.Frame(self.paned, bg=self.c["bg"])
        self.paned.add(left, width=550)
        tk.Label(left, text="Analysis Output", font=("Arial", 11, "bold"),
                 bg=self.c["bg"], fg=self.c["yellow"]).pack(anchor="w", pady=(0, 3))
        self.output = scrolledtext.ScrolledText(left, font=("Consolas", 10),
                                                 bg=self.c["bg2"], fg=self.c["fg"],
                                                 relief="flat", wrap="word")
        self.output.pack(fill="both", expand=True)

        # Right - Source viewer
        right = tk.Frame(self.paned, bg=self.c["bg"])
        self.paned.add(right, width=350)
        tk.Label(right, text="Source Code Viewer", font=("Arial", 11, "bold"),
                 bg=self.c["bg"], fg=self.c["yellow"]).pack(anchor="w", pady=(0, 3))
        self.source_view = scrolledtext.ScrolledText(right, font=("Consolas", 10),
                                                      bg=self.c["bg2"], fg=self.c["fg"],
                                                      relief="flat", wrap="none")
        self.source_view.pack(fill="both", expand=True)

        # Tags
        for tag, cfg in {
            "title": {"foreground": self.c["yellow"], "font": ("Consolas", 12, "bold")},
            "header": {"foreground": self.c["yellow"], "font": ("Consolas", 10, "bold")},
            "error": {"foreground": self.c["red"]},
            "success": {"foreground": self.c["green"]},
            "info": {"foreground": self.c["blue"]},
            "suspect": {"foreground": self.c["orange"], "font": ("Consolas", 10, "bold")},
            "context": {"foreground": self.c["fg2"]},
            "highlight": {"foreground": self.c["red"], "font": ("Consolas", 10, "bold")},
            "divider": {"foreground": self.c["fg3"]},
            "fix": {"foreground": self.c["green"]},
            "label": {"foreground": self.c["pink"]},
        }.items():
            self.output.tag_config(tag, **cfg)

        self.source_view.tag_config("line_num", foreground=self.c["fg3"])
        self.source_view.tag_config("suspect_line", foreground=self.c["red"],
                                     background="#3b2030", font=("Consolas", 10, "bold"))
        self.source_view.tag_config("normal", foreground=self.c["fg"])
        self.source_view.tag_config("file_header", foreground=self.c["blue"],
                                     font=("Consolas", 10, "bold"))

        # Status bar
        sf = tk.Frame(self.root, bg=self.c["bg3"])
        sf.pack(fill="x", side="bottom")
        self.status = tk.Label(sf, text="  Ready - Type command and click Analyse",
                               font=("Arial", 9), bg=self.c["bg3"],
                               fg=self.c["fg3"], anchor="w")
        self.status.pack(side="left", fill="x", expand=True, padx=5, pady=2)
        self.timer = tk.Label(sf, text="", font=("Arial", 9),
                              bg=self.c["bg3"], fg=self.c["fg3"])
        self.timer.pack(side="right", padx=10, pady=2)

        self.root.bind("<F5>", lambda e: self.analyse())

    def analyse(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            messagebox.showwarning("Warning", "Enter a command first.")
            return

        self.output.delete("1.0", "end")
        self.source_view.delete("1.0", "end")
        self.status.config(text="  Running...", fg=self.c["yellow"])
        self.root.update()

        start = datetime.now()
        stdout, stderr, code = run_command(cmd)
        elapsed = (datetime.now() - start).total_seconds()
        self.timer.config(text=f"{elapsed:.2f}s")

        if code == 0 and not stderr.strip():
            self.output.insert("end", "SUCCESS - No Errors!\n\n", "success")
            if stdout.strip():
                self.output.insert("end", "Output:\n", "info")
                self.output.insert("end", stdout)
            self.status.config(text="  Success!", fg=self.c["green"])
            return

        records = parse_stderr(stderr)
        if not records:
            self.output.insert("end", "Error but could not parse.\n\n", "error")
            self.output.insert("end", stderr)
            self.status.config(text="  Unknown error", fg=self.c["yellow"])
            return

        if stdout.strip():
            self.output.insert("end", "Program Output:\n", "info")
            self.output.insert("end", stdout + "\n\n")

        n = len(records)
        self.output.insert("end", f"ANALYSIS REPORT - {n} Error(s)\n", "title")
        self.output.insert("end", "=" * 50 + "\n\n", "divider")

        for idx, r in enumerate(records, 1):
            self.display_error(idx, r)

        shown = set()
        for r in records:
            fp = r["file"]
            if fp and os.path.exists(fp) and fp not in shown:
                suspects = [rec["line"] for rec in records if rec["file"] == fp]
                self.load_source(fp, suspects)
                shown.add(fp)

        self.status.config(text=f"  {n} error(s) - suspect lines marked", fg=self.c["red"])

    def display_error(self, idx, r):
        out = self.output
        out.insert("end", f"Error #{idx} ", "header")
        if r["root_cause"]:
            out.insert("end", "[ROOT CAUSE] ", "error")
        out.insert("end", "\n" + "-" * 45 + "\n", "divider")

        for label, value, tag in [
            ("Error Type", r["type"], None),
            ("Exception", r["exception"], "error"),
            ("File", r["file"], None),
            ("Line", str(r["line"]), "highlight"),
            ("Function", r["function"], None),
            ("Message", r["message"], "error"),
        ]:
            out.insert("end", f"  {label:14s}: ", "label")
            out.insert("end", f"{value}\n", tag if tag else None)

        out.insert("end", "\n")

        if r["context"]:
            out.insert("end", "  Code Context:\n", "info")
            for lineno, marker, text in r["context"]:
                if marker == ">>>":
                    out.insert("end", f"  >>> {lineno:4d} | {text}\n", "highlight")
                else:
                    out.insert("end", f"      {lineno:4d} | {text}\n", "context")
            out.insert("end", "\n")

        if r["suspect"]:
            out.insert("end", "  SUSPECT ANALYSIS:\n", "suspect")
            for line in r["suspect"].split("\n"):
                s = line.strip()
                if not s:
                    continue
                if s.startswith("Suspect Line:"):
                    out.insert("end", f"    {line}\n", "highlight")
                elif s.startswith("Reason:"):
                    out.insert("end", f"    {line}\n", "error")
                elif s.startswith("Fix:"):
                    out.insert("end", f"    {line}\n", "fix")
                else:
                    out.insert("end", f"    {line}\n", "suspect")

        out.insert("end", "\n" + "=" * 50 + "\n\n", "divider")

    def load_source(self, filepath, suspect_lines):
        sv = self.source_view
        sv.delete("1.0", "end")
        sv.insert("end", f"File: {filepath}\n", "file_header")
        sv.insert("end", "-" * 35 + "\n\n", "line_num")
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except Exception:
            sv.insert("end", "Cannot read file.")
            return
        for i, line in enumerate(lines, 1):
            text = line.rstrip()
            sv.insert("end", f" {i:4d} | ", "line_num")
            if i in suspect_lines:
                sv.insert("end", f"{text}  << SUSPECT\n", "suspect_line")
            else:
                sv.insert("end", f"{text}\n", "normal")

    def browse(self):
        fp = filedialog.askopenfilename(title="Select Python File",
                                         filetypes=[("Python files", "*.py")])
        if fp:
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.insert(0, f'python "{fp}"')

    def clear(self):
        self.output.delete("1.0", "end")
        self.source_view.delete("1.0", "end")
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, "python main.py")
        self.timer.config(text="")
        self.status.config(text="  Ready", fg=self.c["fg3"])

    def save_report(self):
        content = self.output.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Info", "Nothing to save.")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".txt",
                                           filetypes=[("Text files", "*.txt")])
        if fp:
            with open(fp, "w") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Saved to {fp}")

    def show_help(self):
        messagebox.showinfo("Help",
            "1. Type: python yourfile.py\n"
            "2. Click Analyse or press F5\n"
            "3. See suspect lines named\n\n"
            "Features:\n"
            "- Names exact suspect line\n"
            "- Shows reason + fix\n"
            "- Source viewer on right\n"
            "- Save report to file")


def main():
    root = tk.Tk()
    ErrorBotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()