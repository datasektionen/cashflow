// Package outbox sends the emails queued in cashflow4_outbox through spam,
// Datasektionen's mail service, retrying with backoff when it is down.
package outbox

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/database/db"
)

const (
	maxAttempts  = 8
	pollInterval = 5 * time.Second
	from         = "cashflow-no-reply@datasektionen.se"
)

type Config struct {
	SpamURL string
	// APIKey empty means development: emails are logged, not sent.
	APIKey string
}

type Worker struct {
	pool *pgxpool.Pool
	cfg  Config
	http *http.Client
}

func NewWorker(pool *pgxpool.Pool, cfg Config) *Worker {
	return &Worker{pool: pool, cfg: cfg, http: &http.Client{Timeout: 15 * time.Second}}
}

// Run sends due emails until ctx is cancelled.
func (w *Worker) Run(ctx context.Context) {
	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()
	for {
		if err := w.sendDue(ctx); err != nil && ctx.Err() == nil {
			slog.Error("outbox", "error", err)
		}
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
		}
	}
}

// sendDue sends one batch. Rows stay locked until the batch's transaction
// ends, so several servers can run workers side by side.
func (w *Worker) sendDue(ctx context.Context) error {
	return pgx.BeginFunc(ctx, w.pool, func(tx pgx.Tx) error {
		q := db.New(tx)
		due, err := q.ClaimDueEmails(ctx, maxAttempts)
		if err != nil {
			return err
		}
		for _, job := range due {
			var mail claims.Email
			if err := json.Unmarshal(job.Payload, &mail); err != nil {
				return fmt.Errorf("outbox %d: %w", job.ID, err)
			}
			if err := w.send(ctx, mail); err != nil {
				// 1, 2, 4 … minutes between attempts.
				retry := time.Now().Add(time.Duration(1<<job.Attempts) * time.Minute)
				slog.Warn("email failed", "id", job.ID, "attempt", job.Attempts+1, "error", err)
				if err := q.MarkEmailFailed(ctx, db.MarkEmailFailedParams{ID: job.ID, LastError: err.Error(), RetryAt: pgTime(retry)}); err != nil {
					return err
				}
				continue
			}
			if err := q.MarkEmailSent(ctx, job.ID); err != nil {
				return err
			}
		}
		return nil
	})
}

func (w *Worker) send(ctx context.Context, mail claims.Email) error {
	if w.cfg.APIKey == "" {
		slog.Info("email (not sent: SPAM_API_KEY is unset)", "to", mail.To, "subject", mail.Subject, "content", mail.Content)
		return nil
	}
	body, err := json.Marshal(map[string]string{
		"from": from, "to": mail.To, "subject": mail.Subject, "content": mail.Content, "key": w.cfg.APIKey,
	})
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, w.cfg.SpamURL+"/api/legacy/sendmail", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	res, err := w.http.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode >= 300 {
		return fmt.Errorf("spam: %s", res.Status)
	}
	return nil
}

func pgTime(t time.Time) pgtype.Timestamptz { return pgtype.Timestamptz{Time: t, Valid: true} }
