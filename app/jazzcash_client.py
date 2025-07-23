import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from flask import current_app
import secrets
import string


class JazzCashClient:
    """JazzCash API client for handling payment transactions"""
    
    def __init__(self):
        self.merchant_id = current_app.config['JAZZCASH_MERCHANT_ID']
        self.password = current_app.config['JAZZCASH_PASSWORD']
        self.integrity_salt = current_app.config['JAZZCASH_INTEGRITY_SALT']
        self.api_url = current_app.config['JAZZCASH_API_URL']
        self.inquiry_url = current_app.config['JAZZCASH_INQUIRY_URL']
        self.return_url = current_app.config['JAZZCASH_RETURN_URL']
        self.version = current_app.config['JAZZCASH_VERSION']
        self.language = current_app.config['JAZZCASH_LANGUAGE']
        self.currency = current_app.config['JAZZCASH_CURRENCY']
    
    def generate_transaction_id(self):
        """Generate a unique transaction ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f'TXN{timestamp}{random_suffix}'
    
    def generate_secure_hash(self, data_dict):
        """Generate secure hash for JazzCash API authentication"""
        # Sort the dictionary by keys
        sorted_data = sorted(data_dict.items())
        
        # Create string for hash generation
        hash_string = '&'.join([f'{key}={value}' for key, value in sorted_data])
        hash_string += f'&{self.integrity_salt}'
        
        # Generate SHA256 hash
        secure_hash = hashlib.sha256(hash_string.encode('utf-8')).hexdigest().upper()
        return secure_hash
    
    def create_payment_request(self, user_id, amount=3, description="Profile Access Payment"):
        """Create payment request data for JazzCash"""
        transaction_id = self.generate_transaction_id()
        
        # Calculate expiry date (1 hour from now)
        expiry_date = datetime.now() + timedelta(hours=1)
        
        # Prepare payment data
        payment_data = {
            'pp_Version': self.version,
            'pp_TxnType': 'MWALLET',
            'pp_Language': self.language,
            'pp_MerchantID': self.merchant_id,
            'pp_SubMerchantID': '',
            'pp_Password': self.password,
            'pp_BankID': 'TBANK',
            'pp_ProductID': 'RETL',
            'pp_TxnRefNo': transaction_id,
            'pp_Amount': str(amount * 100),  # Amount in paisas (PKR * 100)
            'pp_TxnCurrency': self.currency,
            'pp_TxnDateTime': datetime.now().strftime('%Y%m%d%H%M%S'),
            'pp_BillReference': f'user_{user_id}',
            'pp_Description': description,
            'pp_TxnExpiryDateTime': expiry_date.strftime('%Y%m%d%H%M%S'),
            'pp_ReturnURL': self.return_url,
            'pp_SecureHash': '',
            'ppmpf_1': str(user_id),  # Store user_id for reference
            'ppmpf_2': '',
            'ppmpf_3': '',
            'ppmpf_4': '',
            'ppmpf_5': ''
        }
        
        # Generate secure hash
        payment_data['pp_SecureHash'] = self.generate_secure_hash(payment_data)
        
        return {
            'transaction_id': transaction_id,
            'payment_data': payment_data,
            'api_url': self.api_url
        }
    
    def verify_callback_response(self, response_data):
        """Verify the callback response from JazzCash"""
        try:
            # Extract secure hash from response
            received_hash = response_data.get('pp_SecureHash', '')
            
            # Remove secure hash from data for verification
            verification_data = response_data.copy()
            if 'pp_SecureHash' in verification_data:
                del verification_data['pp_SecureHash']
            
            # Calculate expected hash
            expected_hash = self.generate_secure_hash(verification_data)
            
            # Verify hash
            if received_hash.upper() != expected_hash.upper():
                return {'success': False, 'error': 'Invalid secure hash'}
            
            # Check response code
            response_code = response_data.get('pp_ResponseCode', '')
            if response_code == '000':
                return {
                    'success': True,
                    'transaction_id': response_data.get('pp_TxnRefNo'),
                    'user_id': response_data.get('ppmpf_1'),
                    'amount': float(response_data.get('pp_Amount', 0)) / 100,  # Convert from paisas to PKR
                    'response_message': response_data.get('pp_ResponseMessage', ''),
                    'auth_code': response_data.get('pp_AuthCode', ''),
                    'retrieval_reference_no': response_data.get('pp_RetreivalReferenceNo', '')
                }
            else:
                return {
                    'success': False,
                    'error': response_data.get('pp_ResponseMessage', 'Payment failed'),
                    'response_code': response_code
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Verification error: {str(e)}'}
    
    def verify_transaction(self, transaction_id):
        """Verify transaction status using JazzCash inquiry API"""
        try:
            inquiry_data = {
                'pp_Version': self.version,
                'pp_Language': self.language,
                'pp_MerchantID': self.merchant_id,
                'pp_Password': self.password,
                'pp_TxnRefNo': transaction_id,
                'pp_SecureHash': ''
            }
            
            # Generate secure hash for inquiry
            inquiry_data['pp_SecureHash'] = self.generate_secure_hash(inquiry_data)
            
            # Make API request
            response = requests.post(self.inquiry_url, data=inquiry_data, timeout=30)
            
            if response.status_code == 200:
                # Parse response (assuming it's form-encoded or similar)
                response_data = {}
                for line in response.text.split('&'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_data[key] = value
                
                return self.verify_callback_response(response_data)
            else:
                return {'success': False, 'error': f'API request failed: {response.status_code}'}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Inquiry error: {str(e)}'}
