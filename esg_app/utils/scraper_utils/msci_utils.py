''' This module contains helper functions used within msci_threaded.py.'''

def clean_company_name(name: str) -> str:
    """Clean a company name.
    
    Args:
        name (str) : The name of the company to be cleaned.

    Returns:
        (str) : The cleaned company name.
    """
    replacements = {
        'Incorporated': 'Inc',
        'Limited': 'Ltd',
        'PLC': 'Public Limited Company',
        ',' : '',
        '.': '',
        '&': 'and',
        ' Inc': '',
        ' Corp': '',
        ' Ltd': ''
    }
    
    name = name.lower().strip()
    for old, new in replacements.items():
        name = name.replace(old.lower(), new.lower())
    
    return ' '.join(name.split())

def clean_flag_element(element) -> str:
    """Clean a flag's web element.
    
    Args:
        element : The flag web element to be cleaned.

    Returns:
        (str) : The flag color within the web element.
    """
    classes = element.get_attribute("class")
    if "Green" in classes: return "Green"
    if "Yellow" in classes: return "Yellow"
    if "Orange" in classes: return "Orange"
    if "Red" in classes: return "Red"
    return "Unknown"

