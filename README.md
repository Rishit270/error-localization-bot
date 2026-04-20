# 🛠️ Error Localization Bot

> A Python Tkinter GUI tool that analyzes runtime errors, pinpoints suspect code lines, and suggests fixes — automatically.
---

## 📸 Overview

Error Localization Bot is a desktop debugging assistant built with Python and Tkinter. Paste or load your Python source code, trigger the analyzer, and instantly get a highlighted suspect line along with a suggested fix — no manual stack trace reading required.
---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Runtime Error Detection** | Identifies Python runtime exceptions automatically |
| 🧵 **Stack Trace Analysis** | Parses full tracebacks to isolate the root cause |
| 📍 **Suspect Line Finder** | Highlights the exact line responsible for the error |
| 💡 **Fix Suggestions** | Provides actionable fix hints for common error types |
| 📄 **Source Code Viewer** | Built-in viewer to inspect your code alongside the analysis |
| 💾 **Save Reports** | Export error analysis reports for later reference |
---

## 🧰 Tech Stack

- **Python 3** — Core language
- **Tkinter** — GUI framework (built-in, no install needed)
- **re (Regex)** — Pattern matching for error parsing
- **subprocess** — Script execution and output capture
---

## 📁 Project Structure
error-localization-bot/
│
├── error_bot.py       # Main application logic & GUI
├── README.md          # Project documentation
├── LICENSE            # License file
└── .gitignore         # Git ignore rules
---

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- No external libraries required (uses Python standard library only)

### Installation

```bash
# Clone the repository
git clone https://github.com/Theekshan06/error-localization-bot.git

# Navigate into the project directory
cd error-localization-bot
```

### Run the App

```bash
python error_bot.py
```
---

## 🖥️ How to Use

1. **Launch** the app with `python error_bot.py`
2. **Load or paste** your Python script into the source viewer
3. **Click Analyze** to run the error detection
4. **Review** the highlighted suspect line and suggested fix
5. **Save** the report if needed for documentation or sharing
---

## 🐛 Supported Error Types

- `SyntaxError`, `NameError`, `TypeError`
- `IndexError`, `KeyError`, `AttributeError`
- `ZeroDivisionError` and more common Python runtime exceptions
---
## 👥 Team

This project was built by a team of **3 developers** during a hackathon.

| Member |
|--------|
| Theekshan Mari K |
| Rishi |
| Gokul S |
---

## 📄 License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
---

## 🙌 Contributing

Pull requests are welcome! Fork the repo, make your changes, and open a PR.
---

## 👤 Author

Made with ❤️ — feel free to open an issue for bugs or feature requests.