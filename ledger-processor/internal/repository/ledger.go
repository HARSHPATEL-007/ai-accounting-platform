package repository

import (
	"context"
	"fmt"
	"time"

	"ledger-processor/internal/models"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/shopspring/decimal"
)

type LedgerRepository struct {
	pool *pgxpool.Pool
}

func NewLedgerRepository(pool *pgxpool.Pool) *LedgerRepository {
	return &LedgerRepository{pool: pool}
}

func (r *LedgerRepository) Create(ctx context.Context, entry *models.LedgerEntry) error {
	query := `
		INSERT INTO ledgers (
			id, client_id, account_code, transaction_date, transaction_type,
			amount, description, gstin, hsn_code, gst_rate, gst_amount,
			reconciliation_status, bank_transaction_id, document_id, metadata,
			created_by, created_at, updated_at, immutable_hash
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
	`

	_, err := r.pool.Exec(ctx, query,
		entry.ID, entry.ClientID, entry.AccountCode, entry.TransactionDate, entry.TransactionType,
		entry.Amount, entry.Description, entry.GSTIN, entry.HSNCode, entry.GSTRate, entry.GSTAmount,
		entry.ReconciliationStatus, entry.BankTransactionID, entry.DocumentID, entry.Metadata,
		entry.CreatedBy, entry.CreatedAt, entry.UpdatedAt, entry.ImmutableHash,
	)
	return err
}

func (r *LedgerRepository) GetByClientID(ctx context.Context, clientID uuid.UUID, limit, offset int) ([]models.LedgerEntry, error) {
	query := `
		SELECT id, client_id, account_code, transaction_date, transaction_type,
			amount, description, gstin, hsn_code, gst_rate, gst_amount,
			total_amount, reconciliation_status, bank_transaction_id, document_id,
			metadata, created_by, created_at, updated_at, immutable_hash
		FROM ledgers
		WHERE client_id = $1
		ORDER BY transaction_date DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := r.pool.Query(ctx, query, clientID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []models.LedgerEntry
	for rows.Next() {
		var entry models.LedgerEntry
		err := rows.Scan(
			&entry.ID, &entry.ClientID, &entry.AccountCode, &entry.TransactionDate, &entry.TransactionType,
			&entry.Amount, &entry.Description, &entry.GSTIN, &entry.HSNCode, &entry.GSTRate, &entry.GSTAmount,
			&entry.TotalAmount, &entry.ReconciliationStatus, &entry.BankTransactionID, &entry.DocumentID,
			&entry.Metadata, &entry.CreatedBy, &entry.CreatedAt, &entry.UpdatedAt, &entry.ImmutableHash,
		)
		if err != nil {
			return nil, err
		}
		entries = append(entries, entry)
	}

	return entries, rows.Err()
}

func (r *LedgerRepository) BulkInsert(ctx context.Context, entries []models.LedgerEntry) error {
	// Use COPY for high-performance bulk insert
	copyCount, err := r.pool.CopyFrom(ctx,
		pgx.Identifier{"ledgers"},
		[]string{"id", "client_id", "account_code", "transaction_date", "transaction_type",
			"amount", "description", "gstin", "hsn_code", "gst_rate", "gst_amount",
			"reconciliation_status", "bank_transaction_id", "document_id", "metadata",
			"created_by", "created_at", "updated_at", "immutable_hash"},
		pgx.CopyFromSlice(len(entries), func(i int) ([]interface{}, error) {
			e := entries[i]
			return []interface{}{
				e.ID, e.ClientID, e.AccountCode, e.TransactionDate, e.TransactionType,
				e.Amount, e.Description, e.GSTIN, e.HSNCode, e.GSTRate, e.GSTAmount,
				e.ReconciliationStatus, e.BankTransactionID, e.DocumentID, e.Metadata,
				e.CreatedBy, e.CreatedAt, e.UpdatedAt, e.ImmutableHash,
			}, nil
		}),
	)

	if err != nil {
		return fmt.Errorf("bulk insert failed: %w", err)
	}

	if int(copyCount) != len(entries) {
		return fmt.Errorf("expected %d rows, got %d", len(entries), copyCount)
	}

	return nil
}

func (r *LedgerRepository) FindUnreconciled(ctx context.Context, clientID uuid.UUID, startDate, endDate time.Time) ([]models.LedgerEntry, error) {
	query := `
		SELECT id, client_id, account_code, transaction_date, transaction_type,
			amount, description, gstin, hsn_code, gst_rate, gst_amount,
			total_amount, reconciliation_status, bank_transaction_id, document_id,
			metadata, created_by, created_at, updated_at, immutable_hash
		FROM ledgers
		WHERE client_id = $1 
			AND transaction_date BETWEEN $2 AND $3
			AND reconciliation_status IN ('pending', 'mismatch')
		ORDER BY transaction_date
	`

	rows, err := r.pool.Query(ctx, query, clientID, startDate, endDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []models.LedgerEntry
	for rows.Next() {
		var entry models.LedgerEntry
		rows.Scan(
			&entry.ID, &entry.ClientID, &entry.AccountCode, &entry.TransactionDate, &entry.TransactionType,
			&entry.Amount, &entry.Description, &entry.GSTIN, &entry.HSNCode, &entry.GSTRate, &entry.GSTAmount,
			&entry.TotalAmount, &entry.ReconciliationStatus, &entry.BankTransactionID, &entry.DocumentID,
			&entry.Metadata, &entry.CreatedBy, &entry.CreatedAt, &entry.UpdatedAt, &entry.ImmutableHash,
		)
		entries = append(entries, entry)
	}

	return entries, rows.Err()
}

func (r *LedgerRepository) UpdateReconciliationStatus(ctx context.Context, id uuid.UUID, status models.ReconciliationStatus) error {
	query := `UPDATE ledgers SET reconciliation_status = $1, updated_at = NOW() WHERE id = $2`
	_, err := r.pool.Exec(ctx, query, status, id)
	return err
}
