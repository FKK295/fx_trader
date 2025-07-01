# fx-trader-policy.hcl
# Vault policy for FX Trader application
# This policy follows the principle of least privilege

# Enable KV v2 secrets engine at secret/ path
path "secret/data/fx_trader/*" {
  capabilities = ["read"]
  # Allow reading secrets under fx_trader/ prefix
  # This is used for storing sensitive configuration like API keys
}

# Required for listing available secrets (KV v2)
path "secret/metadata/fx_trader/*" {
  capabilities = ["list"]
  # Required for the 'vault kv list' command to work
}

# Allow the app to read its own AppRole secret-id
path "auth/approle/role/fx-trader-role/secret-id" {
  capabilities = ["read", "create", "update"]
  # This allows the application to generate its own secret-ids
  # when using response-wrapping or other dynamic secret generation
}

# Allow checking token capabilities
path "sys/capabilities-self" {
  capabilities = ["read", "update"]
  # Required for the client to check its own capabilities
}

# Allow token renewal
path "auth/token/renew" {
  capabilities = ["update"]
}

# Allow token lookup (required for token renewal)
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# Optional: Add specific paths for different environments
# path "secret/data/fx_trader/development/*" {
#   capabilities = ["read"]
# }
# 
# path "secret/data/fx_trader/production/*" {
#   capabilities = ["read"]
# }
