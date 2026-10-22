import re

KYC_PATTERNS = {
    'pan_card': {
        'name': 'PAN Card (Permanent Account Number)',
        'regex': r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
        'example': 'ABCDE1234F',
        'hint': 'Must be 10 characters: 5 uppercase letters, 4 digits, and 1 uppercase letter (e.g., ABCDE1234F).'
    },
    'passport': {
        'name': 'Indian / International Passport',
        'regex': r'^[A-Z]{1}[0-9]{7}$',
        'example': 'Z1234567',
        'hint': 'Must be 8 characters: 1 uppercase letter followed by 7 digits (e.g., Z1234567).'
    },
    'voter_id': {
        'name': 'Voter ID / Election Card (EPIC)',
        'regex': r'^[A-Z]{3}[0-9]{7}$|^[A-Z0-9]{10,16}$',
        'example': 'ABC1234567',
        'hint': 'Must be 3 letters followed by 7 digits (e.g., ABC1234567) or 10–16 alphanumeric characters.'
    },
    'driving_license': {
        'name': 'Driving Licence',
        'regex': r'^[A-Z]{2}[0-9]{2}[0-9A-Z]{7,12}$',
        'example': 'KL0720210001234',
        'hint': 'Must start with a 2-letter state code followed by RTO and licence digits (e.g., KL0720210001234).'
    }
}

VALID_DISTRICTS = ['Ernakulam', 'Thrissur']


def validate_full_name(full_name):
    """
    Validates full legal name:
    - 2 to 100 characters.
    - Letters, spaces, hyphens, periods, and apostrophes only.
    - Must contain at least two alphabetic letters.
    """
    if not full_name or not isinstance(full_name, str):
        return False, "Full Legal Name is required."
    
    cleaned = full_name.strip()
    if len(cleaned) < 2:
        return False, "Full Name must be at least 2 characters long."
    if len(cleaned) > 100:
        return False, "Full Name cannot exceed 100 characters."
    
    # Must only contain valid name characters
    if not re.match(r"^[A-Za-z\s\.\-']+$", cleaned):
        return False, "Full Name should only contain letters, spaces, hyphens, and periods."
    
    # Must have at least two alphabetic characters
    letter_count = len(re.findall(r'[A-Za-z]', cleaned))
    if letter_count < 2:
        return False, "Full Name must contain at least two letters."
        
    return True, None


def validate_email(email):
    """
    Validates email format:
    - Standard RFC email regex.
    - Max 150 characters.
    """
    if not email or not isinstance(email, str):
        return False, "Email address is required."
        
    cleaned = email.strip().lower()
    if len(cleaned) > 150:
        return False, "Email address cannot exceed 150 characters."
        
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, cleaned):
        return False, "Please enter a valid email address (e.g., name@example.com)."
        
    return True, None


def validate_phone(phone):
    """
    Validates Indian phone numbers:
    - Allows optional +91, 91, or 0 prefix.
    - 10 digits starting with 6, 7, 8, or 9.
    Returns (is_valid, error_msg, normalized_phone).
    """
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required.", None
        
    raw = phone.strip()
    # Strip spaces, hyphens, parentheses
    digits = re.sub(r'[\s\-\(\)]', '', raw)
    
    # Remove leading +91 or 91 or 0 if 10-digit mobile follows
    if digits.startswith('+91') and len(digits) == 13:
        digits = digits[3:]
    elif digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
        
    if not re.match(r'^[6-9]\d{9}$', digits):
        return False, "Please enter a valid 10-digit Indian mobile number (e.g., +91 98470 00000).", None
        
    # Standardized format
    formatted = f"+91 {digits[:5]} {digits[5:]}"
    return True, None, formatted


def validate_password(password, confirm_password):
    """
    Validates password strength and matching confirmation:
    - At least 6 characters.
    - Matches confirm_password.
    """
    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if password != confirm_password:
        return False, "Passwords do not match. Please re-enter your password."
    return True, None


def validate_kyc(document_type, document_number):
    """
    Validates Government KYC identity document:
    - Supported types: pan_card, passport, voter_id, driving_license.
    - Normalizes document number to uppercase and stripped of whitespace.
    - Validates against standard official regex.
    Returns (is_valid, error_msg, cleaned_number).
    """
    if not document_type or not str(document_type).strip():
        return False, "Please select your Government KYC Document Type (PAN Card, Passport, Voter ID, or Driving Licence).", None
        
    doc_type = str(document_type).strip().lower()
    if doc_type not in KYC_PATTERNS:
        valid_types = ", ".join([v['name'] for v in KYC_PATTERNS.values()])
        return False, f"Unsupported KYC document type. Please select from: {valid_types}.", None
        
    pattern_info = KYC_PATTERNS[doc_type]
    
    if not document_number or not str(document_number).strip():
        return False, f"Please enter your {pattern_info['name']} number.", None
        
    # Strip whitespace, spaces, hyphens and uppercase
    cleaned_num = re.sub(r'[\s\-]', '', str(document_number).strip()).upper()
    
    if not re.match(pattern_info['regex'], cleaned_num):
        return False, f"Invalid {pattern_info['name']} format. {pattern_info['hint']}", None
        
    return True, None, cleaned_num


def validate_owner_fields(business_name, district, full_name=""):
    """
    Validates owner specific fields:
    - Operational district must be Ernakulam or Thrissur.
    - Sanitizes business name or defaults nicely.
    Returns (is_valid, error_msg, cleaned_business_name, cleaned_district).
    """
    cleaned_dist = (district or 'Ernakulam').strip()
    if cleaned_dist not in VALID_DISTRICTS:
        return False, "Operational district must be either Ernakulam or Thrissur.", None, None
        
    cleaned_biz = (business_name or '').strip()
    if not cleaned_biz:
        cleaned_biz = f"{full_name.strip()}'s Heritage Rentals" if full_name else "Kerala Heritage Rentals"
    elif len(cleaned_biz) > 150:
        return False, "Business Name cannot exceed 150 characters.", None, None
        
    return True, None, cleaned_biz, cleaned_dist
