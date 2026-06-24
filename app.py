import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "super_secret_legal_key_123"

def init_db():
    conn = sqlite3.connect('legal_marketplace.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ministry TEXT NOT NULL,
            last_designation TEXT NOT NULL,
            experience INTEGER NOT NULL,
            specialization TEXT NOT NULL,
            readymade_service TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    # Check & Add Column category
    try:
        cursor.execute("ALTER TABLE experts ADD COLUMN category TEXT DEFAULT 'Legal'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Check & Add Column is_active
    try:
        cursor.execute("ALTER TABLE experts ADD COLUMN is_active INTEGER DEFAULT 1")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Client Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            client_email TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            expert_id INTEGER NOT NULL,
            problem_description TEXT NOT NULL,
            payment_status TEXT DEFAULT 'Paid (₹1,500 Platform Fee)'
        )
    ''')
    
    # FORCED RESYNC: Santosh ji ko position 1 par fresh sync framework ke sath set karna
    cursor.execute("SELECT COUNT(*) FROM experts")
    if cursor.fetchone()[0] < 4:
        cursor.execute("DELETE FROM experts")
        
        demo_experts = [
            # 👑 1 NUMBER EXPERT - ADVOCATE SANTOSH UPADHYAY
            ("Advocate Santosh Upadhyay", "AIIMS New Delhi / Ex-Ministry of AYUSH & MNRE", "Legal Advisor", 13, "Constitutional, Healthcare Laws & Public Policy", "Premium legal advisory on Healthcare regulations, institutional governance, MNRE/AYUSH compliance auditing, and High Court/Supreme Court litigation blueprint.", 50000, "Legal", 1),
            
            # LEGAL EXPERT 2
            ("Advocate Shri Prakash Mishra", "Ministry of AYUSH", "Ex-Chief Legal Consultant", 25, "Drug Licensing & Regulatory Compliance", "Complete documentation framework and standard compliance file for launching an Ayush Medical College or Hospital.", 45000, "Legal", 1),
            
            # LEGAL EXPERT 3
            ("Shri Ravindra Nath Trivedi", "Ministry of Power / Energy", "Ex-Senior Advisor (Legal)", 28, "Electricity Act & Govt Bidding", "Detailed legal evaluation report, policy compliance check, and drafting format for Hydro/Solar Project Tenders.", 60000, "Legal", 1),
            
            # IT EXPERT 4
            ("Vikash Kumar", "PMU - IMUIS Project (AIIMS)", "Senior Consultant / Technical Officer", 12, "Python, AI Automation & System Design", "One-to-One Career Guidance, Resume Vetting, and Technical Architecture suggestions for IT Sector Growth and Interview cracking.", 30000, "IT", 1)
        ]
        
        cursor.executemany('''
            INSERT INTO experts (id, name, ministry, last_designation, experience, specialization, readymade_service, price, category, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [(i+1, e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8]) for i, e in enumerate(demo_experts)])
        
    conn.commit()
    conn.close()

@app.route('/admin/toggle-expert/<int:expert_id>')
def toggle_expert(expert_id):
    conn = sqlite3.connect('legal_marketplace.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_active, name FROM experts WHERE id = ?", (expert_id,))
    row = cursor.fetchone()
    
    if row:
        current_status = row[0]
        expert_name = row[1]
        new_status = 0 if current_status == 1 else 1
        cursor.execute("UPDATE experts SET is_active = ? WHERE id = ?", (new_status, expert_id))
        conn.commit()
        flash(f"Status Updated for {expert_name}!", "success")
    
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/')
def index():
    return render_template('index.html')

# 💥 NAYA ROUTE: Santosh Upadhyay ji ke premium HTML profile page ke liye gateway
@app.route('/expert/santosh')
def profile_santosh():
    return render_template('expert_santosh.html')

@app.route('/experts')
def view_experts():
    conn = sqlite3.connect('legal_marketplace.db')
    cursor = conn.cursor()
    cat_filter = request.args.get('category', 'Legal')
    
    if cat_filter == 'IT':
        cursor.execute("SELECT * FROM experts WHERE category = 'IT' AND is_active = 1")
        all_experts = cursor.fetchall()
        conn.close()
        return render_template('it_experts.html', experts=all_experts, current_category=cat_filter)
    else:
        cursor.execute("SELECT * FROM experts WHERE category = 'Legal' AND is_active = 1")
        all_experts = cursor.fetchall()
        conn.close()
        return render_template('experts.html', experts=all_experts, current_category=cat_filter)

@app.route('/book/<int:expert_id>', methods=['GET', 'POST'])
def book_consultation(expert_id):
    conn = sqlite3.connect('legal_marketplace.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM experts WHERE id = ?', (expert_id,))
    expert = cursor.fetchone()
    
    if request.method == 'POST':
        client_name = request.form['client_name']
        client_email = request.form['client_email']
        client_phone = request.form['client_phone']
        problem_description = request.form['problem_description']
        
        cursor.execute('''
            INSERT INTO bookings (client_name, client_email, client_phone, expert_id, problem_description)
            VALUES (?, ?, ?, ?, ?)
        ''', (client_name, client_email, client_phone, expert_id, problem_description))
        
        conn.commit()
        conn.close()
        flash(f"Success! Platform Fee Paid.", "success")
        return redirect(url_for('view_experts', category=expert[8]))
        
    conn.close()
    return render_template('book_consultation.html', expert=expert)

@app.route('/admin-panel')
def admin_panel():
    conn = sqlite3.connect('legal_marketplace.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.id, b.client_name, b.client_email, b.client_phone, e.name, b.problem_description, b.payment_status, e.category 
        FROM bookings b
        JOIN experts e ON b.expert_id = e.id
    ''')
    all_bookings = cursor.fetchall()
    
    cursor.execute("SELECT id, name, category, is_active FROM experts")
    all_experts = cursor.fetchall()
    
    conn.close()
    return render_template('admin_panel.html', bookings=all_bookings, experts=all_experts)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)