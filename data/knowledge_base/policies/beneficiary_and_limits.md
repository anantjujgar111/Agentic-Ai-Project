# Beneficiary And Limits Policy

This synthetic policy explains how the assistant should discuss beneficiary setup and transaction limits.

## Beneficiary setup

Beneficiary setup requires beneficiary name, account number, IFSC, bank name, and customer confirmation. Production banking systems usually include a cooling period or lower initial limit for newly added beneficiaries.

## Limit changes

Debit card and fund-transfer limit changes should require authentication and risk checks. The POC can simulate the update but must label it as a mock action.

## Audit requirement

Every sensitive action should create a tool trace with input, output, customer id, timestamp, and status. The chatbot response should not expose internal secrets or full account numbers.
