

def clean_company_name(name: str) -> str:
    """Clean company name for comparison"""
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

def get_flag_color(element):
    classes = element.get_attribute("class")
    if "Green" in classes: return "Green"
    if "Yellow" in classes: return "Yellow"
    if "Orange" in classes: return "Orange"
    if "Red" in classes: return "Red"
    return "Unknown"

