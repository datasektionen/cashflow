// Package database opens the Postgres pool and applies the embedded migrations.
package database

import (
	"context"
	"embed"
	"errors"
	"fmt"
	"io/fs"
	"log/slog"
	"net/url"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/pgx/v5"
	"github.com/golang-migrate/migrate/v4/source/iofs"
	"github.com/jackc/pgx/v5/pgxpool"
)

//go:embed migrations
var migrations embed.FS

// Kept apart from django_migrations: Django owns the shared tables until the
// cutover, and this table records only Go's own migrations.
const migrationsTable = "cashflow4_schema_migrations"

// Open connects to Postgres and applies Go's own migrations.
func Open(ctx context.Context, databaseURL string) (*pgxpool.Pool, error) {
	pool, err := pgxpool.New(ctx, databaseURL)
	if err != nil {
		return nil, fmt.Errorf("connect: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping: %w", err)
	}
	if err := Migrate(databaseURL); err != nil {
		pool.Close()
		return nil, err
	}
	return pool, nil
}

// Migrate applies Go's own migrations. It runs on its own connection, so the
// migrate driver's lock and connection are released by m.Close without
// touching the app's pool.
func Migrate(databaseURL string) error {
	source, err := iofs.New(migrations, "migrations")
	if err != nil {
		return fmt.Errorf("read migrations: %w", err)
	}
	// golang-migrate picks its pgx v5 driver by URL scheme.
	dbURL, err := migrateURL(databaseURL)
	if err != nil {
		return err
	}
	m, err := migrate.NewWithSourceInstance("iofs", source, dbURL)
	if err != nil {
		return fmt.Errorf("migrate: %w", err)
	}
	defer m.Close()

	// No migration files at all is fine too: the schema is Django's until Go adds tables.
	if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) && !errors.Is(err, fs.ErrNotExist) {
		return fmt.Errorf("migrate up: %w", err)
	}
	version, dirty, _ := m.Version()
	slog.Info("database migrated", "version", version, "dirty", dirty)
	return nil
}

// migrateURL points golang-migrate's pgx v5 driver (chosen by the pgx5 scheme)
// at the database, recording versions in migrationsTable.
func migrateURL(databaseURL string) (string, error) {
	u, err := url.Parse(databaseURL)
	if err != nil {
		return "", fmt.Errorf("parse DATABASE_URL: %w", err)
	}
	u.Scheme = "pgx5"
	q := u.Query()
	q.Set("x-migrations-table", migrationsTable)
	u.RawQuery = q.Encode()
	return u.String(), nil
}
