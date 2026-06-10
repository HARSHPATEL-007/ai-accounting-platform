-- Seed data for development/testing
-- Note: In production, use Vault-encrypted secrets

INSERT INTO users (id, client_id, role, email, phone, password_hash, mfa_enabled, mfa_type)
VALUES 
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'admin', 'admin@techstart.in', '+91-9999999999', '$2b$12$...', true, 'totp'),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222', 'ca', 'ca@msme.in', '+91-8888888888', '$2b$12$...', false, 'none');

-- Sample ledger entries for TechStart
INSERT INTO ledgers (id, client_id, account_code, transaction_date, transaction_type, amount, description, gstin, hsn_code, gst_rate, gst_amount, reconciliation_status, created_by)
VALUES 
    ('l1', '11111111-1111-1111-1111-111111111111', 'SAL-001', '2024-06-01', 'credit', 50000.00, 'Software development services', '27BBBBB1111B1Z3', '998314', 18.00, 9000.00, 'matched', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
    ('l2', '11111111-1111-1111-1111-111111111111', 'EXP-001', '2024-06-02', 'debit', 15000.00, 'Cloud infrastructure - AWS', NULL, '998315', 18.00, 2700.00, 'pending', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa');
