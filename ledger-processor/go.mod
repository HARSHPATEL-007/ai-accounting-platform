module ledger-processor

go 1.22

require (
	github.com/gin-gonic/gin v1.9.1
	github.com/jackc/pgx/v5 v5.5.5
	github.com/jackc/pgxpool v0.0.0-20231213222702-5b53f6b66be6
	github.com/prometheus/client_golang v1.19.0
	github.com/sony/gobreaker v1.0.0
	github.com/hibiken/asynq v0.24.1
	go.opentelemetry.io/otel v1.24.0
	go.opentelemetry.io/otel/trace v1.24.0
	github.com/golang-migrate/migrate/v4 v4.17.0
	github.com/google/uuid v1.6.0
	github.com/shopspring/decimal v1.3.1
)
