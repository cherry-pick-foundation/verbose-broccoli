# Data Model: Multi-source Secrets Refresh

Source map keys identify sources. Each value holds token_file (absolute, non-symlink private file), project (non-empty string) and optional server (HTTPS URL). All tokens preflight; all configured sources are fetched.

File map keys are provider names or literal absolute fixed client paths. Each value holds source and exactly one of variables (non-empty ordered variable-to-secret map) or content (one secret name). Variable names match `[A-Za-z_][A-Za-z0-9_]*`. Secret names are non-empty strings. A source and secret may have many consumers.

Fetched responses are arrays of objects with string key/value fields; other bws metadata is ignored. Duplicate names refuse the run. Requested values must be non-empty; line values also exclude CR/LF. In-memory prepared targets hold their safe path and bytes; existing unrelated bytes are not parsed as configuration.

States: configuration validated -> all tokens checked -> all configured sources collected -> all contents validated -> all private temporary files prepared -> renamed -> success output. Every failure before rename leaves targets unchanged. A later filesystem failure can leave a partial refresh; no rollback is promised.
