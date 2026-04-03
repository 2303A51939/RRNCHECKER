# RRN Status Checker v2.0
### With OTP Login + Database + Admin Panel
**SR University · Karthik (2303A51939)**

---

## 🚀 Setup & Run

```bash
pip install -r requirements.txt
python app.py
# Visit http://127.0.0.1:5000
```

---

## 🔑 Fast2SMS Setup (Free OTP SMS)

1. Go to https://fast2sms.com → Sign up free
2. Dashboard → Dev API → Copy your API key
3. Open app.py → Line 13 → Replace `YOUR_FAST2SMS_API_KEY`

If no API key → OTP is shown on screen (demo mode, perfect for evaluation)

---

## 🔐 Admin Panel

- URL: `/admin`
- Password: `admin@sru2024`

---

## 📂 Structure

```
rrn-v2/
├── app.py
├── requirements.txt
├── instance/
│   └── rrn.db          ← Auto-created SQLite database
└── templates/
    ├── login.html       ← Mobile OTP login
    ├── index.html       ← App selector + RRN checker
    ├── history.html     ← User search history
    ├── admin.html       ← Admin dashboard
    └── admin_login.html ← Admin login
```

---

## 🗄️ Database Tables

| Table | Stores |
|-------|--------|
| User | mobile, name, created date |
| OTP | mobile, otp code, used flag, created time |
| Transaction | rrn, app, merchant, bank, amount, status, user |

---

## 📱 Supported Apps
PhonePe, Paytm, Google Pay, Amazon Pay, BookMyShow, Meesho, Swiggy, Zomato, CRED

---

## 🤖 AI-Assisted Development
Built using Claude (Anthropic) for code generation, UI design, database schema, and OTP integration logic.
