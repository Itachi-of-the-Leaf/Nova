import re

texts = [
    "We investigate the variable IINo in the subset M.",
    "The function sup(D) is defined.",
    "Let V be a vector space, and x be an element.",
    "Standard text with no math. Some 123 numbers. A sentence."
]

def wrap_math(text: str) -> str:
    # Match isolated single letters (case-sensitive, usually variables if capitalized or certain lowercase)
    # Match strings ending in numbers like IINo if they look like variables
    # Match functions like sup(D)
    
    # 1. Single letter variables (A-Z, or specific math letters like x, y, z, i, j, k, n, m) surrounded by spaces
    text = re.split(r'(\s)(IINo|sup\([A-Za-z0-9]+\)|[A-Z]|[xyzijknm])([.,;:\s]|$)', text)
    
    # Reconstruct
    res = ""
    for i, part in enumerate(text):
        if i % 4 == 2:  # The matched variable
            if part in ['A', 'I']: # Exclude common English words
                res += part
            else:
                res += f"${part}$"
        else:
            res += part
    
    # Simple regex replace for more complex ones
    res = re.sub(r'\b(IINo|sup\([A-Za-z0-9]+\))\b', r'$\1$', res)
    
    return res.replace('$$', '$')

for t in texts:
    print("ORIG:", t)
    print("MATH:", wrap_math(t))
    print()
