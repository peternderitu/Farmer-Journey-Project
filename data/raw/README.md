# Simulated farmer data pack (practice only)
All people, IDs, phone numbers and amounts are SIMULATED. Nothing here is real data from Vermi-Farm Initiative or any employer.
Regenerate with: python generate_data.py (pandas and numpy required).

Tables: farmers, village_champions, training_sessions, attendance, sales, wallet_transactions, outcomes, finance_ledger
Keys: farmers.farmer_id links to attendance, sales, wallet_transactions, outcomes. attendance.session_id links to training_sessions.
finance_ledger = finance's monthly total by product, to reconcile against sales.

Do not open ANSWER_KEY_planted_errors.csv until you have built your own data quality checks.
Then compare your data quality log with the key. Finding what is NOT in the key is a bonus.
Suggested indicator definitions are in the build guide you received in chat.
