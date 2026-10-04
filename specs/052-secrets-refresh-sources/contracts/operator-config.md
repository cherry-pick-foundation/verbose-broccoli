# Operator Configuration Contract

Location: `<config>/verbose-broccoli/secrets.json`, where config is absolute XDG_CONFIG_HOME or HOME/.config. JSON is an object with exactly sources and files, both non-empty objects. The old project/files-array shape is unsupported.

Each source has exactly token_file and project, plus optional server. Token paths are literal absolute paths without `..`; files must be user-owned regular files, mode 600, with exactly one non-empty BWS_ACCESS_TOKEN line. No symlink component is accepted. Server must parse as HTTPS with a hostname, no embedded user/password and no control characters; omission selects https://vault.bitwarden.com. Project is a non-empty string. No path interpolation occurs.

Each file value has source and exactly one of variables or content, with no unknown fields. Source must exist. Variables is a non-empty object whose keys match `[A-Za-z_][A-Za-z0-9_]*` and values are non-empty secret names; content is one non-empty secret name. Secret names may differ from variable names and may repeat across mappings.

A plain name matching `[A-Za-z0-9][A-Za-z0-9._-]*` resolves to `<config>/verbose-broccoli/providers/<name>` (bitwarden.env remains reserved). Other variables keys must resolve exactly to HOME/.omp/agent/.env, config/ocis-mcp/client.env or config/ocis-mcp/cloudflare-client.env. Only config/gws/client_secret.json accepts content. All other paths and `..` segments refuse. Two keys resolving to one path refuse.

Targets cannot alias any token or the operator file, lexically, canonically or by existing inode. Symlink files/parents refuse. Immediate parent must already exist, be a user-owned directory and have no group/world write bits. Existing target must be a user-owned regular file, checked with lstat. Successful replacements are new user-owned mode-600 files.

Existing variables files preserve every unmapped byte and mapped line's position/ending; duplicate mapped VARIABLE= lines refuse. Missing variables append in configured order, adding a newline separator after an unterminated existing line when needed. New files contain only mapped lines in order. Values are non-empty UTF-8 strings without CR/LF; content values are non-empty UTF-8 strings written exactly, including line breaks and final-newline choice.

The command checks all configured tokens before starting bws, lists each configured source once, validates all requested content, prepares all temporary files, then renames. Success prints target keys and a file count only. Failures print a fixed sanitized message and exit non-zero. Validation/fetch/preparation failures preserve target bytes and modes; rename failures have no rollback guarantee. JSON duplicate raw member names follow native JSON.parse behavior; duplicate resolved file keys and duplicate mapped lines are explicitly rejected.

See [quickstart](../quickstart.md) for the placeholder example. Unknown fields are rejected to catch operator typos; this is the only refinement beyond the proposed sources/files shape.
