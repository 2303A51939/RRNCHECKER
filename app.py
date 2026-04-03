from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random, string, time, os, requests

app = Flask(__name__)
app.secret_key = 'rrn_secret_key_sru_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rrn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── FAST2SMS API KEY ────────────────────────────────────────
FAST2SMS_API_KEY = "YOUR_FAST2SMS_API_KEY"  # Replace with your key from fast2sms.com

# ─── MODELS ─────────────────────────────────────────────────

class User(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    mobile    = db.Column(db.String(10), unique=True, nullable=False)
    name      = db.Column(db.String(100))
    created   = db.Column(db.DateTime, default=datetime.utcnow)
    searches  = db.relationship('Transaction', backref='user', lazy=True)

class OTP(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    mobile    = db.Column(db.String(10), nullable=False)
    otp       = db.Column(db.String(6), nullable=False)
    created   = db.Column(db.DateTime, default=datetime.utcnow)
    used      = db.Column(db.Boolean, default=False)

class Transaction(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    rrn         = db.Column(db.String(20), nullable=False)
    app_name    = db.Column(db.String(50))
    status      = db.Column(db.String(20))
    amount      = db.Column(db.Float)
    merchant    = db.Column(db.String(100))
    bank        = db.Column(db.String(100))
    timestamp   = db.Column(db.String(50))
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'))

# ─── PAYMENT APPS ────────────────────────────────────────────

PAYMENT_APPS = [
    {"id": "phonepe",     "name": "PhonePe",      "color": "#5f259f", "icon": "📱"},
    {"id": "paytm",       "name": "Paytm",         "color": "#002970", "icon": "💙"},
    {"id": "gpay",        "name": "Google Pay",    "color": "#4285f4", "icon": "🔵"},
    {"id": "amazonpay",   "name": "Amazon Pay",    "color": "#ff9900", "icon": "🟠"},
    {"id": "bookmyshow",  "name": "BookMyShow",    "color": "#e51937", "icon": "🎬"},
    {"id": "meesho",      "name": "Meesho",        "color": "#9b2335", "icon": "🛍️"},
    {"id": "swiggy",      "name": "Swiggy",        "color": "#fc8019", "icon": "🍔"},
    {"id": "zomato",      "name": "Zomato",        "color": "#e23744", "icon": "🍕"},
    {"id": "cred",        "name": "CRED",           "color": "#1a1a2e", "icon": "💳"},
]

MERCHANTS = {
    "phonepe":    ["Reliance Jio", "BigBazaar", "Flipkart", "IRCTC", "Myntra"],
    "paytm":      ["Paytm Mall", "Movies", "Travel", "Games", "Utilities"],
    "gpay":       ["Google Store", "YouTube Premium", "Play Store", "Tata Sky"],
    "amazonpay":  ["Amazon.in", "Prime Video", "Fresh", "Pantry", "Audible"],
    "bookmyshow": ["PVR Cinemas", "INOX", "Carnival", "SPI Cinemas", "Miraj"],
    "meesho":     ["Meesho Store", "Fashion Hub", "Electronics Zone", "HomeDecor"],
    "swiggy":     ["KFC", "McDonald's", "Domino's", "Burger King", "Pizza Hut"],
    "zomato":     ["Zomato Kitchen", "Blinkit", "Hyperpure", "Gold Restaurant"],
    "cred":       ["CRED Store", "CRED Travel", "CRED Pay", "CRED Mint"],
}

BANKS = ["HDFC Bank", "SBI", "ICICI Bank", "Axis Bank", "Kotak Bank",
         "Yes Bank", "PNB", "Bank of Baroda", "Canara Bank", "Union Bank"]

# ─── HELPERS ─────────────────────────────────────────────────

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_fast2sms(mobile, otp):
    """Send OTP via Fast2SMS API"""
    try:
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "otp",
            "variables_values": otp,
            "numbers": mobile,
        }
        headers = {"authorization": FAST2SMS_API_KEY}
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        return data.get("return", False)
    except Exception as e:
        print(f"SMS Error: {e}")
        return False

def simulate_transaction(rrn, app_id):
    """Generate realistic fake transaction data"""
    random.seed(rrn + app_id)  # Same RRN+app always gives same result

    last_digit = int(rrn[-1]) if rrn[-1].isdigit() else 0
    all_same   = len(set(rrn)) == 1

    if all_same or rrn in ["100000","200000","999999"]:
        status = "failed"
    elif last_digit % 2 == 0:
        status = "success"
    else:
        status = "pending"

    merchants = MERCHANTS.get(app_id, ["Unknown Merchant"])
    merchant  = random.choice(merchants)
    bank      = random.choice(BANKS)
    amount    = round(random.uniform(50, 9999), 2)

    # Generate realistic timestamp
    days_ago  = random.randint(0, 30)
    txn_time  = datetime.now() - timedelta(days=days_ago,
                    hours=random.randint(0,23), minutes=random.randint(0,59))

    refund_timeline = None
    if status == "failed":
        refund_timeline = [
            {"step": "Transaction Failed",    "date": txn_time.strftime("%d %b %Y %I:%M %p"),        "done": True},
            {"step": "Refund Initiated",      "date": (txn_time + timedelta(hours=2)).strftime("%d %b %Y %I:%M %p"),  "done": True},
            {"step": "Bank Processing",       "date": (txn_time + timedelta(days=1)).strftime("%d %b %Y"),             "done": days_ago > 2},
            {"step": "Refund Credited",       "date": (txn_time + timedelta(days=5)).strftime("%d %b %Y"),             "done": days_ago > 5},
        ]

    return {
        "rrn":              rrn,
        "app_id":           app_id,
        "app_name":         next((a["name"] for a in PAYMENT_APPS if a["id"] == app_id), app_id),
        "status":           status,
        "amount":           amount,
        "merchant":         merchant,
        "bank":             bank,
        "utr":              ''.join(random.choices(string.digits, k=12)),
        "txn_id":           ''.join(random.choices(string.ascii_uppercase + string.digits, k=16)),
        "timestamp":        txn_time.strftime("%d %b %Y, %I:%M %p"),
        "refund_timeline":  refund_timeline,
        "payment_mode":     random.choice(["UPI", "Debit Card", "Credit Card", "Net Banking"]),
        "vpa":              f"user{random.randint(1000,9999)}@{app_id}",
    }

# ─── ROUTES ──────────────────────────────────────────────────

@app.route("/")
def index():
    if "mobile" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", apps=PAYMENT_APPS)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/send_otp", methods=["POST"])
def send_otp():
    data   = request.get_json()
    mobile = data.get("mobile", "").strip()

    if not mobile.isdigit() or len(mobile) != 10:
        return jsonify({"success": False, "message": "Enter valid 10-digit mobile number."})

    otp = generate_otp()

    # Save OTP to DB
    db.session.add(OTP(mobile=mobile, otp=otp))
    db.session.commit()

    # Try Fast2SMS
    sent = send_otp_fast2sms(mobile, otp)

    # Always return OTP in demo mode if SMS fails
    return jsonify({
        "success": True,
        "message": "OTP sent!" if sent else f"SMS failed. Demo OTP: {otp}",
        "demo_otp": otp  # Remove this in production!
    })

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data   = request.get_json()
    mobile = data.get("mobile", "").strip()
    otp    = data.get("otp", "").strip()

    # Find latest unused OTP
    record = OTP.query.filter_by(mobile=mobile, used=False)\
                      .order_by(OTP.id.desc()).first()

    if not record:
        return jsonify({"success": False, "message": "OTP not found. Request again."})

    # Check expiry (5 minutes)
    if datetime.utcnow() - record.created > timedelta(minutes=5):
        return jsonify({"success": False, "message": "OTP expired. Request a new one."})

    if record.otp != otp:
        return jsonify({"success": False, "message": "Incorrect OTP. Try again."})

    record.used = True
    db.session.commit()

    # Create/get user
    user = User.query.filter_by(mobile=mobile).first()
    if not user:
        user = User(mobile=mobile, name=f"User{mobile[-4:]}")
        db.session.add(user)
        db.session.commit()

    session["mobile"]  = mobile
    session["user_id"] = user.id
    return jsonify({"success": True, "message": "Verified!"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/check_rrn", methods=["POST"])
def check_rrn():
    if "mobile" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data   = request.get_json()
    rrn    = data.get("rrn", "").strip()
    app_id = data.get("app_id", "").strip()

    if not rrn.isdigit() or len(rrn) < 6 or len(rrn) > 15:
        return jsonify({"success": False, "message": "Invalid RRN. Must be 6–15 digits."})
    if not app_id:
        return jsonify({"success": False, "message": "Please select a payment app."})

    result = simulate_transaction(rrn, app_id)

    # Save to DB
    txn = Transaction(
        rrn      = rrn,
        app_name = result["app_name"],
        status   = result["status"],
        amount   = result["amount"],
        merchant = result["merchant"],
        bank     = result["bank"],
        timestamp= result["timestamp"],
        user_id  = session.get("user_id")
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify({"success": True, "data": result})

@app.route("/history")
def history():
    if "mobile" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(mobile=session["mobile"]).first()
    txns = Transaction.query.filter_by(user_id=user.id)\
                            .order_by(Transaction.searched_at.desc()).limit(20).all()
    return render_template("history.html", txns=txns)

# ─── ADMIN ───────────────────────────────────────────────────

ADMIN_PASSWORD = "admin@sru2024"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == ADMIN_PASSWORD:
            session["admin"] = True
        else:
            return render_template("admin_login.html", error="Wrong password")

    if not session.get("admin"):
        return render_template("admin_login.html", error=None)

    users = User.query.order_by(User.created.desc()).all()
    txns  = Transaction.query.order_by(Transaction.searched_at.desc()).limit(50).all()
    stats = {
        "total_users":    User.query.count(),
        "total_searches": Transaction.query.count(),
        "success_count":  Transaction.query.filter_by(status="success").count(),
        "failed_count":   Transaction.query.filter_by(status="failed").count(),
        "pending_count":  Transaction.query.filter_by(status="pending").count(),
    }
    return render_template("admin.html", users=users, txns=txns, stats=stats)

# ─── INIT ────────────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
