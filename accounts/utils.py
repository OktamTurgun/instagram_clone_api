import phonenumbers
from phonenumbers import NumberParseException
from django.core.exceptions import ValidationError


def validate_phone_number(phone_number, country_code='UZ'):
    """
    Phone number'ni validatsiya qiladi va normalize qiladi.
    
    Args:
        phone_number: str - telefon raqam (any format)
        country_code: str - default country (UZ, RU, US, etc.)
    
    Returns:
        str - Normalized E164 format: +998901234567
    
    Raises:
        ValidationError - Invalid number
    
    Examples:
        validate_phone_number("+998901234567")  # +998901234567
        validate_phone_number("998901234567")   # +998901234567
        validate_phone_number("901234567")      # +998901234567
        validate_phone_number("+998 90 123 45 67")  # +998901234567
    """
    try:
        # Parse qilish
        parsed_number = phonenumbers.parse(phone_number, country_code)
        
        # Valid ekanligini tekshirish
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError("Invalid phone number")
        
        # E164 formatga o'tkazish (+998901234567)
        formatted_number = phonenumbers.format_number(
            parsed_number, 
            phonenumbers.PhoneNumberFormat.E164
        )
        
        return formatted_number
        
    except NumberParseException:
        raise ValidationError("Invalid phone number format")


def format_phone_display(phone_number):
    """
    Phone number'ni user-friendly formatga o'tkazadi.
    
    Examples:
        +998901234567 → +998 90 123-45-67
        +79161234567  → +7 916 123-45-67
    """
    try:
        parsed = phonenumbers.parse(phone_number, None)
        return phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
    except:
        return phone_number


def get_phone_carrier(phone_number):
    """
    Phone operator'ni aniqlaydi (if available in library).
    
    Examples:
        +998901234567 → "UMS" (Beeline)
        +79161234567  → "MTS"
    """
    from phonenumbers import carrier
    
    try:
        parsed = phonenumbers.parse(phone_number, None)
        carrier_name = carrier.name_for_number(parsed, 'en')
        return carrier_name if carrier_name else "Unknown"
    except:
        return "Unknown"


def is_uzbekistan_number(phone_number):
    """
    O'zbekiston raqami ekanligini tekshiradi.
    
    Returns:
        bool: True if Uzbekistan number
    """
    try:
        parsed = phonenumbers.parse(phone_number, None)
        region = phonenumbers.region_code_for_number(parsed)
        return region == 'UZ'
    except:
        return False


def get_phone_country(phone_number):
    """
    Phone number mamlakati.
    
    Returns:
        str: Country code (UZ, RU, US, etc.)
    """
    try:
        parsed = phonenumbers.parse(phone_number, None)
        return phonenumbers.region_code_for_number(parsed)
    except:
        return "Unknown"


# O'zbekiston operator kodlari
UZ_OPERATORS = {
    '90': 'Beeline',
    '91': 'Ucell',
    '93': 'Ucell',
    '94': 'Ucell',
    '95': 'Uzmobile',
    '97': 'Uzmobile',
    '98': 'Perfectum',
    '99': 'Uzmobile',
    '88': 'Uzmobile',
    '33': 'Uztel',
}


def get_uzbek_operator(phone_number):
    """
    O'zbekiston operator'ini aniqlaydi.
    
    Examples:
        +998901234567 → Beeline
        +998911234567 → Ucell
        +998951234567 → Uzmobile
    
    Returns:
        str: Operator name or "Unknown"
    """
    try:
        # +998XX formatdan operator kodini olish
        if phone_number.startswith('+998') and len(phone_number) >= 6:
            operator_code = phone_number[4:6]
            return UZ_OPERATORS.get(operator_code, 'Unknown')
        
        # Agar +998 bilan boshlanmasa
        parsed = phonenumbers.parse(phone_number, 'UZ')
        formatted = phonenumbers.format_number(
            parsed, 
            phonenumbers.PhoneNumberFormat.E164
        )
        
        if formatted.startswith('+998') and len(formatted) >= 6:
            operator_code = formatted[4:6]
            return UZ_OPERATORS.get(operator_code, 'Unknown')
            
    except:
        pass
    
    return 'Unknown'


def validate_uzbek_phone(phone_number):
    """
    Faqat O'zbekiston raqamlarini qabul qiladi.
    
    Raises:
        ValidationError: If not Uzbekistan number
    """
    normalized = validate_phone_number(phone_number, 'UZ')
    
    if not is_uzbekistan_number(normalized):
        raise ValidationError("Only Uzbekistan phone numbers are allowed")
    
    return normalized