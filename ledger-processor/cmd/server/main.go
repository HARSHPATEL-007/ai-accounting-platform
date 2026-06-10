package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"ledger-processor/internal/db"
	"ledger-processor/internal/handlers"
	"ledger-processor/internal/repository"
	"ledger-processor/internal/services"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	// Initialize database connection pool
	pool, err := db.NewPool(os.Getenv("DATABASE_URL"))
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer pool.Close()

	// Initialize repositories
	ledgerRepo := repository.NewLedgerRepository(pool)

	// Initialize services
	ledgerService := services.NewLedgerService(ledgerRepo)
	reconciliationService := services.NewReconciliationService(ledgerRepo)

	// Initialize handlers
	ledgerHandler := handlers.NewLedgerHandler(ledgerService, reconciliationService)

	// Setup Gin router
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(correlationIDMiddleware())
	router.Use(metricsMiddleware())

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy", "service": "ledger-processor"})
	})

	// Metrics
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// API routes
	api := router.Group("/api/v1")
	{
		api.POST("/ledgers", ledgerHandler.CreateTransaction)
		api.GET("/ledgers/:client_id", ledgerHandler.GetTransactions)
		api.POST("/ledgers/bulk", ledgerHandler.BulkInsert)
		api.POST("/reconcile", ledgerHandler.Reconcile)
		api.GET("/reconcile/status/:run_id", ledgerHandler.ReconciliationStatus)
	}

	// Graceful shutdown
	srv := &http.Server{
		Addr:    ":8080",
		Handler: router,
	}

	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	log.Println("Server exited gracefully")
}

func correlationIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		correlationID := c.GetHeader("X-Request-ID")
		if correlationID == "" {
			correlationID = uuid.New().String()
		}
		c.Set("correlation_id", correlationID)
		c.Header("X-Request-ID", correlationID)
		c.Next()
	}
}

func metricsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()
		duration := time.Since(start)
		// Record metrics (simplified - use prometheus in production)
		_ = duration
	}
}
