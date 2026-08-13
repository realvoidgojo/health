def format_inr(amount: float) -> str:
    """Formats a float to INR currency string."""
    try:
        amt = float(amount)
        is_negative = amt < 0
        s, *d = str(abs(amt)).split('.')
        d = d[0] if d else '00'
        if len(d) == 1:
            d += '0'
        
        # Indian format: last 3 digits, then groups of 2
        if len(s) > 3:
            last_3 = s[-3:]
            remaining = s[:-3]
            # Group the remaining by 2 from the right
            groups = []
            while remaining:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            groups.reverse()
            s = ",".join(groups) + "," + last_3
            
        prefix = "₹-" if is_negative else "₹"
        return f"{prefix}{s}.{d}"
    except (ValueError, TypeError):
        return "₹0.00"
