#=== Required Imports for Security and Email ===#
import hashlib
import secrets
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from flask import Blueprint, request, jsonify, session, flash
from datetime import datetime

#=== IMPORTANT: Define the Blueprint first to fix NameError ===#
vendor_api = Blueprint('vendor_api', __name__)

#=== Database Settings ===#
DATABASE = 'sooqkabeer.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

#=== Vendor Security Decorator ===#
def vendor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('vendor_id'):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

#=== Email Configuration ===#
EMAIL_SENDER = "support@sooqkabeer.com"
EMAIL_PASSWORD = "your-app-password"

#=== Payout Email Function ===#
def send_payout_email(vendor_email, vendor_name, amount, ref_no):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = vendor_email
        msg['Subject'] = f"Payout Request Received - {ref_no}"
        
        body = f"Dear {vendor_name},\n\nRequest received for {amount} KWD.\nRef: {ref_no}"
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"#=== EMAIL ERROR: {str(e)} ===#")
        return False

#=== Now your routes below will work fine ===#

def send_payout_email(vendor_email, vendor_name, amount, ref_no):
    """Sends a professional email confirmation for payout requests"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = vendor_email
        msg['Subject'] = f"Payout Request Received - {ref_no}"

        body = f"""
        Dear {vendor_name},

        We have received your payout request. Here are the details:
        
        #=== Transaction Details ===#
        Reference No: {ref_no}
        Amount: {amount} KWD
        Status: Pending
        Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Our team will review your request and process the payment soon. 
        You will receive another update once it's completed.

        Thank you for being with Sooq Kabeer!
        """
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {str(e)}")
        return False

@vendor_api.route('/api/vendor/request-payout', methods=['POST'])
@vendor_required
def request_payout():
    """Handles payout requests and sends email notification"""
    vendor_id = session.get('vendor_id')
    vendor_email = session.get('vendor_email') # Ensure this is in session
    vendor_name = session.get('vendor_name')
    data = request.json
    
    try:
        amount = float(data.get('amount', 0))
        if amount <= 0:
            return jsonify({'status': 'error', 'message': 'Invalid amount'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT vendor_id_code FROM users WHERE id = ?", (vendor_id,))
        vendor_code = cursor.fetchone()['vendor_id_code']
        
        ref_no = f"PAY-{vendor_code}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Insert Payout Transaction
        cursor.execute("""
            INSERT INTO transactions (vendor_id, type, amount, status, reference_no)
            VALUES (?, 'payout', ?, 'pending', ?)
        """, (vendor_id, amount, ref_no))
        
        conn.commit()
        conn.close()

        # Send Email Notification
        send_payout_email(vendor_email, vendor_name, amount, ref_no)
        
        return jsonify({
            'status': 'success',
            'message': 'Payout request submitted and email sent',
            'reference': ref_no
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
#=============================================
# Vendor Payout Methods Management
#=============================================
@vendor_api.route('/api/vendor/payout-methods', methods=['GET'])
@vendor_required
def get_payout_methods():
    """Returns list of saved payout methods for the vendor"""
    vendor_id = session.get('vendor_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetching all saved methods (Bank, Mobile, etc.)
        cursor.execute("""
            SELECT id, method_type, account_name, account_number, bank_name, is_verified 
            FROM vendor_payout_methods WHERE vendor_id = ?
        """, (vendor_id,))
        methods = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': [dict(m) for m in methods]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@vendor_api.route('/api/vendor/add-payout-method', methods=['POST'])
@vendor_required
def add_payout_method():
    """Saves new bank or payment info for the vendor"""
    vendor_id = session.get('vendor_id')
    vendor_code = session.get('vendor_custom_id') # HKO-XXXXX
    data = request.json
    
    try:
        method_type = data.get('method_type') # e.g., 'bank'
        acc_name = data.get('account_name')
        acc_number = data.get('account_number')
        bank_name = data.get('bank_name')
        
        if not all([method_type, acc_name, acc_number]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Inserting new payout method
        cursor.execute("""
            INSERT INTO vendor_payout_methods 
            (vendor_id, vendor_code, method_type, account_name, account_number, bank_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, vendor_code, method_type, acc_name, acc_number, bank_name))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': 'Payout method added successfully. Waiting for verification.',
            'arabic_message': 'تمت إضافة طريقة الدفع بنجاح. بانتظار التأكيد.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

