"""Discount service with intentional logic error."""

def calculate_discounted_price(price: float, discount_rate: float) -> float:
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not (0 <= discount_rate <= 1):
        raise ValueError("Discount rate must be between 0 and 1")
    
    # BUG: Logic error! Adds discount instead of subtracting it!
    return price + (price * discount_rate)

