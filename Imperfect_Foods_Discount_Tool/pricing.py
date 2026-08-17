def calculate_dynamic_discount(item):
    """Calculates dynamic discount based on days left to expiry and cosmetic grade."""
    base_discount = 0.0

    # Days_left discount
    if item['days_left'] <= 2:
        base_discount += 45.0
    elif item['days_left'] <= 4:
        base_discount += 30.0
    else:
        base_discount += 15.0

    # Grade defect discount
    if item['grade'] == 'C':
        base_discount += 25.0
    elif item['grade'] == 'B':
        base_discount += 15.0
    elif item['grade'] == 'A':
        base_discount += 5.0

    # Max discount is 80%
    final_discount = min(base_discount, 80.0)
    new_price = item['original_price'] * (1 - (final_discount / 100))

    item['discount_percent'] = final_discount
    item['new_price'] = round(new_price, 2)
    return item