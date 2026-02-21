const API_URL = window.API_URL || 'http://localhost:5001/api';

// State
let workplaces = [];
let shifts = [];
let expenses = [];
let goals = [];
let fortnightSummary = {};
let stats = {};
let currentCalendarMonth = new Date();
let selectedShifts = new Set();
let selectedExpenses = new Set();
let selectedGoals = new Set();
let draggedGoalId = null;

// ============ AUTHENTICATION ============
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('authError');
    
    try {
        const response = await authFetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Login failed');
        }
        
        // Store token and user
        setAuthToken(data.token);
        setStoredUser(data.user);
        
        // Hide auth screen and load app
        document.getElementById('authScreen').classList.remove('active');
        await loadAllData();
        setupEventListeners();
        errorEl.classList.remove('show');
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.classList.add('show');
    }
}

async function handleSignup(event) {
    event.preventDefault();
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const errorEl = document.getElementById('authError');
    
    try {
        const response = await authFetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, name })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Signup failed');
        }
        
        // Store token and user
        setAuthToken(data.token);
        setStoredUser(data.user);
        
        // Hide auth screen and load app
        document.getElementById('authScreen').classList.remove('active');
        await loadAllData();
        setupEventListeners();
        errorEl.classList.remove('show');
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.classList.add('show');
    }
}

function switchAuthTab(tab) {
    const loginTab = document.getElementById('loginTab');
    const signupTab = document.getElementById('signupTab');
    
    if (tab === 'login') {
        loginTab.classList.add('active');
        signupTab.classList.remove('active');
    } else {
        signupTab.classList.add('active');
        loginTab.classList.remove('active');
    }
    
    document.getElementById('authError').classList.remove('show');
}

function handleLogout() {
    clearAuth();
    document.getElementById('authScreen').classList.add('active');
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('signupName').value = '';
    document.getElementById('signupEmail').value = '';
    document.getElementById('signupPassword').value = '';
}

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    if (isLoggedIn()) {
        document.getElementById('authScreen').classList.remove('active');
        await loadAllData();
        setupEventListeners();
    } else {
        document.getElementById('authScreen').classList.add('active');
    }
});

// Load all data
async function loadAllData() {
    await Promise.all([
        loadWorkplaces(),
        loadShifts(),
        loadExpenses(),
        loadGoals(),
        loadFortnightSummary(),
        loadStats()
    ]);
    renderAll();
}

// API Calls with Auth Header
function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
    };
}
// Smart fetch with auto-auth headers
async function authFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    const token = getAuthToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(url, { ...options, headers });
        
        // If 401, user is not authenticated
        if (response.status === 401) {
            clearAuth();
            handleLogout();
            throw new Error('Session expired. Please login again.');
        }
        
        return response;
    } catch (error) {
        // Network error or other fetch issues
        console.error('Fetch error:', error);
        throw error;
    }
}

async function loadWorkplaces() {
    try {
        const response = await authFetch(`${API_URL}/workplaces`);
        workplaces = await response.json();
    } catch (error) {
        console.error('Error loading workplaces:', error);
    }
}

async function loadShifts() {
    try {
        const response = await authFetch(`${API_URL}/shifts`);
        shifts = await response.json();
    } catch (error) {
        console.error('Error loading shifts:', error);
    }
}

async function loadExpenses() {
    try {
        const response = await authFetch(`${API_URL}/expenses`);
        expenses = await response.json();
    } catch (error) {
        console.error('Error loading expenses:', error);
    }
}

async function loadGoals() {
    try {
        const response = await authFetch(`${API_URL}/goals`);
        goals = await response.json();
    } catch (error) {
        console.error('Error loading goals:', error);
    }
}

async function loadFortnightSummary() {
    try {
        const response = await authFetch(`${API_URL}/summary/fortnight`);
        fortnightSummary = await response.json();
    } catch (error) {
        console.error('Error loading fortnight summary:', error);
    }
}

async function loadStats() {
    try {
        const response = await authFetch(`${API_URL}/stats`);
        stats = await response.json();
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Render functions
function renderAll() {
    renderFortnightSummary();
    renderStats();
    renderDashboard();
    renderWeeklyComparison();
    renderExpenseBreakdown();
    renderWorkAnalysis();
    renderSavingsAnalysis();
    renderProductivityMetrics();
    renderUsageStats();
    renderGoalsStatus();
    renderShiftsList();
    renderWorkplacesList();
    renderExpensesList();
    renderGoalsList();
    populateSearchWorkplaces();
    renderSpendingChart();
    renderIncomeChart();
    renderShiftCalendar();
}

function renderStats() {
    const statsHtml = `
        <div class="stat-box">
            <div class="stat-value">$${(stats.total_earned || 0).toFixed(0)}</div>
            <div class="stat-label">Total Earned</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">${(stats.total_hours || 0).toFixed(0)}h</div>
            <div class="stat-label">Total Hours</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">$${(stats.average_rate || 0).toFixed(2)}</div>
            <div class="stat-label">Avg Rate/Hour</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">$${(stats.goals_saved || 0).toFixed(0)}</div>
            <div class="stat-label">Goals Saved</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">${stats.this_week?.shifts || 0}</div>
            <div class="stat-label">This Week's Shifts</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">$${(stats.this_week?.earned || 0).toFixed(0)}</div>
            <div class="stat-label">This Week Earned</div>
        </div>
    `;
    document.getElementById('quickStats').innerHTML = statsHtml;
}

function renderFortnightSummary() {
    document.getElementById('fortnightEarned').textContent = 
        `$${(fortnightSummary.total_earned || 0).toFixed(2)}`;
    document.getElementById('fortnightExpenses').textContent = 
        `-$${(fortnightSummary.total_expenses || 0).toFixed(2)}`;
    document.getElementById('fortnightGoals').textContent = 
        `-$${(fortnightSummary.goal_allocations || 0).toFixed(2)}`;
    document.getElementById('netIncome').textContent = 
        `$${(fortnightSummary.net_after_goals || 0).toFixed(2)}`;
}

function renderDashboard() {
    // Recent shifts (last 5)
    const recentShifts = shifts.slice(0, 5);
    const recentShiftsHtml = recentShifts.length > 0 ? recentShifts.map(shift => `
        <div class="list-item">
            <div>
                <div class="list-item-title">${shift.workplace_name}</div>
                <div class="list-item-subtitle">
                    ${formatDate(shift.date)} • ${shift.start_time} - ${shift.end_time}
                    <span class="badge badge-${shift.shift_type.split('_')[0]}">${formatShiftType(shift.shift_type)}</span>
                </div>
            </div>
            <div class="list-item-amount">$${shift.total_pay.toFixed(2)}</div>
        </div>
    `).join('') : '<div class="empty-state"><div class="empty-state-icon">📅</div><div class="empty-state-text">No shifts recorded yet</div></div>';
    
    document.getElementById('recentShifts').innerHTML = recentShiftsHtml;
    
    // Financial Snapshot - Show this week's activity and top goals
    const thisWeekShifts = stats.this_week?.shifts || 0;
    const thisWeekEarned = stats.this_week?.earned || 0;
    const thisWeekHours = stats.this_week?.hours || 0;
    const totalAvailable = fortnightSummary.net_after_goals || 0;
    
    // Get top 3 active goals sorted by priority
    const topGoals = goals
        .filter(g => g.current_amount < g.target_amount)
        .sort((a, b) => {
            const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        })
        .slice(0, 3);
    
    const budgetHtml = `
        <div class="budget-item">
            <span class="budget-item-label">Available Money</span>
            <span class="budget-item-amount" style="color: var(--success);">$${totalAvailable.toFixed(2)}</span>
        </div>
        <div class="budget-item">
            <span class="budget-item-label">This Week: ${thisWeekShifts} Shifts</span>
            <span class="budget-item-amount">$${thisWeekEarned.toFixed(2)}</span>
        </div>
        <div class="budget-item">
            <span class="budget-item-label">Hours This Week</span>
            <span class="budget-item-amount">${thisWeekHours.toFixed(1)}h</span>
        </div>
        ${topGoals.length > 0 ? `
            <div style="margin-top: 15px; padding-top: 15px; border-top: 2px solid var(--border); color: var(--gray); font-size: 12px; font-weight: 600;">
                Active Goals
            </div>
            ${topGoals.map(goal => `
                <div class="budget-item">
                    <span class="budget-item-label">${goal.name}</span>
                    <span class="budget-item-amount">${goal.progress.toFixed(0)}%</span>
                </div>
            `).join('')}
        ` : ''}
    `;
    document.getElementById('budgetOverview').innerHTML = budgetHtml;
}

function renderWeeklyComparison() {
    // Show last 2 weeks comparison
    const today = new Date();
    const startOfThisWeek = new Date(today);
    startOfThisWeek.setDate(today.getDate() - today.getDay());
    
    const startOfLastWeek = new Date(startOfThisWeek);
    startOfLastWeek.setDate(startOfThisWeek.getDate() - 7);
    
    const thisWeekShifts = shifts.filter(s => {
        const shiftDate = new Date(s.date);
        return shiftDate >= startOfThisWeek;
    });
    
    const lastWeekShifts = shifts.filter(s => {
        const shiftDate = new Date(s.date);
        return shiftDate >= startOfLastWeek && shiftDate < startOfThisWeek;
    });
    
    const thisWeekEarned = thisWeekShifts.reduce((sum, s) => sum + s.total_pay, 0);
    const lastWeekEarned = lastWeekShifts.reduce((sum, s) => sum + s.total_pay, 0);
    const difference = thisWeekEarned - lastWeekEarned;
    const percentChange = lastWeekEarned > 0 ? ((difference / lastWeekEarned) * 100) : 0;
    
    const html = `
        <div class="weekly-item">
            <div class="weekly-item-label">This Week</div>
            <div class="weekly-item-value">$${thisWeekEarned.toFixed(2)}</div>
            <div style="font-size: 12px; color: var(--gray); margin-top: 4px;">${thisWeekShifts.length} shifts</div>
        </div>
        <div class="weekly-item">
            <div class="weekly-item-label">Last Week</div>
            <div class="weekly-item-value">$${lastWeekEarned.toFixed(2)}</div>
            <div style="font-size: 12px; color: var(--gray); margin-top: 4px;">${lastWeekShifts.length} shifts</div>
        </div>
        <div class="weekly-item" style="border-left-color: ${difference >= 0 ? 'var(--success)' : 'var(--danger)'};background: ${difference >= 0 ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)'};">
            <div class="weekly-item-label">Change</div>
            <div class="weekly-item-value" style="color: ${difference >= 0 ? 'var(--success)' : 'var(--danger)'};">
                ${difference >= 0 ? '+' : ''}$${difference.toFixed(2)} (${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(0)}%)
            </div>
        </div>
    `;
    
    const container = document.getElementById('weeklyComparison');
    if (container) {
        container.innerHTML = html;
    }
}

function renderExpenseBreakdown() {
    // Group expenses by category
    const expensesByCategory = {};
    
    expenses.forEach(expense => {
        if (!expensesByCategory[expense.category]) {
            expensesByCategory[expense.category] = { total: 0, count: 0, recurring: false };
        }
        expensesByCategory[expense.category].total += expense.amount;
        expensesByCategory[expense.category].count += 1;
        if (expense.recurring) {
            expensesByCategory[expense.category].recurring = true;
        }
    });
    
    let html = '';
    if (Object.keys(expensesByCategory).length > 0) {
        // Sort by amount descending
        const sorted = Object.entries(expensesByCategory)
            .sort((a, b) => b[1].total - a[1].total)
            .slice(0, 5); // Show top 5 categories
        
        html = sorted.map(([category, data]) => `
            <div class="expense-item">
                <div>
                    <div class="expense-category">${category}</div>
                    <div class="expense-meta">
                        <span>${data.count} entries</span>
                        ${data.recurring ? '<span style="color: var(--info);">Recurring</span>' : ''}
                    </div>
                </div>
                <div class="expense-amount">-$${data.total.toFixed(2)}</div>
            </div>
        `).join('');
    } else {
        html = '<div class="empty-message">No expenses recorded yet</div>';
    }
    
    const container = document.getElementById('expenseBreakdown');
    if (container) {
        container.innerHTML = html;
    }
}

function renderWorkAnalysis() {
    // Calculate work statistics
    const totalShifts = shifts.length;
    const totalHours = shifts.reduce((sum, s) => sum + (s.hours || 0), 0);
    const totalEarnings = shifts.reduce((sum, s) => sum + s.total_pay, 0);
    const averageHourlyRate = totalHours > 0 ? totalEarnings / totalHours : 0;
    
    // Find highest earning shift
    let bestDay = { date: 'N/A', earned: 0 };
    if (shifts.length > 0) {
        const shiftsByDate = {};
        shifts.forEach(s => {
            if (!shiftsByDate[s.date]) {
                shiftsByDate[s.date] = 0;
            }
            shiftsByDate[s.date] += s.total_pay;
        });
        const bestDate = Object.entries(shiftsByDate).sort((a, b) => b[1] - a[1])[0];
        bestDay = { date: formatDate(bestDate[0]), earned: bestDate[1] };
    }
    
    const html = `
        <div class="work-stat-card">
            <div class="work-stat-label">💵 Avg Hourly Rate</div>
            <div class="work-stat-value">$${averageHourlyRate.toFixed(2)}</div>
            <div class="work-stat-subtext">${totalShifts} shifts, ${totalHours.toFixed(1)}h total</div>
        </div>
        <div class="work-stat-card">
            <div class="work-stat-label">🚀 Best Earning Day</div>
            <div class="work-stat-value">$${bestDay.earned.toFixed(2)}</div>
            <div class="work-stat-subtext">${bestDay.date}</div>
        </div>
        <div class="work-stat-card">
            <div class="work-stat-label">📊 Avg Per Shift</div>
            <div class="work-stat-value">$${totalShifts > 0 ? (totalEarnings / totalShifts).toFixed(2) : '0.00'}</div>
            <div class="work-stat-subtext">${(totalHours / totalShifts).toFixed(1)}h per shift</div>
        </div>
        <div class="work-stat-card">
            <div class="work-stat-label">⏱️ Avg Shift Length</div>
            <div class="work-stat-value">${totalShifts > 0 ? (totalHours / totalShifts).toFixed(1) : '0'}h</div>
            <div class="work-stat-subtext">${totalShifts} total shifts</div>
        </div>
    `;
    
    const container = document.getElementById('workAnalysis');
    if (container) {
        container.innerHTML = html;
    }
}

function renderSavingsAnalysis() {
    // Calculate savings vs spending
    const totalEarnings = shifts.reduce((sum, s) => sum + s.total_pay, 0);
    const totalExpenses = expenses.reduce((sum, e) => sum + e.amount, 0);
    const totalGoalsSaved = goals.reduce((sum, g) => sum + g.current_amount, 0);
    const totalSpent = totalExpenses - totalGoalsSaved;
    const netAfterExpenses = totalEarnings - totalExpenses;
    
    // Calculate percentages
    const earningsPercent = totalEarnings > 0 ? 100 : 0;
    const goalPercent = totalEarnings > 0 ? (totalGoalsSaved / totalEarnings) * 100 : 0;
    const spentPercent = totalEarnings > 0 ? ((totalSpent) / totalEarnings) * 100 : 0;
    
    const html = `
        <div class="savings-bar">
            <div class="savings-bar-label">💰 Earnings</div>
            <div class="savings-bar-container">
                <div class="savings-bar-fill" style="width: 100%; background: var(--success);">
                    $${totalEarnings.toFixed(2)}
                </div>
            </div>
        </div>
        <div class="savings-bar">
            <div class="savings-bar-label">🎯 Goals</div>
            <div class="savings-bar-container">
                <div class="savings-bar-fill" style="width: ${goalPercent}%; background: var(--secondary);">
                    ${goalPercent > 15 ? '$' + totalGoalsSaved.toFixed(2) : ''}
                </div>
            </div>
        </div>
        <div class="savings-bar">
            <div class="savings-bar-label">💸 Expenses</div>
            <div class="savings-bar-container">
                <div class="savings-bar-fill" style="width: ${spentPercent}%; background: var(--danger);">
                    ${spentPercent > 15 ? '$' + totalSpent.toFixed(2) : ''}
                </div>
            </div>
        </div>
        <div class="savings-summary">
            <div class="savings-summary-item">
                <div class="savings-summary-label">Saved in Goals</div>
                <div class="savings-summary-value" style="color: var(--secondary);">$${totalGoalsSaved.toFixed(2)}</div>
            </div>
            <div class="savings-summary-item">
                <div class="savings-summary-label">Net Available</div>
                <div class="savings-summary-value" style="${netAfterExpenses >= 0 ? 'color: var(--success)' : 'color: var(--danger)'}">
                    ${netAfterExpenses >= 0 ? '+' : ''}$${netAfterExpenses.toFixed(2)}
                </div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('savingsAnalysis');
    if (container) {
        container.innerHTML = html;
    }
}

function renderProductivityMetrics() {
    if (shifts.length === 0) {
        document.getElementById('productivityMetrics').innerHTML = '<div class="empty-message">No shifts to analyze</div>';
        return;
    }
    
    // Calculate metrics
    const totalShifts = shifts.length;
    const totalHours = shifts.reduce((sum, s) => sum + s.hours, 0);
    const avgHoursPerShift = totalHours / totalShifts;
    
    // Find most active workplace
    const workplaceMap = {};
    shifts.forEach(shift => {
        workplaceMap[shift.workplace_id] = (workplaceMap[shift.workplace_id] || 0) + 1;
    });
    const mostActiveId = Object.keys(workplaceMap).reduce((a, b) => 
        workplaceMap[a] > workplaceMap[b] ? a : b
    );
    const mostActiveWorkplace = shifts.find(s => s.workplace_id == mostActiveId)?.workplace_name || 'N/A';
    const mostActiveCount = workplaceMap[mostActiveId];
    
    // Consistency score (shifts per week on average)
    const oldestShift = shifts[shifts.length - 1];
    const newestShift = shifts[0];
    const daysActive = (new Date(newestShift.date) - new Date(oldestShift.date)) / (1000 * 60 * 60 * 24) + 1;
    const weeksActive = Math.max(daysActive / 7, 1);
    const shiftsPerWeek = totalShifts / weeksActive;
    const consistencyScore = Math.min(shiftsPerWeek / 3 * 100, 100); // 3 shifts/week = 100% score
    
    // Busy vs slow periods
    const weekMap = {};
    shifts.forEach(shift => {
        const date = new Date(shift.date);
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        const weekKey = weekStart.toISOString().split('T')[0];
        weekMap[weekKey] = (weekMap[weekKey] || 0) + shift.hours;
    });
    const avgHoursPerWeek = Object.values(weekMap).reduce((a, b) => a + b, 0) / Object.keys(weekMap).length;
    
    let html = '';
    html += '<div class="metric-card">';
    html += '<div class="metric-label">Total Shifts</div>';
    html += '<div class="metric-value">' + totalShifts + '</div>';
    html += '<div class="metric-sub">' + avgHoursPerShift.toFixed(1) + 'h per shift</div>';
    html += '</div>';
    html += '<div class="metric-card">';
    html += '<div class="metric-label">Most Active</div>';
    html += '<div class="metric-value">' + mostActiveWorkplace + '</div>';
    html += '<div class="metric-sub">' + mostActiveCount + ' shifts</div>';
    html += '</div>';
    html += '<div class="metric-card">';
    html += '<div class="metric-label">Consistency</div>';
    html += '<div class="metric-value">' + consistencyScore.toFixed(0) + '%</div>';
    html += '<div class="metric-sub">' + shiftsPerWeek.toFixed(1) + ' shifts/week</div>';
    html += '</div>';
    html += '<div class="metric-card">';
    html += '<div class="metric-label">Weekly Average</div>';
    html += '<div class="metric-value">' + avgHoursPerWeek.toFixed(1) + 'h</div>';
    html += '<div class="metric-sub">per week</div>';
    html += '</div>';
    
    const container = document.getElementById('productivityMetrics');
    if (container) container.innerHTML = html;
}

function renderUsageStats() {
    const stats = {
        totalShifts: shifts.length,
        totalExpenses: expenses.length,
        totalGoals: goals.length,
        totalWorkplaces: workplaces.length,
        totalEarned: shifts.reduce((sum, s) => sum + s.total_pay, 0),
        totalSpent: expenses.reduce((sum, e) => sum + e.amount, 0),
        totalSaved: goals.reduce((sum, g) => sum + g.current_amount, 0)
    };
    
    // Calculate active months
    const allDates = [
        ...shifts.map(s => new Date(s.date)),
        ...expenses.map(e => new Date(e.due_date || new Date())),
        ...goals.map(g => new Date(g.deadline || new Date()))
    ].filter(d => d.toString() !== 'Invalid Date');
    
    const months = new Set(allDates.map(d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0')));
    
    let html = '';
    html += '<div class="stats-grid">';
    html += '<div class="stats-box"><div class="stats-icon">📊</div><div class="stats-text"><div class="stats-number">' + stats.totalShifts + '</div><div class="stats-label">Total Shifts</div></div></div>';
    html += '<div class="stats-box"><div class="stats-icon">💼</div><div class="stats-text"><div class="stats-number">' + stats.totalWorkplaces + '</div><div class="stats-label">Workplaces</div></div></div>';
    html += '<div class="stats-box"><div class="stats-icon">💸</div><div class="stats-text"><div class="stats-number">' + stats.totalExpenses + '</div><div class="stats-label">Expenses</div></div></div>';
    html += '<div class="stats-box"><div class="stats-icon">🎯</div><div class="stats-text"><div class="stats-number">' + stats.totalGoals + '</div><div class="stats-label">Goals</div></div></div>';
    html += '<div class="summary-stat">';
    html += '<div class="summary-stat-row"><span class="summary-label">Total Earned</span><span class="summary-value earned">$' + stats.totalEarned.toFixed(2) + '</span></div>';
    html += '<div class="summary-stat-row"><span class="summary-label">Total Spent</span><span class="summary-value spent">-$' + stats.totalSpent.toFixed(2) + '</span></div>';
    html += '<div class="summary-stat-row"><span class="summary-label">Total Saved</span><span class="summary-value saved">$' + stats.totalSaved.toFixed(2) + '</span></div>';
    html += '<div class="summary-stat-row"><span class="summary-label">Active Months</span><span class="summary-value">' + Math.max(months.size, 1) + ' months</span></div>';
    html += '</div></div>';
    
    const container = document.getElementById('usageStats');
    if (container) container.innerHTML = html;
}

// ============ SORTING FUNCTIONS ============
function sortAndRenderShifts() {
    const sortValue = document.getElementById('shiftsSort').value;
    const [field, order] = sortValue.split('-');
    
    shifts.sort((a, b) => {
        let compareA, compareB;
        
        if (field === 'date') {
            compareA = new Date(a.date);
            compareB = new Date(b.date);
        } else if (field === 'pay') {
            compareA = a.total_pay;
            compareB = b.total_pay;
        } else if (field === 'hours') {
            compareA = a.hours;
            compareB = b.hours;
        }
        
        if (order === 'asc') {
            return compareA > compareB ? 1 : -1;
        } else {
            return compareA < compareB ? 1 : -1;
        }
    });
    
    renderShiftsList();
}

function sortAndRenderExpenses() {
    const sortValue = document.getElementById('expensesSort').value;
    const [field, order] = sortValue.split('-');
    
    expenses.sort((a, b) => {
        let compareA, compareB;
        
        if (field === 'date') {
            compareA = new Date(a.due_date || a.created_at || '1970-01-01');
            compareB = new Date(b.due_date || b.created_at || '1970-01-01');
        } else if (field === 'amount') {
            compareA = a.amount;
            compareB = b.amount;
        } else if (field === 'category') {
            compareA = a.category.toLowerCase();
            compareB = b.category.toLowerCase();
            return compareA > compareB ? 1 : -1;
        }
        
        if (order === 'asc') {
            return compareA > compareB ? 1 : -1;
        } else {
            return compareA < compareB ? 1 : -1;
        }
    });
    
    renderExpensesList();
}

function sortAndRenderGoals() {
    const sortValue = document.getElementById('goalsSort').value;
    const [field, order] = sortValue.split('-');
    
    goals.sort((a, b) => {
        let compareA, compareB;
        
        if (field === 'priority') {
            const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
            compareA = priorityOrder[a.priority] || 999;
            compareB = priorityOrder[b.priority] || 999;
            return compareA - compareB;
        } else if (field === 'deadline') {
            compareA = new Date(a.deadline || '2099-12-31');
            compareB = new Date(b.deadline || '2099-12-31');
            return compareA - compareB;
        } else if (field === 'progress') {
            compareA = a.progress || 0;
            compareB = b.progress || 0;
        } else if (field === 'target') {
            compareA = a.target_amount || 0;
            compareB = b.target_amount || 0;
        }
        
        if (order === 'asc') {
            return compareA > compareB ? 1 : -1;
        } else {
            return compareA < compareB ? 1 : -1;
        }
    });
    
    renderGoalsList();
}

function renderShiftsList() {
    const shiftsHtml = shifts.length > 0 ? `
        <table>
            <thead>
                <tr>
                    <th style="width: 40px;"><input type="checkbox" id="selectAllShiftsTable" onchange="toggleSelectAll('shifts')" ${selectedShifts.size === shifts.length && shifts.length > 0 ? 'checked' : ''}></th>
                    <th>Date</th>
                    <th>Workplace</th>
                    <th>Hours</th>
                    <th>Time</th>
                    <th>Type</th>
                    <th>Pay</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${shifts.map(shift => `
                    <tr ${selectedShifts.has(shift.id) ? 'class="selected-row"' : ''}>
                        <td><input type="checkbox" ${selectedShifts.has(shift.id) ? 'checked' : ''} onchange="toggleSelection('shifts', ${shift.id})"></td>
                        <td>${formatDate(shift.date)}</td>
                        <td>${shift.workplace_name}</td>
                        <td>${shift.hours.toFixed(1)}h</td>
                        <td>${shift.start_time} - ${shift.end_time}</td>
                        <td><span class="badge badge-${shift.shift_type.split('_')[0]}">${formatShiftType(shift.shift_type)}</span></td>
                        <td style="font-weight: 700; color: var(--success)">$${shift.total_pay.toFixed(2)}</td>
                        <td class="actions">
                            <button class="btn btn-edit" onclick="editShift(${shift.id})">Edit</button>
                            <button class="btn btn-danger" onclick="deleteShift(${shift.id})">Delete</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    ` : '<div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-text">No shifts yet. Add your first shift!</div></div>';
    
    document.getElementById('shiftsList').innerHTML = shiftsHtml;
    updateBulkActionUI('shifts');
}

function switchDashboardView(view) {
    // Hide all views
    document.querySelectorAll('.dashboard-view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.dashboard-tab').forEach(t => t.classList.remove('active'));
    
    // Show selected view and tab
    const viewElement = document.getElementById(view + '-view');
    if (viewElement) viewElement.classList.add('active');
    
    // Find and activate the corresponding tab
    document.querySelectorAll('.dashboard-tab').forEach(tab => {
        if (tab.textContent.toLowerCase() === view) {
            tab.classList.add('active');
        }
    });
}

function renderGoalsStatus() {
    if (goals.length === 0) {
        document.getElementById('goalsStatus').innerHTML = '<div class="empty-goals"><div class="empty-goals-icon">📋</div><div>No goals yet</div></div>';
        return;
    }
    
    const today = new Date();
    const goalsWithStatus = goals.map(goal => {
        const deadline = goal.deadline ? new Date(goal.deadline) : null;
        const daysUntil = deadline ? Math.ceil((deadline - today) / (1000 * 60 * 60 * 24)) : null;
        const progress = goal.target_amount > 0 ? (goal.current_amount / goal.target_amount) * 100 : 0;
        
        let status = 'success';
        if (daysUntil !== null && daysUntil <= 7 && progress < 100) status = 'warning';
        if (daysUntil !== null && daysUntil <= 0) status = 'danger';
        
        return { ...goal, daysUntil, progress, status };
    });
    
    // Sort by urgency
    const sorted = goalsWithStatus.sort((a, b) => {
        if (a.status === 'danger' && b.status !== 'danger') return -1;
        if (a.status === 'warning' && b.status === 'success') return -1;
        return (a.daysUntil ?? 999) - (b.daysUntil ?? 999);
    }).slice(0, 4); // Show top 4 goals
    
    let html = sorted.map(goal => {
        const progressPercent = Math.min(goal.progress, 100);
        const deadlineText = goal.daysUntil !== null ? 
            (goal.daysUntil < 0 ? '<span style="color: var(--danger)">Overdue</span>' : 
             goal.daysUntil + ' days left') : 'No deadline';
        
        return `
            <div class="goal-alert ${goal.status}">
                <div class="goal-alert-content">
                    <div class="goal-alert-name">${goal.name}</div>
                    <div class="goal-alert-info">$${goal.current_amount.toFixed(2)} / $${goal.target_amount.toFixed(2)} • ${deadlineText}</div>
                </div>
                <div class="goal-alert-progress">
                    <div class="goal-progress-bar">
                        <div class="goal-progress-fill" style="width: ${progressPercent}%"></div>
                    </div>
                    <div class="goal-alert-percentage">${progressPercent.toFixed(0)}%</div>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('goalsStatus').innerHTML = html || '<div class="empty-goals">No active goals</div>';
}



function renderWorkplacesList() {
    const workplacesHtml = workplaces.length > 0 ? `
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Base Rate</th>
                    <th>Weekend</th>
                    <th>Public Holiday</th>
                    <th>Overtime</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${workplaces.map(wp => `
                    <tr>
                        <td style="font-weight: 600">${wp.name}</td>
                        <td>$${wp.base_rate.toFixed(2)}/hr</td>
                        <td>${wp.weekend_multiplier}×</td>
                        <td>${wp.public_holiday_multiplier}×</td>
                        <td>${wp.overtime_multiplier}× (after ${wp.overtime_threshold}h)</td>
                        <td class="actions">
                            <button class="btn btn-edit" onclick="editWorkplace(${wp.id})">Edit</button>
                            <button class="btn btn-danger" onclick="deleteWorkplace(${wp.id})">Delete</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    ` : '<div class="empty-state"><div class="empty-state-icon">🏢</div><div class="empty-state-text">No workplaces yet. Add your first workplace!</div></div>';
    
    document.getElementById('workplacesList').innerHTML = workplacesHtml;
}

function renderExpensesList() {
    const expensesHtml = expenses.length > 0 ? `
        <table>
            <thead>
                <tr>
                    <th style="width: 40px;"><input type="checkbox" id="selectAllExpensesTable" onchange="toggleSelectAll('expenses')" ${selectedExpenses.size === expenses.length && expenses.length > 0 ? 'checked' : ''}></th>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Due Date</th>
                    <th>Recurring</th>
                    <th>Notes</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${expenses.map(exp => `
                    <tr ${selectedExpenses.has(exp.id) ? 'class="selected-row"' : ''}>
                        <td><input type="checkbox" ${selectedExpenses.has(exp.id) ? 'checked' : ''} onchange="toggleSelection('expenses', ${exp.id})"></td>
                        <td style="font-weight: 600">${exp.category}</td>
                        <td style="color: var(--danger); font-weight: 700">-$${exp.amount.toFixed(2)}</td>
                        <td>${exp.due_date ? formatDate(exp.due_date) : '-'}</td>
                        <td>${exp.is_recurring ? '✓' : '✗'}</td>
                        <td>${exp.notes || '-'}</td>
                        <td class="actions">
                            <button class="btn btn-edit" onclick="editExpense(${exp.id})">Edit</button>
                            <button class="btn btn-danger" onclick="deleteExpense(${exp.id})">Delete</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    ` : '<div class="empty-state"><div class="empty-state-icon">💵</div><div class="empty-state-text">No expenses yet. Add your first expense!</div></div>';
    
    document.getElementById('expensesList').innerHTML = expensesHtml;
    updateBulkActionUI('expenses');
}

function renderGoalsList() {
    const goalsHtml = goals.length > 0 ? goals.map(goal => {
        const progress = Math.min(goal.progress, 100);
        const isCompleted = progress >= 100;
        const deadline = goal.deadline ? new Date(goal.deadline + 'T00:00:00') : null;
        const isNearDeadline = deadline && (deadline - new Date()) < 30 * 24 * 60 * 60 * 1000 && !isCompleted;
        
        let cardClass = 'goal-card draggable-goal';
        if (isCompleted) cardClass += ' goal-completed';
        else if (isNearDeadline) cardClass += ' goal-deadline-warning';
        if (selectedGoals.has(goal.id)) cardClass += ' selected-card';
        
        return `
            <div class="${cardClass}" 
                 data-goal-id="${goal.id}"
                 draggable="true"
                 ondragstart="handleDragStart(event, ${goal.id})"
                 ondragover="handleDragOver(event)"
                 ondrop="handleDrop(event, ${goal.id})"
                 ondragend="handleDragEnd(event)">
                <div class="goal-checkbox">
                    <input type="checkbox" ${selectedGoals.has(goal.id) ? 'checked' : ''} onchange="toggleSelection('goals', ${goal.id})" onclick="event.stopPropagation()">
                    <span class="drag-handle" title="Drag to reorder">⋮⋮</span>
                </div>
                <div class="goal-header">
                    <div>
                        <div class="goal-name">${goal.name}</div>
                        ${goal.deadline ? `<div style="font-size: 13px; opacity: 0.9;">Target: ${formatDate(goal.deadline)}</div>` : ''}
                    </div>
                    <div class="goal-priority">${goal.priority === 3 ? 'High' : goal.priority === 2 ? 'Medium' : 'Low'}</div>
                </div>
                
                <div class="goal-amounts">
                    <div class="goal-target">$${goal.target_amount.toFixed(2)}</div>
                    <div class="goal-saved">Saved: $${goal.saved_amount.toFixed(2)} • Remaining: $${goal.remaining.toFixed(2)}</div>
                </div>
                
                <div class="goal-progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%">
                            ${progress > 15 ? `${progress.toFixed(0)}%` : ''}
                        </div>
                    </div>
                    ${progress <= 15 ? `<div style="font-size: 12px; text-align: right;">${progress.toFixed(0)}%</div>` : ''}
                </div>
                
                ${goal.auto_allocate > 0 ? `
                    <div class="goal-info">
                        <span>💵 Auto-save: $${goal.auto_allocate.toFixed(2)}/fortnight</span>
                        ${!isCompleted && goal.remaining > 0 && goal.auto_allocate > 0 ? 
                            `<span>~${Math.ceil(goal.remaining / goal.auto_allocate)} fortnights</span>` : ''}
                    </div>
                ` : ''}
                
                ${goal.notes ? `<div style="font-size: 13px; margin-bottom: 15px; opacity: 0.95;">${goal.notes}</div>` : ''}
                
                <div class="goal-actions">
                    ${!isCompleted ? `<button class="btn btn-success" onclick="showContributeModal(${goal.id})">💰 Add Money</button>` : ''}
                    <button class="btn btn-edit" onclick="editGoal(${goal.id})">Edit</button>
                    <button class="btn btn-danger" onclick="deleteGoal(${goal.id})">Delete</button>
                </div>
            </div>
        `;
    }).join('') : '<div class="empty-state"><div class="empty-state-icon">🎯</div><div class="empty-state-text">No goals yet. Set your first financial goal!</div></div>';
    
    document.getElementById('goalsList').innerHTML = goalsHtml;
    updateBulkActionUI('goals');
}

// ============ CHARTS ============
let spendingChartInstance = null;
let incomeChartInstance = null;

function renderSpendingChart() {
    const canvas = document.getElementById('spendingChart');
    if (!canvas) return;
    
    // Group expenses by category
    const categoryTotals = {};
    expenses.forEach(expense => {
        const category = expense.category || 'Other';
        categoryTotals[category] = (categoryTotals[category] || 0) + expense.amount;
    });
    
    const categories = Object.keys(categoryTotals);
    const amounts = Object.values(categoryTotals);
    
    // Destroy previous chart if exists
    if (spendingChartInstance) {
        spendingChartInstance.destroy();
    }
    
    // Create pie chart
    spendingChartInstance = new Chart(canvas, {
        type: 'pie',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: [
                    '#3b82f6', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6',
                    '#ec4899', '#f97316', '#06b6d4', '#10b981', '#6366f1'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 12,
                        font: {
                            size: 12,
                            family: 'Space Grotesk'
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = amounts.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderIncomeChart() {
    const canvas = document.getElementById('incomeChart');
    if (!canvas) return;
    
    // Group shifts by month
    const monthlyIncome = {};
    shifts.forEach(shift => {
        const date = new Date(shift.date);
        const monthKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        monthlyIncome[monthKey] = (monthlyIncome[monthKey] || 0) + shift.total_pay;
    });
    
    // Sort by date
    const sortedMonths = Object.keys(monthlyIncome).sort((a, b) => {
        return new Date(a) - new Date(b);
    });
    
    // Get last 6 months
    const months = sortedMonths.slice(-6);
    const income = months.map(m => monthlyIncome[m]);
    
    // Destroy previous chart if exists
    if (incomeChartInstance) {
        incomeChartInstance.destroy();
    }
    
    // Create line chart
    incomeChartInstance = new Chart(canvas, {
        type: 'line',
        data: {
            labels: months,
            datasets: [{
                label: 'Monthly Income',
                data: income,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Income: $${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        },
                        font: {
                            family: 'Space Grotesk'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            family: 'Space Grotesk'
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ============ CALENDAR FUNCTIONS ============
function renderShiftCalendar() {
    const calendar = document.getElementById('shiftCalendar');
    if (!calendar) return;

    const year = currentCalendarMonth.getFullYear();
    const month = currentCalendarMonth.getMonth();
    
    // Update title
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    const title = document.getElementById('calendarTitle');
    if (title) {
        title.textContent = `📅 ${monthNames[month]} ${year}`;
    }
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    // Build calendar HTML
    let html = '<div class="calendar-weekdays">';
    const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    weekdays.forEach(day => {
        html += `<div class="calendar-weekday">${day}</div>`;
    });
    html += '</div><div class="calendar-days">';
    
    // Add empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
        html += '<div class="calendar-day empty"></div>';
    }
    
    // Add days of month
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayShifts = shifts.filter(s => s.date === dateStr);
        
        const isToday = new Date().toDateString() === new Date(year, month, day).toDateString();
        const hasShifts = dayShifts.length > 0;
        
        let dayClass = 'calendar-day';
        if (isToday) dayClass += ' today';
        if (hasShifts) dayClass += ' has-shifts';
        
        let shiftsHtml = '';
        if (hasShifts) {
            const totalPay = dayShifts.reduce((sum, s) => sum + (s.total_pay || 0), 0);
            const totalHours = dayShifts.reduce((sum, s) => sum + (s.hours || 0), 0);
            shiftsHtml = `
                <div class="calendar-shifts">
                    <span class="shift-count">${dayShifts.length} shift${dayShifts.length > 1 ? 's' : ''}</span>
                    <span class="shift-hours">${totalHours}h</span>
                    <span class="shift-pay">$${totalPay.toFixed(0)}</span>
                </div>
            `;
        }
        
        html += `
            <div class="${dayClass}" data-date="${dateStr}">
                <div class="calendar-day-number">${day}</div>
                ${shiftsHtml}
            </div>
        `;
    }
    
    html += '</div>';
    calendar.innerHTML = html;
}

function changeCalendarMonth(direction) {
    currentCalendarMonth.setMonth(currentCalendarMonth.getMonth() + direction);
    renderShiftCalendar();
}

// Event Listeners
function setupEventListeners() {
    try {
        // Shift form
        const shiftForm = document.getElementById('shiftForm');
        if (shiftForm) {
            shiftForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                console.log('Shift form submitted');
                await saveShift();
            });
        } else {
            console.warn('shiftForm not found');
        }
        
        // Workplace form
        const workplaceForm = document.getElementById('workplaceForm');
        if (workplaceForm) {
            workplaceForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                console.log('Workplace form submitted');
                await saveWorkplace();
            });
        } else {
            console.warn('workplaceForm not found');
        }
        
        // Expense form
        const expenseForm = document.getElementById('expenseForm');
        if (expenseForm) {
            expenseForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                console.log('Expense form submitted');
                await saveExpense();
            });
        } else {
            console.warn('expenseForm not found');
        }
        
        // Goal form
        const goalForm = document.getElementById('goalForm');
        if (goalForm) {
            goalForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                console.log('Goal form submitted');
                await saveGoal();
            });
        } else {
            console.warn('goalForm not found');
        }
        
        // Contribute form
        const contributeForm = document.getElementById('contributeForm');
        if (contributeForm) {
            contributeForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                console.log('Contribution form submitted');
                await saveContribution();
            });
        } else {
            console.warn('contributeForm not found');
        }
        
        // Calendar navigation
        const prevMonthBtn = document.getElementById('prevMonth');
        const nextMonthBtn = document.getElementById('nextMonth');
        if (prevMonthBtn) {
            prevMonthBtn.addEventListener('click', () => changeCalendarMonth(-1));
        }
        if (nextMonthBtn) {
            nextMonthBtn.addEventListener('click', () => changeCalendarMonth(1));
        }
        
        console.log('Event listeners attached successfully');
    } catch (error) {
        console.error('Error setting up event listeners:', error);
    }
}

// Tab management
function showTab(tabName, event) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    let trigger = (event && event.currentTarget) ? event.currentTarget : null;
    if (!trigger) {
        trigger = document.querySelector(`.tab[data-tab="${tabName}"]`);
    }
    if (trigger) {
        trigger.classList.add('active');
    }
}

// Modal management
function showShiftModal(shiftId = null) {
    const modal = document.getElementById('shiftModal');
    const form = document.getElementById('shiftForm');
    form.reset();
    
    // Populate workplaces dropdown
    const workplaceSelect = document.getElementById('shiftWorkplace');
    workplaceSelect.innerHTML = workplaces.map(wp => 
        `<option value="${wp.id}">${wp.name}</option>`
    ).join('');
    
    if (shiftId) {
        const shift = shifts.find(s => s.id === shiftId);
        document.getElementById('shiftModalTitle').textContent = 'Edit Shift';
        document.getElementById('shiftId').value = shift.id;
        document.getElementById('shiftWorkplace').value = shift.workplace_id;
        document.getElementById('shiftDate').value = shift.date;
        document.getElementById('shiftStart').value = shift.start_time;
        document.getElementById('shiftEnd').value = shift.end_time;
        document.getElementById('shiftHours').value = shift.hours;
        document.getElementById('shiftNotes').value = shift.notes || '';
    } else {
        document.getElementById('shiftModalTitle').textContent = 'Add Shift';
        // Set today's date as default
        document.getElementById('shiftDate').value = new Date().toISOString().split('T')[0];
    }
    
    modal.classList.add('active');
}

function showWorkplaceModal(workplaceId = null) {
    const modal = document.getElementById('workplaceModal');
    const form = document.getElementById('workplaceForm');
    form.reset();
    
    if (workplaceId) {
        const workplace = workplaces.find(w => w.id === workplaceId);
        document.getElementById('workplaceModalTitle').textContent = 'Edit Workplace';
        document.getElementById('workplaceId').value = workplace.id;
        document.getElementById('workplaceName').value = workplace.name;
        document.getElementById('baseRate').value = workplace.base_rate;
        document.getElementById('weekendMultiplier').value = workplace.weekend_multiplier;
        document.getElementById('publicHolidayMultiplier').value = workplace.public_holiday_multiplier;
        document.getElementById('overtimeMultiplier').value = workplace.overtime_multiplier;
        document.getElementById('overtimeThreshold').value = workplace.overtime_threshold;
    } else {
        document.getElementById('workplaceModalTitle').textContent = 'Add Workplace';
    }
    
    modal.classList.add('active');
}

function showExpenseModal(expenseId = null) {
    const modal = document.getElementById('expenseModal');
    const form = document.getElementById('expenseForm');
    form.reset();
    
    if (expenseId) {
        const expense = expenses.find(e => e.id === expenseId);
        document.getElementById('expenseModalTitle').textContent = 'Edit Expense';
        document.getElementById('expenseId').value = expense.id;
        document.getElementById('expenseCategory').value = expense.category;
        document.getElementById('expenseAmount').value = expense.amount;
        document.getElementById('expenseDueDate').value = expense.due_date || '';
        document.getElementById('expenseRecurring').checked = expense.is_recurring;
        document.getElementById('expenseNotes').value = expense.notes || '';
    } else {
        document.getElementById('expenseModalTitle').textContent = 'Add Expense';
    }
    
    modal.classList.add('active');
}

function showGoalModal(goalId = null) {
    const modal = document.getElementById('goalModal');
    const form = document.getElementById('goalForm');
    form.reset();
    
    if (goalId) {
        const goal = goals.find(g => g.id === goalId);
        document.getElementById('goalModalTitle').textContent = 'Edit Goal';
        document.getElementById('goalId').value = goal.id;
        document.getElementById('goalName').value = goal.name;
        document.getElementById('goalTarget').value = goal.target_amount;
        document.getElementById('goalDeadline').value = goal.deadline || '';
        document.getElementById('goalAutoAllocate').value = goal.auto_allocate || 0;
        document.getElementById('goalPriority').value = goal.priority || 2;
        document.getElementById('goalNotes').value = goal.notes || '';
    } else {
        document.getElementById('goalModalTitle').textContent = 'Add Goal';
        document.getElementById('goalPriority').value = 2;
    }
    
    modal.classList.add('active');
}

function showContributeModal(goalId) {
    const modal = document.getElementById('contributeModal');
    const form = document.getElementById('contributeForm');
    form.reset();
    
    document.getElementById('contributeGoalId').value = goalId;
    document.getElementById('contributeDate').value = new Date().toISOString().split('T')[0];
    
    modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('closing');
    setTimeout(() => {
        modal.classList.remove('active');
        modal.classList.remove('closing');
    }, 250);
}

// Close modal when clicking outside
window.onclick = (event) => {
    if (event.target.classList.contains('modal') && event.target.classList.contains('active')) {
        closeModal(event.target.id);
    }
};

// CRUD Operations
async function saveShift() {
    const id = document.getElementById('shiftId').value;
    const workplaceId = parseInt(document.getElementById('shiftWorkplace').value);
    const hours = parseFloat(document.getElementById('shiftHours').value);
    
    // Find the workplace to get base_rate
    const workplace = workplaces.find(w => w.id === workplaceId);
    let totalPay = hours * (workplace ? workplace.base_rate : 20);  // Default to $20/hr if workplace not found
    
    const data = {
        workplace_id: workplaceId,
        date: document.getElementById('shiftDate').value,
        start_time: document.getElementById('shiftStart').value,
        end_time: document.getElementById('shiftEnd').value,
        hours: hours,
        total_pay: totalPay,
        notes: document.getElementById('shiftNotes').value
    };
    
    const url = id ? `${API_URL}/shifts/${id}` : `${API_URL}/shifts`;
    const method = id ? 'PUT' : 'POST';
    
    try {
        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || err.errors?.join(', ') || 'Failed to save shift');
        }
        
        closeModal('shiftModal');
        await loadAllData();
    } catch (error) {
        console.error('Error saving shift:', error);
        alert('Error: ' + error.message);
    }
}

async function saveWorkplace() {
    const id = document.getElementById('workplaceId').value;
    const data = {
        name: document.getElementById('workplaceName').value,
        base_rate: parseFloat(document.getElementById('baseRate').value),
        weekend_multiplier: parseFloat(document.getElementById('weekendMultiplier').value),
        public_holiday_multiplier: parseFloat(document.getElementById('publicHolidayMultiplier').value),
        overtime_multiplier: parseFloat(document.getElementById('overtimeMultiplier').value),
        overtime_threshold: parseFloat(document.getElementById('overtimeThreshold').value)
    };
    
    const url = id ? `${API_URL}/workplaces/${id}` : `${API_URL}/workplaces`;
    const method = id ? 'PUT' : 'POST';
    
    try {
        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to save workplace');
        }
        
        closeModal('workplaceModal');
        await loadAllData();
    } catch (error) {
        console.error('Error saving workplace:', error);
        alert('Error: ' + error.message);
    }
}

async function saveExpense() {
    const id = document.getElementById('expenseId').value;
    const data = {
        category: document.getElementById('expenseCategory').value,
        amount: parseFloat(document.getElementById('expenseAmount').value),
        due_date: document.getElementById('expenseDueDate').value || null,
        is_recurring: document.getElementById('expenseRecurring').checked ? 1 : 0,
        notes: document.getElementById('expenseNotes').value
    };
    
    const url = id ? `${API_URL}/expenses/${id}` : `${API_URL}/expenses`;
    const method = id ? 'PUT' : 'POST';
    
    try {
        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to save expense');
        }
        
        closeModal('expenseModal');
        await loadAllData();
    } catch (error) {
        console.error('Error saving expense:', error);
        alert('Error: ' + error.message);
    }
}

async function editShift(id) {
    showShiftModal(id);
}

async function editWorkplace(id) {
    showWorkplaceModal(id);
}

async function editExpense(id) {
    showExpenseModal(id);
}

async function deleteShift(id) {
    if (!confirm('Are you sure you want to delete this shift?')) return;
    
    try {
        const response = await authFetch(`${API_URL}/shifts/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete shift');
        await loadAllData();
    } catch (error) {
        console.error('Error deleting shift:', error);
        alert('Error: ' + error.message);
    }
}

async function deleteWorkplace(id) {
    if (!confirm('Are you sure you want to delete this workplace?')) return;
    
    try {
        const response = await authFetch(`${API_URL}/workplaces/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete workplace');
        await loadAllData();
    } catch (error) {
        console.error('Error deleting workplace:', error);
        alert('Error: ' + error.message);
    }
}

async function deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense?')) return;
    
    try {
        const response = await authFetch(`${API_URL}/expenses/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete expense');
        await loadAllData();
    } catch (error) {
        console.error('Error deleting expense:', error);
        alert('Error: ' + error.message);
    }
}

async function saveGoal() {
    const id = document.getElementById('goalId').value;
    const data = {
        name: document.getElementById('goalName').value,
        target_amount: parseFloat(document.getElementById('goalTarget').value),
        deadline: document.getElementById('goalDeadline').value || null,
        auto_allocate: parseFloat(document.getElementById('goalAutoAllocate').value) || 0,
        priority: parseInt(document.getElementById('goalPriority').value),
        notes: document.getElementById('goalNotes').value
    };
    
    const url = id ? `${API_URL}/goals/${id}` : `${API_URL}/goals`;
    const method = id ? 'PUT' : 'POST';
    
    try {
        const response = await authFetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to save goal');
        }
        
        closeModal('goalModal');
        await loadAllData();
    } catch (error) {
        console.error('Error saving goal:', error);
        alert('Error: ' + error.message);
    }
}

async function saveContribution() {
    const goalId = document.getElementById('contributeGoalId').value;
    const data = {
        amount: parseFloat(document.getElementById('contributeAmount').value),
        date: document.getElementById('contributeDate').value,
        notes: document.getElementById('contributeNotes').value
    };
    
    try {
        const response = await authFetch(`${API_URL}/goals/${goalId}/contribute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to add contribution');
        }
        
        closeModal('contributeModal');
        await loadAllData();
    } catch (error) {
        console.error('Error adding contribution:', error);
        alert('Error: ' + error.message);
    }
}

async function editGoal(id) {
    showGoalModal(id);
}

async function deleteGoal(id) {
    if (!confirm('Are you sure you want to delete this goal? All contributions will also be deleted.')) return;
    
    try {
        const response = await authFetch(`${API_URL}/goals/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete goal');
        await loadAllData();
    } catch (error) {
        console.error('Error deleting goal:', error);
        alert('Error: ' + error.message);
    }
}

// Utility functions
function formatDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatShiftType(type) {
    return type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Search and Export Functions
function toggleSearch() {
    const panel = document.getElementById('searchPanel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

function populateSearchWorkplaces() {
    const select = document.getElementById('searchWorkplace');
    select.innerHTML = '<option value="">All Workplaces</option>' + 
        workplaces.map(wp => `<option value="${wp.id}">${wp.name}</option>`).join('');
}

async function searchShifts() {
    const startDate = document.getElementById('searchStartDate').value;
    const endDate = document.getElementById('searchEndDate').value;
    const workplaceId = document.getElementById('searchWorkplace').value;
    
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (workplaceId) params.append('workplace_id', workplaceId);
    
    try {
        const response = await authFetch(`${API_URL}/search/shifts?${params}`);
        shifts = await response.json();
        renderShiftsList();
    } catch (error) {
        console.error('Error searching shifts:', error);
    }
}

async function clearSearch() {
    document.getElementById('searchStartDate').value = '';
    document.getElementById('searchEndDate').value = '';
    document.getElementById('searchWorkplace').value = '';
    await loadShifts();
    renderShiftsList();
}

async function exportShifts() {
    try {
        const response = await authFetch(`${API_URL}/export/shifts`);
        const csv = await response.text();
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `shifts_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Error exporting shifts:', error);
        alert('Error exporting shifts');
    }
}

// ============ BULK ACTIONS ============
function toggleSelection(type, id) {
    const selectedSet = type === 'shifts' ? selectedShifts : 
                       type === 'expenses' ? selectedExpenses : selectedGoals;
    
    if (selectedSet.has(id)) {
        selectedSet.delete(id);
    } else {
        selectedSet.add(id);
    }
    
    // Re-render to update UI
    if (type === 'shifts') renderShiftsList();
    else if (type === 'expenses') renderExpensesList();
    else if (type === 'goals') renderGoalsList();
}

function toggleSelectAll(type) {
    const selectedSet = type === 'shifts' ? selectedShifts : 
                       type === 'expenses' ? selectedExpenses : selectedGoals;
    const items = type === 'shifts' ? shifts : 
                 type === 'expenses' ? expenses : goals;
    
    if (selectedSet.size === items.length) {
        // Deselect all
        selectedSet.clear();
    } else {
        // Select all
        selectedSet.clear();
        items.forEach(item => selectedSet.add(item.id));
    }
    
    // Re-render to update UI
    if (type === 'shifts') renderShiftsList();
    else if (type === 'expenses') renderExpensesList();
    else if (type === 'goals') renderGoalsList();
}

function updateBulkActionUI(type) {
    const selectedSet = type === 'shifts' ? selectedShifts : 
                       type === 'expenses' ? selectedExpenses : selectedGoals;
    const count = selectedSet.size;
    
    // Construct proper element IDs
    const typeCapitalized = type.charAt(0).toUpperCase() + type.slice(1);
    const deleteBtn = document.getElementById(`bulkDelete${typeCapitalized}`);
    const countSpan = document.getElementById(`selected${typeCapitalized}Count`);
    const selectAllCheckbox = document.getElementById(`selectAll${typeCapitalized}`);
    
    if (deleteBtn) {
        deleteBtn.style.display = count > 0 ? 'inline-block' : 'none';
    }
    
    if (countSpan) {
        countSpan.textContent = count > 0 ? `${count} selected` : '';
    }
    
    if (selectAllCheckbox) {
        const items = type === 'shifts' ? shifts : type === 'expenses' ? expenses : goals;
        selectAllCheckbox.checked = count === items.length && items.length > 0;
    }
}

async function bulkDeleteShifts() {
    if (selectedShifts.size === 0) return;
    
    if (!confirm(`Delete ${selectedShifts.size} selected shift(s)?`)) return;
    
    try {
        const deletePromises = Array.from(selectedShifts).map(id =>
            authFetch(`${API_URL}/shifts/${id}`, { method: 'DELETE' })
        );
        
        await Promise.all(deletePromises);
        selectedShifts.clear();
        await loadAllData();
    } catch (error) {
        console.error('Error deleting shifts:', error);
        alert('Failed to delete some shifts');
    }
}

async function bulkDeleteExpenses() {
    if (selectedExpenses.size === 0) return;
    
    if (!confirm(`Delete ${selectedExpenses.size} selected expense(s)?`)) return;
    
    try {
        const deletePromises = Array.from(selectedExpenses).map(id =>
            authFetch(`${API_URL}/expenses/${id}`, { method: 'DELETE' })
        );
        
        await Promise.all(deletePromises);
        selectedExpenses.clear();
        await loadAllData();
    } catch (error) {
        console.error('Error deleting expenses:', error);
        alert('Failed to delete some expenses');
    }
}

async function bulkDeleteGoals() {
    if (selectedGoals.size === 0) return;
    
    if (!confirm(`Delete ${selectedGoals.size} selected goal(s)?`)) return;
    
    try {
        const deletePromises = Array.from(selectedGoals).map(id =>
            authFetch(`${API_URL}/goals/${id}`, { method: 'DELETE' })
        );
        
        await Promise.all(deletePromises);
        selectedGoals.clear();
        await loadAllData();
    } catch (error) {
        console.error('Error deleting goals:', error);
        alert('Failed to delete some goals');
    }
}

// ============ DRAG AND DROP ============
function handleDragStart(event, goalId) {
    draggedGoalId = goalId;
    event.currentTarget.style.opacity = '0.5';
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/html', event.currentTarget.innerHTML);
}

function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDrop(event, targetGoalId) {
    event.stopPropagation();
    event.preventDefault();
    
    if (draggedGoalId !== targetGoalId) {
        // Find indices
        const draggedIndex = goals.findIndex(g => g.id === draggedGoalId);
        const targetIndex = goals.findIndex(g => g.id === targetGoalId);
        
        if (draggedIndex !== -1 && targetIndex !== -1) {
            // Reorder array
            const [draggedGoal] = goals.splice(draggedIndex, 1);
            goals.splice(targetIndex, 0, draggedGoal);
            
            // Re-render
            renderGoalsList();
        }
    }
    
    return false;
}

function handleDragEnd(event) {
    event.currentTarget.style.opacity = '1';
    draggedGoalId = null;
}

// ============ THEME FUNCTIONS ============
function setTheme(themeName) {
    // Set theme on body
    document.body.setAttribute('data-theme', themeName);
    
    // Save to localStorage
    localStorage.setItem('theme', themeName);
    
    // Update active button
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`.theme-btn[data-theme="${themeName}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'default';
    setTheme(savedTheme);
}

// Load theme on page load
loadTheme();
