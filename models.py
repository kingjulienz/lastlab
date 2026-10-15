from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Password Hashing
    phone = db.Column(db.String(20), nullable=False)      # PII Masking (เบอร์โทรศัพท์)
    role = db.Column(db.String(20), default='user')       # RBAC (user / admin)
    transactions = db.relationship('Transaction', backref='owner', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)     # รายละเอียดรายการ
    amount = db.Column(db.Float, nullable=False)         # จำนวนเงิน
    type = db.Column(db.String(10), nullable=False)      # ประเภท: 'income' (รายรับ) หรือ 'expense' (รายจ่าย)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)