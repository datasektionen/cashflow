package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/datasektionen/cashflow/server/internal/config"
	"github.com/datasektionen/cashflow/server/internal/database"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/outbox"
	"github.com/datasektionen/cashflow/server/internal/storage"
	"github.com/datasektionen/cashflow/server/internal/web"
)

func main() {
	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})))

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	if err := run(ctx); err != nil {
		slog.Error("server stopped", "error", err)
		os.Exit(1)
	}
}

func run(ctx context.Context) error {
	if err := config.LoadDotEnv(".env"); err != nil {
		return err
	}
	env, err := config.FromEnv()
	if err != nil {
		return err
	}

	pool, err := database.Open(ctx, env.DatabaseURL)
	if err != nil {
		return err
	}
	defer pool.Close()

	files, err := storage.New(ctx, env.S3)
	if err != nil {
		return err
	}

	// Sends emails queued by workflow changes; stops with the server.
	go outbox.NewWorker(pool, env.Outbox).Run(ctx)

	handler, err := web.NewHandler(ctx, web.Deps{
		Pool:      pool,
		PublicURL: env.PublicURL,
		Hive:      hive.NewClient(env.HiveURL, env.HiveSecret),
		Files:     files,
	})
	if err != nil {
		return err
	}

	server := &http.Server{
		Addr:              "0.0.0.0:" + env.Port,
		Handler:           handler,
		ReadHeaderTimeout: 10 * time.Second,
		// Uploads of scanned receipts can be slow on mobile networks.
		ReadTimeout:  2 * time.Minute,
		WriteTimeout: 2 * time.Minute,
		IdleTimeout:  time.Minute,
	}

	errs := make(chan error, 1)
	go func() {
		slog.Info("listening", "address", server.Addr)
		errs <- server.ListenAndServe()
	}()

	select {
	case err := <-errs:
		if !errors.Is(err, http.ErrServerClosed) {
			return err
		}
	case <-ctx.Done():
		slog.Info("shutting down")
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return server.Shutdown(shutdownCtx)
}
