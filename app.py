import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "walletfindx_secret_key")

# Configure server-side session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Define premium codes
PERMANENT_CODE = "PKN2384QSX"
LIMITED_CODES = [f"QSXCGU{i:04d}" for i in range(1, 10000)]

# Store used limited codes to prevent reuse
USED_CODES = set()

# Routes
@app.route("/")
def index():
    # Clear session if user is accessing the homepage (to simulate logout)
    if 'premium_code' in session:
        return redirect(url_for('crypto_select'))
    return render_template("index.html")

@app.route("/verify_code", methods=["POST"])
def verify_code():
    premium_code = request.form.get("premium_code")
    
    # Check if code is valid
    if premium_code == PERMANENT_CODE:
        session["premium_code"] = premium_code
        session["is_permanent"] = True
        session["scans_used"] = 0
        session["scans_remaining"] = float('inf')
        return redirect(url_for("crypto_select"))
    elif premium_code in LIMITED_CODES and premium_code not in USED_CODES:
        # Mark code as used
        USED_CODES.add(premium_code)
        
        session["premium_code"] = premium_code
        session["is_permanent"] = False
        session["scans_used"] = 0
        session["scans_remaining"] = 5
        return redirect(url_for("crypto_select"))
    else:
        flash("Invalid premium code or code has already been used. Please try again.", "error")
        return redirect(url_for("index"))

@app.route("/crypto_select")
def crypto_select():
    # Check if user has a valid premium code
    if "premium_code" not in session:
        return redirect(url_for("index"))
    
    return render_template("crypto_select.html")

@app.route("/select_crypto", methods=["POST"])
def select_crypto():
    crypto = request.form.get("crypto")
    if crypto in ["BTC", "ETH", "USDT"]:
        session["selected_crypto"] = crypto
        return redirect(url_for("scan"))
    
    flash("Invalid cryptocurrency selection.", "error")
    return redirect(url_for("crypto_select"))

@app.route("/scan")
def scan():
    # Check if user has a valid premium code and selected crypto
    if "premium_code" not in session:
        return redirect(url_for("index"))
    
    if "selected_crypto" not in session:
        return redirect(url_for("crypto_select"))
    
    selected_crypto = session["selected_crypto"]
    scans_used = session.get("scans_used", 0)
    scans_remaining = session.get("scans_remaining", 0)
    
    return render_template("scan.html", 
                          selected_crypto=selected_crypto,
                          scans_used=scans_used,
                          scans_remaining=scans_remaining)

@app.route("/perform_scan", methods=["POST"])
def perform_scan():
    # Check if user has a valid premium code
    if "premium_code" not in session:
        return {"success": False, "message": "Not authenticated"}, 401
    
    # Check if user has scans remaining
    if not session.get("is_permanent", False) and session.get("scans_remaining", 0) <= 0:
        return {"success": False, "message": "No scans remaining"}, 403
    
    # Update scan count
    if not session.get("is_permanent", False):
        session["scans_used"] = session.get("scans_used", 0) + 1
        session["scans_remaining"] = session.get("scans_remaining", 5) - 1
    
    # In a real app, this would perform actual scanning
    # For this simulation, we just return success
    return {"success": True, "scans_used": session.get("scans_used", 0), 
            "scans_remaining": session.get("scans_remaining", 0)}

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
