// Package config reads the server's environment. OIDC and APP_SECRET_KEY are
// read by GO-auth-yourself itself (auth.ConfigFromEnv).
package config

import (
	"bufio"
	"fmt"
	"os"
	"slices"
	"strings"

	"github.com/datasektionen/cashflow/server/internal/outbox"
	"github.com/datasektionen/cashflow/server/internal/storage"
)

// LoadDotEnv sets variables from path that are not already set. It is for local
// development; production gets its environment from Nomad.
func LoadDotEnv(path string) error {
	f, err := os.Open(path)
	if os.IsNotExist(err) {
		return nil
	} else if err != nil {
		return err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		key, value, ok := strings.Cut(line, "=")
		if !ok || strings.HasPrefix(line, "#") {
			continue
		}
		if _, set := os.LookupEnv(key); !set {
			os.Setenv(key, value)
		}
	}
	return scanner.Err()
}

type Env struct {
	Port string
	// PublicURL is where users reach Cashflow; emails link there.
	PublicURL   string
	DatabaseURL string
	HiveURL     string
	HiveSecret  string
	S3          storage.Config
	Outbox      outbox.Config
	// BudgetURL is GOrdian, which also serves development: its API is public.
	BudgetURL string
	// rfinger serves profile pictures; without a key users show initials.
	RFingerURL string
	RFingerKey string
}

func FromEnv() (Env, error) {
	env := Env{
		Port:        getenv("PORT", "3000"),
		PublicURL:   getenv("PUBLIC_URL", "http://localhost:5173"),
		DatabaseURL: os.Getenv("DATABASE_URL"),
		HiveURL:     strings.TrimSuffix(getenv("HIVE_URL", "https://hive.datasektionen.se"), "/"),
		HiveSecret:  os.Getenv("HIVE_SECRET"),
		BudgetURL:   getenv("BUDGET_URL", "https://budget.datasektionen.se"),
		RFingerURL:  strings.TrimSuffix(getenv("RFINGER_API_URL", "https://rfinger.datasektionen.se"), "/"),
		RFingerKey:  os.Getenv("RFINGER_API_KEY"),
		// The same variables as Cashflow 3, plus S3_ENDPOINT for development.
		S3: storage.Config{
			Bucket:          os.Getenv("S3_BUCKET_NAME"),
			Region:          getenv("S3_REGION", "eu-north-1"),
			AccessKeyID:     os.Getenv("S3_ACCESS_KEY_ID"),
			SecretAccessKey: os.Getenv("S3_SECRET_ACCESS_KEY"),
			Endpoint:        os.Getenv("S3_ENDPOINT"),
		},
		Outbox: outbox.Config{
			SpamURL: strings.TrimSuffix(getenv("SPAM_URL", "https://spam.datasektionen.se"), "/"),
			APIKey:  os.Getenv("SPAM_API_KEY"),
		},
	}
	var missing []string
	if env.DatabaseURL == "" {
		missing = append(missing, "DATABASE_URL")
	}
	if env.HiveSecret == "" {
		missing = append(missing, "HIVE_SECRET")
	}
	for name, value := range map[string]string{
		"S3_BUCKET_NAME":       env.S3.Bucket,
		"S3_ACCESS_KEY_ID":     env.S3.AccessKeyID,
		"S3_SECRET_ACCESS_KEY": env.S3.SecretAccessKey,
	} {
		if value == "" {
			missing = append(missing, name)
		}
	}
	if len(missing) > 0 {
		slices.Sort(missing)
		return Env{}, fmt.Errorf("missing environment variables: %s", strings.Join(missing, ", "))
	}
	return env, nil
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
