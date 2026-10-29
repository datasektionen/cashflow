// Package database opens the Postgres pool and applies the embedded migrations.
package database

import (
	"context"
	"embed"
	"errors"
	"fmt"
	"log/slog"
	"strings"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/pgx/v5"
	"github.com/golang-migrate/migrate/v4/source/iofs"
	"github.com/jackc/pgx/v5/pgxpool"
)

//go:embed migrations/*.sql
var migrations embed.FS

// Open connects to Postgres and migrates the schema to the latest version.
func Open(ctx context.Context, url string) (*pgxpool.Pool, error) {
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return nil, fmt.Errorf("connect: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping: %w", err)
	}
	if err := migrateUp(url); err != nil {
		pool.Close()
		return nil, err
	}
	return pool, nil
}

// migrateUp runs on its own connection, so the migrate driver's lock and
// connection are released by m.Close without touching the app's pool.
func migrateUp(url string) error {
	source, err := iofs.New(migrations, "migrations")
	if err != nil {
		return fmt.Errorf("read migrations: %w", err)
	}
	// golang-migrate picks its pgx v5 driver by URL scheme.
	dbURL := "pgx5://" + strings.TrimPrefix(strings.TrimPrefix(url, "postgres://"), "postgresql://")
	m, err := migrate.NewWithSourceInstance("iofs", source, dbURL)
	if err != nil {
		return fmt.Errorf("migrate: %w", err)
	}
	defer m.Close()

	if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
		return fmt.Errorf("migrate up: %w", err)
	}
	version, dirty, _ := m.Version()
	slog.Info("database migrated", "version", version, "dirty", dirty)
	return nil
}
