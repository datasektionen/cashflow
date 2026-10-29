// Package config reads the server's environment. OIDC and APP_SECRET_KEY are
// read by GO-auth-yourself itself (auth.ConfigFromEnv).
package config

import (
	"bufio"
	"fmt"
	"os"
	"strings"
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
	Port        string
	DatabaseURL string
	HiveURL     string
	HiveSecret  string
}

func FromEnv() (Env, error) {
	env := Env{
		Port:        getenv("PORT", "3000"),
		DatabaseURL: os.Getenv("DATABASE_URL"),
		HiveURL:     strings.TrimSuffix(getenv("HIVE_URL", "https://hive.datasektionen.se"), "/"),
		HiveSecret:  os.Getenv("HIVE_SECRET"),
	}
	var missing []string
	if env.DatabaseURL == "" {
		missing = append(missing, "DATABASE_URL")
	}
	if env.HiveSecret == "" {
		missing = append(missing, "HIVE_SECRET")
	}
	if len(missing) > 0 {
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
