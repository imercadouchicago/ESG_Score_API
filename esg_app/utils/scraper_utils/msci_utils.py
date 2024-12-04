''' This module contains helper functions used within msci_threaded.py.'''

def clean_company_name(name: str) -> str:
    """Simple cleaning of company names"""
    original = name
    
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
