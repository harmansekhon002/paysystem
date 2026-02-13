# 🚀 How to Run the Payroll System

## ⚡ Super Simple Way (ONE CLICK!)

### On Windows:
1. Go to the project folder
2. **Double-click `start.bat`**
3. Done! App opens in browser automatically! 🎉

### On Mac:
**Option 1:** Double-click `start_payroll.py` (works everywhere!)

**Option 2:** Use Terminal:
```bash
cd "/Users/harmansekhon/Developer/payroll sys2"
chmod +x run.sh
./run.sh
```

---

## 🔧 Manual Way (if you prefer)

### Step 1: Start Backend

**On Mac:**
```bash
cd "/Users/harmansekhon/Developer/payroll sys2/backend"
"/Users/harmansekhon/Developer/payroll sys2/.venv/bin/python" app.py
```

**On Windows:**
```bash
cd "C:\path\to\payroll sys2\backend"
..\\.venv\\Scripts\\python.exe app.py
```

**Keep this terminal/command window open!**

### Step 2: Open Frontend
1. Go to `frontend` folder
2. Double-click `index.html`
3. Use the app in your browser!

---

## 🛑 Stopping the Program

- **One-click method**: Just close the backend window (black terminal/command prompt)
- **Manual method**: Press `Ctrl+C` in the terminal

---

## ✅ Setup Already Done!

- Python environment: ✅
- Dependencies installed: ✅
- Database: ✅ Auto-creates on first run

**Just run it and start adding your shifts!**

---

## ❓ Troubleshooting

**"Port already in use":**
- Mac: `lsof -ti:5001 | xargs kill -9`
- Windows: Find and close the previous Python window

**Application won't start:**
1. Make sure Python 3.7+ is installed
2. Try the manual method above
3. Check that you're in the right folder

**Need help?** Check the full README.md for more details!

---

## Quick Test

1. Click **"Workplaces"** tab
2. Click **"+ Add Workplace"**
3. Enter name and hourly rate
4. Click **"Shifts"** tab  
5. Add a test shift
6. Watch it calculate automatically!

---

**App URL:** Open `frontend/index.html` in any browser  
**API:** Running on http://localhost:5001  
**Database:** `backend/payroll.db` (auto-created)

Need help? Check [QUICKSTART.md](QUICKSTART.md) or [README.md](README.md)
