package api

import (
	"context"
	"net/http"
	"os"
	"strings"
)

type contextKey string

const apiKeyContextKey contextKey = "api_key"

// KeyInfo represents minimal API key information stored in context.
type KeyInfo struct {
	ID   int
	Name string
}

// ValidateKeyFunc is a function that validates an API key and returns key info.
type ValidateKeyFunc func(ctx context.Context, key string) (keyID int, keyName string, err error)

// KeyAuth middleware validates API keys from Authorization or X-API-Key headers.
// Set SCRAPER_NO_AUTH=true to disable authentication entirely (open access).
// Set SCRAPER_STATIC_KEY=<secret> to accept a fixed key without a DB lookup.
func KeyAuth(validateKey ValidateKeyFunc) func(http.Handler) http.Handler {
	noAuth := os.Getenv("SCRAPER_NO_AUTH") == "true"
	staticKey := os.Getenv("SCRAPER_STATIC_KEY")

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// No auth mode — allow all requests freely.
			if noAuth {
				ctx := context.WithValue(r.Context(), apiKeyContextKey, &KeyInfo{ID: 0, Name: "open"})
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}

			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				authHeader = r.Header.Get("X-API-Key")
			}

			if authHeader == "" {
				http.Error(w, `{"error": "missing api key"}`, http.StatusUnauthorized)
				return
			}

			key := strings.TrimPrefix(authHeader, "Bearer ")

			if staticKey != "" && key == staticKey {
				ctx := context.WithValue(r.Context(), apiKeyContextKey, &KeyInfo{ID: 0, Name: "static"})
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}

			keyID, keyName, err := validateKey(r.Context(), key)
			if err != nil {
				http.Error(w, `{"error": "invalid api key"}`, http.StatusUnauthorized)
				return
			}

			ctx := context.WithValue(r.Context(), apiKeyContextKey, &KeyInfo{ID: keyID, Name: keyName})
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// KeyFromContext retrieves the API key info from context.
func KeyFromContext(ctx context.Context) *KeyInfo {
	if key, ok := ctx.Value(apiKeyContextKey).(*KeyInfo); ok {
		return key
	}

	return nil
}
