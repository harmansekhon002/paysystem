# 💰 Payroll & Budget Management System

A modern, easy-to-use payroll calculator and budget manager specifically designed for Australian workers with multiple workplaces. Track shifts, calculate pay rates (weekdays, weekends, public holidays, overtime), and manage fortnight budgets.

## 🌟 Features

### 💼 Payroll Management
- **Multiple Workplaces**: Manage different jobs with different pay rates
- **Smart Pay Calculation**: Automatic calculation for:
  - Weekday rates (base pay)
  - Weekend rates (1.5× default)
  - Public holiday rates (2.5× default)
  - Overtime rates (1.5× after 8 hours default)
- **Shift Tracking**: Full CRUD operations for all your shifts
- **Search & Filter**: Find shifts by date range or workplace
- **CSV Export**: Download shift records for tax purposes
- **Fortnight Summary**: See your earnings for the current pay period

### 💰 Budget Management
- **Expense Tracking**: Categorize expenses (Rent, Groceries, Utilities, etc.)
- **Recurring Expenses**: Mark expenses that repeat every fortnight
- **Budget Overview**: See income vs. expenses at a glance
- **Due Date Tracking**: Never miss a payment
- **Smart Calculations**: See exactly what's left after expenses and goals

### 🎯 Goals & Savings System
- **Financial Goals**: Set targets (college fees, emergency fund, holiday, etc.)
- **Auto-Allocation**: Automatically save money each fortnight
- **Progress Tracking**: Visual progress bars and percentage complete
- **Priority System**: Organize goals by importance
- **Manual Contributions**: Add extra money anytime
- **Deadline Tracking**: Set target dates for your goals
- **Contribution History**: See every deposit made to your goals

### 📊 Dashboard & Analytics
- **Quick Statistics**: Total earned, hours worked, average hourly rate
- **This Week Summary**: Current week's shifts and earnings
- **Goal Progress**: See top active goals at a glance
- **Financial Breakdown**: Earned → Expenses → Goals = Available Money
- **Recent Activity**: Latest shifts and expenses

### 🎨 Modern UI
- Clean, modern design with gradient backgrounds
- Responsive layout for mobile and desktop
- Intuitive navigation with tabs
- Real-time calculations
- Easy-to-use modals for data entry
- Animated progress bars and transitions

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Navigate to the project directory**
```bash
cd "/Users/harmansekhon/Developer/payroll sys2"
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

### Running the Application

#### Quick Start (Recommended)
```bash
cd "/Users/harmansekhon/Developer/payroll sys2"
chmod +x run.sh
./run.sh
```
The application will start automatically and open in your browser!

#### Manual Start

1. **Start the backend server**
```bash
cd backend
"/Users/harmansekhon/Developer/payroll sys2/.venv/bin/python" app.py
```
The server will start on `http://localhost:5001`

2. **Open the frontend**
   - Open `frontend/index.html` in your web browser

## 📖 How to Use

### 1. Add Your Workplaces
- Click on the "Workplaces" tab
- Click "+ Add Workplace"
- Enter:
  - Workplace name
  - Base hourly rate (AUD)
  - Weekend multiplier (default 1.5×)
  - Public holiday multiplier (default 2.5×)
  - Overtime multiplier (default 1.5×)
  - Overtime threshold (hours before overtime kicks in)

### 2. Record Your Shifts
- Go to the "Shifts" tab
- Click "+ Add Shift"
- Select workplace, date, start time, end time
- The system automatically calculates:
  - Total hours worked
  - Shift type (weekday/weekend/public holiday)
  - Overtime if applicable
  - Total pay

### 3. Manage Your Budget
- Navigate to "Budget" tab
- Click "+ Add Expense"
- Add expenses like rent, groceries, etc.
- Mark recurring expenses to include in fortnight calculations

### 4. Set Financial Goals
- Navigate to "Goals" tab
- Click "+ Add Goal"
- Example goal:
  - Name: "College Fees"
  - Target Amount: $15,000
  - Auto-save per fortnight: $250
  - Priority: High
  - Deadline: December 2027
- System auto-allocates money each fortnight
- Make manual contributions anytime!

### 5. Use Advanced Features

#### Search Shifts
- Go to Shifts tab
- Use search panel to filter by:
  - Date range (from/to)
  - Specific workplace
- Click "Clear" to reset filters

#### Export Data
- Click "Export to CSV" button in Shifts tab
- Downloads spreadsheet with all shift records
- Perfect for tax time!

#### View Statistics
- Dashboard shows quick stats:
  - Total money earned (all time)
  - Total hours worked
  - Average hourly rate
  - Total saved toward goals
  - This week's shifts and earnings

### 6. Monitor Your Finances
- Dashboard provides complete breakdown:
  - **Total Earned**: All shift income
  - **Expenses**: Bills and recurring costs
  - **Goals**: Auto-saved + manual contributions
  - **Available**: What's left to spend!

## 🗂️ Project Structure

```
payroll sys2/
├── backend/
│   ├── app.py              # Flask API server
│   └── payroll.db          # SQLite database (auto-created)
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── styles.css          # Styling
│   └── app.js              # Frontend logic
└── requirements.txt        # Python dependencies
```

## 🎯 Key Features Explained

### Australian Pay Rates
The system uses standard Australian penalty rates:
- **Weekend**: 1.5× base rate (configurable)
- **Public Holidays**: 2.5× base rate (configurable)
- **Overtime**: 1.5× after 8 hours (configurable)

### Public Holidays 2026
Pre-configured Australian public holidays:
- New Year's Day, Australia Day
- Easter (Good Friday, Easter Saturday, Easter Monday)
- ANZAC Day
- Queen's Birthday
- Christmas, Boxing Day

### Fortnight Calculations
- Automatically calculates current pay period
- Shows total earned, hours worked, and net income
- Includes recurring expenses in budget calculations
- **Financial Breakdown Formula:**
  ```
  Available Money = Total Earned - Total Expenses - Total Goals Saved
  ```
- Goals are auto-allocated at the start of each fortnight
- Manual contributions count toward goal totals immediately

## 🛠️ API Endpoints

### Workplaces
- `GET /api/workplaces` - List all workplaces
- `POST /api/workplaces` - Create workplace
- `GET /api/workplaces/:id` - Get workplace details
- `PUT /api/workplaces/:id` - Update workplace
- `DELETE /api/workplaces/:id` - Delete workplace

### Shifts
- `GET /api/shifts` - List all shifts
- `POST /api/shifts` - Create shift (auto-calculates pay)
- `GET /api/shifts/:id` - Get shift details
- `PUT /api/shifts/:id` - Update shift
- `DELETE /api/shifts/:id` - Delete shift

### Expenses
- `GET /api/expenses` - List all expenses
- `POST /api/expenses` - Create expense
- `GET /api/expenses/:id` - Get expense details
- `PUT /api/expenses/:id` - Update expense
- `DELETE /api/expenses/:id` - Delete expense

### Goals
- `GET /api/goals` - List all goals
- `POST /api/goals` - Create goal
- `GET /api/goals/:id` - Get goal details
- `PUT /api/goals/:id` - Update goal
- `DELETE /api/goals/:id` - Delete goal
- `POST /api/goals/:id/contribute` - Add manual contribution

### Analytics & Data
- `GET /api/summary/fortnight` - Current fortnight summary with goals
- `GET /api/stats` - Overall statistics (earned, hours, rates, goals)
- `GET /api/export/shifts` - Export all shifts to CSV
- `GET /api/search/shifts?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&workplace_id=1` - Search shifts

## ✅ Recently Added Features

- ✨ **Goals & Savings System**: Track financial goals with auto-allocation
- 📊 **Statistics Dashboard**: Quick stats on earnings, hours, and rates
- 🔍 **Search & Filter**: Find shifts by date range or workplace
- 📥 **CSV Export**: Download shift records for tax purposes
- 📈 **Progress Tracking**: Visual progress bars for goals
- 💰 **Smart Financial Breakdown**: See Available = Earned - Expenses - Goals

## 💡 Suggested Future Features

1. **Tax Calculator**: Automatic tax withholding calculations (Australian tax brackets)
2. **Superannuation Tracker**: Track employer super contributions (11.5% as of 2024)
3. **PDF Reports**: Professional formatted reports for record keeping
4. **Shift Reminders**: Email/SMS notifications for upcoming shifts
5. **Leave Tracker**: Track annual leave, sick leave entitlements (Fair Work compliant)
6. **Chart Visualizations**: Interactive graphs for earnings and expenses over time
7. **Multi-Currency Support**: For international work or freelancing
8. **Cloud Backup**: Automatic backup to Google Drive/Dropbox
9. **Dark Mode**: Eye-friendly theme for night use
10. **Mobile App**: React Native or Flutter mobile version
11. **Bank Integration**: Connect to banks and auto-categorize expenses
12. **Shift Templates**: Quickly add recurring shifts with one click
13. **Multi-User Support**: For couples managing joint finances
14. **Receipt Scanner**: OCR to capture expenses from photos
15. **Budget Alerts**: Notifications when approaching budget limits

## 🐛 Troubleshooting

**Backend won't start:**
- Make sure Python 3.7+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check if port 5001 is already in use (changed from 5000 due to macOS AirPlay)

**Frontend not connecting to backend:**
- Ensure backend is running on port 5001
- Check browser console for CORS errors
- Try refreshing the page

**Goals not showing on dashboard:**
- Add at least one goal first
- Refresh the page
- Check browser console for errors

**CSV export not working:**
- Ensure you have shifts recorded first
- Check browser's download settings
- Try a different browser

**Database errors:**
- Delete `backend/payroll.db` and restart the backend (it will recreate with fresh tables)
- Check file permissions on the backend folder

## 🔒 Security Notes

This is a **single-user local application**. For production use:
- Add authentication
- Use environment variables for configuration
- Implement proper data validation
- Add HTTPS support
- Use a production database (PostgreSQL)

## 📝 License

This project is free to use and modify for personal use.

---

Made with ❤️ for Australian workers managing multiple jobs!
