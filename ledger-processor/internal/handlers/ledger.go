package handlers

import (
	"net/http"
	"strconv"
	"time"

	"ledger-processor/internal/models"
	"ledger-processor/internal/services"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type LedgerHandler struct {
	ledgerService         *services.LedgerService
	reconciliationService *services.ReconciliationService
}

func NewLedgerHandler(ls *services.LedgerService, rs *services.ReconciliationService) *LedgerHandler {
	return &LedgerHandler{ledgerService: ls, reconciliationService: rs}
}

func (h *LedgerHandler) CreateTransaction(c *gin.Context) {
	var req models.CreateTransactionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	entry, err := h.ledgerService.CreateTransaction(c.Request.Context(), &req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, entry)
}

func (h *LedgerHandler) GetTransactions(c *gin.Context) {
	clientID, err := uuid.Parse(c.Param("client_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid client_id"})
		return
	}

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	entries, err := h.ledgerService.GetTransactions(c.Request.Context(), clientID, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": entries, "limit": limit, "offset": offset})
}

func (h *LedgerHandler) BulkInsert(c *gin.Context) {
	var reqs []models.CreateTransactionRequest
	if err := c.ShouldBindJSON(&reqs); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	entries, err := h.ledgerService.BulkInsert(c.Request.Context(), reqs)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"count": len(entries), "data": entries})
}

func (h *LedgerHandler) Reconcile(c *gin.Context) {
	var req models.ReconciliationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	result, err := h.reconciliationService.StartReconciliation(c.Request.Context(), &req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusAccepted, result)
}

func (h *LedgerHandler) ReconciliationStatus(c *gin.Context) {
	runID := c.Param("run_id")
	status, err := h.reconciliationService.GetStatus(c.Request.Context(), runID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, status)
}
