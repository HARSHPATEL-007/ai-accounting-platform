package services

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"

	"ledger-processor/internal/models"
	"ledger-processor/internal/repository"

	"github.com/google/uuid"
	"github.com/shopspring/decimal"
)

type LedgerService struct {
	repo *repository.LedgerRepository
}

func NewLedgerService(repo *repository.LedgerRepository) *LedgerService {
	return &LedgerService{repo: repo}
}

func (s *LedgerService) CreateTransaction(ctx context.Context, req *models.CreateTransactionRequest) (*models.LedgerEntry, error) {
	now := time.Now().UTC()

	entry := &models.LedgerEntry{
		ID:                   uuid.New(),
		ClientID:             req.ClientID,
		AccountCode:          req.AccountCode,
		TransactionDate:      req.TransactionDate,
		TransactionType:      req.TransactionType,
		Amount:               req.Amount,
		Description:          req.Description,
		GSTIN:                req.GSTIN,
		HSNCode:              req.HSNCode,
		GSTRate:              req.GSTRate,
		GSTAmount:            req.GSTAmount,
		ReconciliationStatus: models.ReconciliationStatusPending,
		BankTransactionID:    req.BankTransactionID,
		DocumentID:           req.DocumentID,
		Metadata:             req.Metadata,
		CreatedBy:            req.CreatedBy,
		CreatedAt:            now,
		UpdatedAt:            now,
	}

	// Calculate total amount
	if entry.GSTAmount != nil {
		entry.TotalAmount = entry.Amount.Add(*entry.GSTAmount)
	} else {
		entry.TotalAmount = entry.Amount
	}

	// Generate immutable hash
	entry.ImmutableHash = s.generateHash(entry)

	if err := s.repo.Create(ctx, entry); err != nil {
		return nil, fmt.Errorf("failed to create transaction: %w", err)
	}

	return entry, nil
}

func (s *LedgerService) GetTransactions(ctx context.Context, clientID uuid.UUID, limit, offset int) ([]models.LedgerEntry, error) {
	if limit > 1000 {
		limit = 1000
	}
	return s.repo.GetByClientID(ctx, clientID, limit, offset)
}

func (s *LedgerService) BulkInsert(ctx context.Context, reqs []models.CreateTransactionRequest) ([]models.LedgerEntry, error) {
	now := time.Now().UTC()
	entries := make([]models.LedgerEntry, len(reqs))

	for i, req := range reqs {
		entry := models.LedgerEntry{
			ID:                   uuid.New(),
			ClientID:             req.ClientID,
			AccountCode:          req.AccountCode,
			TransactionDate:      req.TransactionDate,
			TransactionType:      req.TransactionType,
			Amount:               req.Amount,
			Description:          req.Description,
			GSTIN:                req.GSTIN,
			HSNCode:              req.HSNCode,
			GSTRate:              req.GSTRate,
			GSTAmount:            req.GSTAmount,
			ReconciliationStatus: models.ReconciliationStatusPending,
			BankTransactionID:    req.BankTransactionID,
			DocumentID:           req.DocumentID,
			Metadata:             req.Metadata,
			CreatedBy:            req.CreatedBy,
			CreatedAt:            now,
			UpdatedAt:            now,
		}

		if entry.GSTAmount != nil {
			entry.TotalAmount = entry.Amount.Add(*entry.GSTAmount)
		} else {
			entry.TotalAmount = entry.Amount
		}

		entry.ImmutableHash = s.generateHash(&entry)
		entries[i] = entry
	}

	if err := s.repo.BulkInsert(ctx, entries); err != nil {
		return nil, err
	}

	return entries, nil
}

func (s *LedgerService) generateHash(entry *models.LedgerEntry) string {
	data := fmt.Sprintf("%s|%s|%s|%s|%s|%s|%s|%s|%s",
		entry.ID.String(),
		entry.ClientID.String(),
		entry.AccountCode,
		entry.TransactionDate.Format(time.RFC3339),
		entry.Amount.String(),
		entry.Description,
		func() string { if entry.GSTIN != nil { return *entry.GSTIN }; return "" }(),
		entry.CreatedAt.Format(time.RFC3339),
		entry.CreatedBy.String(),
	)

	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}
