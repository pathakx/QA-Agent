# Product Specifications & Rules

## Discount Codes
- **SAVE15**: Applies a 15% discount to the subtotal (before shipping).
- Invalid codes should show an error message.

## Shipping
- **Standard Shipping**: Free ($0).
- **Express Shipping**: Flat rate of $10.00.

## Cart Logic
- Items can be added multiple times; quantity should increment.
- Total price = (Subtotal * (1 - Discount)) + Shipping.

## Checkout Flow
- User must fill in all required fields: Name, Email, Address.
- Email must contain "@" and ".".
- Payment is simulated; no actual processing occurs.
- Successful payment displays "Payment Successful!" message.
