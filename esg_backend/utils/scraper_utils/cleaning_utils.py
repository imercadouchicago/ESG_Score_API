''' This module contains helper functions for cleaning company names and flag elements.'''

def clean_company_name(name: str) -> str:
    """Clean a company's name.
    
    Args:
        name: [str] Name to be cleaned.

    Returns:
        [str] : Cleaned name.
    """

    # Convert to title case first to standardize
    name = name.title()
    
    # Do replacements with case variations
    name = name.replace("The", "").strip()
    name = name.replace(".", "").replace(",", "")
    name = " ".join(name.split())
    name = name.replace("Corporation", "Corp").replace("CORPORATION", "Corp")
    name = name.replace("Company", "Co").replace("COMPANY", "Co")
    name = name.replace("Incorporated", "Inc").replace("INCORPORATED", "Inc")
    name = name.replace('"', '')

    return name

def clean_flag_element(element) -> str:
    """Clean a flag's web element.
    
    Args:
        element: [element] The flag web element to be cleaned.

    Returns:
        [str] : The flag color within the web element.
    """
    classes = element.get_attribute("class")
    if "Green" in classes: return "Green"
    if "Yellow" in classes: return "Yellow"
    if "Orange" in classes: return "Orange"
    if "Red" in classes: return "Red"
    return "Unknown"

def csrhub_clean_company_name(name: str) -> str:
    """Clean a company's name.
    
    Args:
        name: [str] Name to be cleaned.

    Returns:
        [str] : Cleaned name.
    """
    
    replacements = {
        'Corporation': 'Corp',
        'Incorporated': 'Inc',
        'Limited': 'Ltd',
        ',': '',
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