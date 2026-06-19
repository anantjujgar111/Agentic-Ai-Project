# Payment Methods

The smart payments agent can recommend a payment rail based on amount, urgency, beneficiary status, and cost.

## UPI

UPI is recommended for low-value instant bill payments and peer transfers where UPI is accepted.

## IMPS

IMPS is useful for instant transfers to bank accounts, especially when UPI is not suitable or when the amount is higher.

## NEFT

NEFT is recommended for scheduled or non-urgent transfers. It works in settlement batches and can be useful for recurring instructions.

## RTGS

RTGS is recommended for high-value same-day transfers. Production systems must check minimum transfer amount, bank limits, beneficiary activation, and cut-off windows.

## Payment date optimization

The assistant should recommend paying one or two days before the due date to avoid penalties, while considering salary date, cash-flow, and weekend or holiday risk.
