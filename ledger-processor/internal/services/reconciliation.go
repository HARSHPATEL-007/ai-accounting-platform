package services

import (
	"context"
	"fmt"
	"sync"
	"time"

	"ledger-processor/internal/models"
	"ledger-processor/internal/repository"

	"github.com/google/uuid"
)

type ReconciliationService struct {
	repo      *repository.LedgerRepository
	jobs      map[string]*models.ReconciliationResult
	jobsMutex sync.RWMutex
}

func NewReconciliationService(repo *repository.LedgerRepository) *ReconciliationService {
	return &ReconciliationService{
		repo: repo,
		jobs: make(map[string]*models.ReconciliationResult),
	}
}

func (s *ReconciliationService) StartReconciliation(ctx context.Context, req *models.ReconciliationRequest) (*models.ReconciliationResult, error) {
	runID := uuid.New().String()

	result := &models.ReconciliationResult{
		RunID:         runID,
		ClientID:      req.ClientID,
		TotalProcessed: 0,
		Matched:       0,
		Mismatched:    0,
		Flagged:       0,
		Status:        "running",
	}

	s.jobsMutex.Lock()
	s.jobs[runID] = result
	s.jobsMutex.Unlock()

	// Run reconciliation asynchronously
	go s.runReconciliation(runID, req)

	return result, nil
}

func (s *ReconciliationService) runReconciliation(runID string, req *models.ReconciliationRequest) {
	ctx := context.Background()

	entries, err := s.repo.FindUnreconciled(ctx, req.ClientID, req.StartDate, req.EndDate)
	if err != nil {
		s.updateJob(runID, func(r *models.ReconciliationResult) {
			r.Status = "failed"
		})
		return
	}

	matched := 0
	mismatched := 0
	flagged := 0

	for _, entry := range entries {
		// Deterministic matching logic
		// In production: match against bank statements from Account Aggregator API
		if entry.BankTransactionID != nil && *entry.BankTransactionID != "" {
			// Simulate bank match check
			matched++
			if req.AutoApproveMatch {
				s.repo.UpdateReconciliationStatus(ctx, entry.ID, models.ReconciliationStatusMatched)
			}
		} else if entry.GSTIN != nil && entry.GSTAmount != nil {
			// Check GSTIN validity and amount consistency
			if entry.GSTAmount.GreaterThan(entry.Amount) {
				flagged++
				s.repo.UpdateReconciliationStatus(ctx, entry.ID, models.ReconciliationStatusFlagged)
			} else {
				mismatched++
				s.repo.UpdateReconciliationStatus(ctx, entry.ID, models.ReconciliationStatusMismatch)
			}
		} else {
			mismatched++
			s.repo.UpdateReconciliationStatus(ctx, entry.ID, models.ReconciliationStatusMismatch)
		}
	}

	now := time.Now().UTC()
	s.updateJob(runID, func(r *models.ReconciliationResult) {
		r.TotalProcessed = len(entries)
		r.Matched = matched
		r.Mismatched = mismatched
		r.Flagged = flagged
		r.Status = "completed"
		r.CompletedAt = &now
	})
}

func (s *ReconciliationService) updateJob(runID string, updater func(*models.ReconciliationResult)) {
	s.jobsMutex.Lock()
	defer s.jobsMutex.Unlock()
	if job, ok := s.jobs[runID]; ok {
		updater(job)
	}
}

func (s *ReconciliationService) GetStatus(ctx context.Context, runID string) (*models.ReconciliationResult, error) {
	s.jobsMutex.RLock()
	defer s.jobsMutex.RUnlock()

	if job, ok := s.jobs[runID]; ok {
		return job, nil
	}

	return nil, fmt.Errorf("reconciliation job not found: %s", runID)
}
