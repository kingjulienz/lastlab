from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Transaction
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey123'

# --- ส่วนที่แก้ไข: รองรับทั้ง SQLite และ Neon (PostgreSQL) บน Vercel ---
database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# -------------------------------------------------------------

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def mask_phone(phone):
    if phone and len(phone) >= 3:
        return f"{phone[:3]}-xxxx-xxxx"
    return "xxx-xxxx-xxxx"

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        role = request.form.get('role', 'user')

        if User.query.filter_by(username=username).first():
            flash('ชื่อผู้ใช้นี้ถูกใช้งานแล้ว')
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_pw, phone=phone, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    
    total_balance = 0
    for t in user_transactions:
        if t.type == 'income':
            total_balance += t.amount
        else:
            total_balance -= t.amount

    masked_phone = mask_phone(current_user.phone)
    return render_template('dashboard.html', transactions=user_transactions, total_balance=total_balance, masked_phone=masked_phone)

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    title = request.form['title']
    amount = float(request.form['amount'])
    t_type = request.form['type']
    
    new_t = Transaction(title=title, amount=amount, type=t_type, user_id=current_user.id)
    db.session.add(new_t)
    db.session.commit()
    flash('บันทึกรายการสำเร็จ!')
    return redirect(url_for('dashboard'))

@app.route('/delete_transaction/<int:t_id>', methods=['POST'])
@login_required
def delete_transaction(t_id):
    t = Transaction.query.filter_by(id=t_id, user_id=current_user.id).first()
    if t:
        db.session.delete(t)
        db.session.commit()
        flash('ลบรายการเรียบร้อย')
    else:
        flash('คุณไม่มีสิทธิ์ลบรายการนี้!')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('ปฏิเสธการเข้าถึง! เฉพาะผู้ดูแลระบบเท่านั้น')
        return redirect(url_for('dashboard'))

    all_users = User.query.all()
    all_transactions = Transaction.query.all()
    return render_template('admin.html', users=all_users, transactions=all_transactions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("Server running on http://127.0.0.1:5000")
    app.run(debug=True)