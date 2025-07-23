"""
JazzCash API Client for payment verification
"""
import requests
import hashlib
import urllib.parse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JazzCashClient:
    def __init__(self, merchant_id, password, integrity_salt, api_url, return_url):
        self.merchant_id = merchant_id
        self.password = password
        self.integrity_salt = integrity_salt
        self.api_url = api_url
        self.return_url = return_url
    
    def generate_secure_hash(self, data_string):
        """Generate secure hash for JazzCash API calls"""
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest().upper()
    
    def create_payment_request(self, transaction_id, amount, mobile_number, description="Full Access Payment"):
        """
        Create a payment request for JazzCash
        Returns payment URL and transaction data
        """
        try:
            # Prepare payment data
            payment_data = {
                'pp_Version': '1.1',
                'pp_TxnType': 'MWALLET',
                'pp_Language': 'EN',
                'pp_MerchantID': self.merchant_id,
                'pp_SubMerchantID': '',
                'pp_Password': self.password,
                'pp_BankID': 'TBANK',
                'pp_ProductID': 'RETL',
                'pp_TxnRefNo': transaction_id,
                'pp_Amount': str(int(amount * 100)),  # Amount in paisa
                'pp_TxnCurrency': 'PKR',
                'pp_TxnDateTime': datetime.now().strftime('%Y%m%d%H%M%S'),
                'pp_BillReference': transaction_id,
                'pp_Description': description,
                'pp_TxnExpiryDateTime': '',
                'pp_ReturnURL': self.return_url,
                'pp_SecureHash': '',
                'ppmpf_1': mobile_number,  # Customer mobile number
                'ppmpf_2': '',
                'ppmpf_3': '',
                'ppmpf_4': '',
                'ppmpf_5': ''
            }
            
            # Create hash string
            hash_string = f"{self.integrity_salt}&{payment_data['pp_Amount']}&{payment_data['pp_BankID']}&{payment_data['pp_BillReference']}&{payment_data['pp_Description']}&{payment_data['pp_Language']}&{payment_data['pp_MerchantID']}&{payment_data['pp_Password']}&{payment_data['pp_ProductID']}&{payment_data['pp_ReturnURL']}&{payment_data['pp_SubMerchantID']}&{payment_data['pp_TxnCurrency']}&{payment_data['pp_TxnDateTime']}&{payment_data['pp_TxnExpiryDateTime']}&{payment_data['pp_TxnRefNo']}&{payment_data['pp_TxnType']}&{payment_data['pp_Version']}&{payment_data['ppmpf_1']}&{payment_data['ppmpf_2']}&{payment_data['ppmpf_3']}&{payment_data['ppmpf_4']}&{payment_data['ppmpf_5']}"
            
            payment_data['pp_SecureHash'] = self.generate_secure_hash(hash_string)
            
            return payment_data
            
        except Exception as e:
            logger.error(f"Error creating payment request: {str(e)}")
            return None
    
    def verify_transaction(self, transaction_id):
        """
        Verify transaction status with JazzCash
        Returns (success: bool, response_data: dict)
        """
        try:
            # Prepare inquiry data
            inquiry_data = {
                'pp_Version': '1.1',
                'pp_TxnType': 'INQUIRY',
                'pp_Language': 'EN',
                'pp_MerchantID': self.merchant_id,
                'pp_Password': self.password,
                'pp_TxnRefNo': transaction_id,
                'pp_SecureHash': ''
            }
            
            # Create hash string for inquiry
            hash_string = f"{self.integrity_salt}&{inquiry_data['pp_Language']}&{inquiry_data['pp_MerchantID']}&{inquiry_data['pp_Password']}&{inquiry_data['pp_TxnRefNo']}&{inquiry_data['pp_TxnType']}&{inquiry_data['pp_Version']}"
            
            inquiry_data['pp_SecureHash'] = self.generate_secure_hash(hash_string)
            
            # Make API call
            response = requests.post(
                self.api_url,
                data=inquiry_data,
                timeout=30,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                # Parse response (JazzCash typically returns form data)
                response_data = {}
                for line in response.text.split('&'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_data[key] = urllib.parse.unquote_plus(value)
                
                # Check if transaction was successful
                if response_data.get('pp_ResponseCode') == '000':
                    logger.info(f"Transaction {transaction_id} verified successfully")
                    return True, response_data
                else:
                    logger.warning(f"Transaction {transaction_id} failed with code: {response_data.get('pp_ResponseCode')}")
                    return False, response_data
            else:
                logger.error(f"API request failed with status: {response.status_code}")
                return False, {'error': 'API request failed'}
                
        except requests.RequestException as e:
            logger.error(f"Network error during transaction verification: {str(e)}")
            return False, {'error': 'Network error'}
        except Exception as e:
            logger.error(f"Error verifying transaction: {str(e)}")
            return False, {'error': str(e)}
    
    def verify_callback_response(self, callback_data):
        """
        Verify callback response from JazzCash
        Returns (success: bool, transaction_data: dict)
        """
        try:
            # Extract data from callback
            required_fields = ['pp_TxnRefNo', 'pp_Amount', 'pp_ResponseCode', 'pp_SecureHash']
            
            for field in required_fields:
                if field not in callback_data:
                    return False, {'error': f'Missing required field: {field}'}
            
            # Verify secure hash
            hash_fields = [
                'pp_Amount', 'pp_BankID', 'pp_BillReference', 'pp_Description',
                'pp_Language', 'pp_MerchantID', 'pp_Password', 'pp_ProductID',
                'pp_ResponseCode', 'pp_ResponseMessage', 'pp_ReturnURL',
                'pp_SubMerchantID', 'pp_TxnCurrency', 'pp_TxnDateTime',
                'pp_TxnRefNo', 'pp_TxnType', 'pp_Version'
            ]
            
            hash_string = self.integrity_salt
            for field in hash_fields:
                hash_string += f"&{callback_data.get(field, '')}"
            
            calculated_hash = self.generate_secure_hash(hash_string)
            
            if calculated_hash != callback_data.get('pp_SecureHash'):
                return False, {'error': 'Invalid secure hash'}
            
            # Check if transaction was successful
            if callback_data.get('pp_ResponseCode') == '000':
                return True, callback_data
            else:
                return False, {'error': f"Transaction failed: {callback_data.get('pp_ResponseMessage')}"}
                
        except Exception as e:
            logger.error(f"Error verifying callback response: {str(e)}")
            return False, {'error': str(e)}
