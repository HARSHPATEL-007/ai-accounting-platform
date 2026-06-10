package models

import (
	"time"
	"github.com/google/uuid"
	"github.com/shopspring/decimal"
)

type TransactionType string

const (
	TransactionTypeDebit  TransactionType = "debit"
	TransactionTypeCredit TransactionType = "credit"
)

type ReconciliationStatus string

const (
	ReconciliationStatusPending   ReconciliationStatus = "pending"
	ReconciliationStatusMatched   ReconciliationStatus = "matched"
	ReconciliationStatusMismatch  ReconciliationStatus = "mismatch"
	ReconciliationStatusFlagged   ReconciliationStatus = "flagged"
	ReconciliationStatusApproved  ReconciliationStatus = "approved"
)

type LedgerEntry struct {
	ID                    uuid.UUID            `json:"id" db:"id"`
	ClientID              uuid.UUID            `json:"client_id" db:"client_id"`
	AccountCode           string               `json:"account_code" db:"account_code"`
	TransactionDate       time.Time            `json:"transaction_date" db:"transaction_date"`
	TransactionType       TransactionType      `json:"transaction_type" db:"transaction_type"`
	Amount                decimal.Decimal      `json:"amount" db:"amount"`
	Description           string               `json:"description" db:"description"`
	GSTIN                 *string              `json:"gstin,omitempty" db:"gstin"`
	HSNCode               *string              `json:"hsn_code,omitempty" db:"hsn_code"`
	GSTRate               *decimal.Decimal     `json:"gst_rate,omitempty" db:"gst_rate"`
	GSTAmount             *decimal.Decimal     `json:"gst_amount,omitempty" db:"gst_amount"`
	TotalAmount           decimal.Decimal      `json:"total_amount" db:"total_amount"`
	ReconciliationStatus  ReconciliationStatus `json:"reconciliation_status" db:"reconciliation_status"`
	BankTransactionID     *string              `json:"bank_transaction_id,omitempty" db:"bank_transaction_id"`
	DocumentID            *uuid.UUID           `json:"document_id,omitempty" db:"document_id"`
	Metadata              map[string]interface{} `json:"metadata" db:"metadata"`
	CreatedBy             uuid.UUID            `json:"created_by" db:"created_by"`
	CreatedAt             time.Time            `json:"created_at" db:"created_at"`
	UpdatedAt             time.Time            `json:"updated_at" db:"updated_at"`
	ImmutableHash         string               `json:"immutable_hash" db:"immutable_hash"`
}

type CreateTransactionRequest struct {
	ClientID          uuid.UUID       `json:"client_id" binding:"required"`
	AccountCode       string          `json:"account_code" binding:"required,max=50"`
	TransactionDate   time.Time       `json:"transaction_date" binding:"required"`
	TransactionType   TransactionType `json:"transaction_type" binding:"required,oneof=debit credit"`
	Amount            decimal.Decimal `json:"amount" binding:"required,gt=0"`
	Description       string          `json:"description" binding:"required,max=1000"`
	GSTIN             *string         `json:"gstin,omitempty" binding:"omitempty,len=15"`
	HSNCode           *string         `json:"hsn_code,omitempty" binding:"omitempty,min=4,max=8"`
	GSTRate           *decimal.Decimal `json:"gst_rate,omitempty"`
	GSTAmount         *decimal.Decimal `json:"gst_amount,omitempty"`
	BankTransactionID *string         `json:"bank_transaction_id,omitempty"`
	DocumentID        *uuid.UUID      `json:"document_id,omitempty"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
	CreatedBy         uuid.UUID       `json:"created_by" binding:"required"`
}

type ReconciliationRequest struct {
	ClientID          uuid.UUID `json:"client_id" binding:"required"`
	StartDate         time.Time `json:"start_date" binding:"required"`
	EndDate           time.Time `json:"end_date" binding:"required"`
	BankStatementID   *uuid.UUID `json:"bank_statement_id,omitempty"`
	AutoApproveMatch  bool      `json:"auto_approve_match"`
}

type ReconciliationResult struct {
	RunID             string    `json:"run_id"`
	ClientID          uuid.UUID `json:"client_id"`
	TotalProcessed    int       `json:"total_processed"`
	Matched         int       `json:"matched"`
	Mismatched      int       `json:"mismatched"`
	Flagged         int       `json:"flagged"`
	Status          string    `json:"status"`
	CompletedAt     *time.Time `json:"completed_at,omitempty"`
}
