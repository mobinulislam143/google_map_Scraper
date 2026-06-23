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
// If the SCRAPER_STATIC_KEY environment variable is set, requests that supply
// that value as their key are accepted without a database lookup — no admin-panel
// API key required.
func KeyAuth(validateKey ValidateKeyFunc) func(http.Handler) http.Handler {
	staticKey := os.Getenv("SCRAPER_STATIC_KEY")

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				authHeader = r.Header.Get("X-API-Key")
			}

			if authHeader == "" {
				http.Error(w, `{"error": "missing api key"}`, http.StatusUnauthorized)
				return
			}

			key := strings.TrimPrefix(authHeader, "Bearer ")

			// Accept the static env-var key without hitting the database.
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
