# 🧠 AZ-204 Ultimate Simulator

An advanced **Streamlit-based exam simulator** designed to help you prepare for the **Microsoft AZ-204: Developing Solutions for Microsoft Azure** certification exam.

This application provides a realistic practice environment with progress tracking, smart filtering, case study support, community statistics, and more.

---

## 🚀 Features

### 🎯 Practice Modes

- **Practice (Random)** – Randomized questions based on selected filters
- **Sequential** – Go through questions in order

### 🧠 Smart Question Filtering

Choose what to include in your session:

- 🆕 Unseen Questions
- ❌ Mistakes (Review)
- ✅ Mastered (Re-check)

The question pool is generated once per session to ensure stability.

---

### 📊 Progress Tracking (Persistent)

- Tracks **Unseen / Mastered / Mistakes**
- Auto-saves progress to `user_progress.json`
- Displays completion percentage
- Community voting statistics (if available)

---

### 📚 Case Study Support

- Scenario-based questions
- Expandable scenario context
- Visual identification for case studies

---

### 🖼️ Visual & Interactive Questions

- Embedded images (if available)
- PDF source snapshots
- Support for Visual/Interactive question types

---

### 📝 Answer Types Supported

- Single-choice (Radio buttons)
- Multiple-choice (Checkboxes, auto-detected)
- Visual reveal answers

---

### 💬 Community Section

- Explanation tab
- Embedded solutions (code)
- PDF Source tab
- Comments with user points
- Vote distribution statistics

---

## 📁 Project Structure

```
.
├── app.py                  # Main Streamlit application
├── config.py               # Configuration file (defines OUTPUT_JSON_FILE)
├── main.py                 # Script that generates the JSON database
├── user_progress.json      # Auto-generated progress tracking file
├── questions.json          # Generated questions database
└── assets/                 # Images / PDF snapshots (optional)
```

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/az-204-simulator.git
cd az-204-simulator
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, install manually:

```bash
pip install streamlit
```

---

## ▶️ Running the Application

If your JSON file is not generated yet:

```bash
python main.py
```

Then start the simulator:

```bash
python -m streamlit run app.py
```

The app will open in your browser.

---

## 🔄 Session Reset

You can:

- Regenerate the question pool
- Reset session filters
- Manually override question status

All changes are automatically saved.

---

## 🧠 How Status Works

Each question can have one of the following states:

| Status    | Meaning              |
| --------- | -------------------- |
| Unseen    | Not answered yet     |
| Correct   | Answered correctly   |
| Incorrect | Answered incorrectly |

Status can be:

- Automatically updated after answering
- Manually overridden via dropdown

---

## 📌 Notes

- If the JSON file is missing, run `main.py` to generate it.
- The simulator requires a properly structured JSON file.
- Image paths must exist locally to display properly.
- Progress is stored locally in `user_progress.json`.

---

## 🎯 Goal

The purpose of this project is to provide a **focused, distraction-free, high-performance practice environment** for AZ-204 candidates.

---

## 📜 License

This project is intended for educational purposes.

---

## 💡 Future Improvements

- Timed exam mode
- Performance analytics dashboard
- Cloud-based progress sync
- Leaderboard system
- Dark/Light theme toggle

---

If you find this project useful, feel free to ⭐ the repository.
