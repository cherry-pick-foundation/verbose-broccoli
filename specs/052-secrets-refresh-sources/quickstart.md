# Quickstart: Multi-source Secrets Refresh

This is a public placeholder example, not a live inventory. Main fills the operator file after integration; this worker does not read or change live credentials. The old single-project configuration is unsupported and must be replaced.

## Prepare the operator file

Keep the existing pinned bws 2.1.0. Save JSON at `<config>/verbose-broccoli/secrets.json`, with config equal to absolute XDG_CONFIG_HOME or HOME/.config. Replace `<home>` and `<config>` with absolute paths, and token placeholders with private absolute file paths. The script does not expand placeholders, tilde or environment variables. Each token file must hold exactly one `BWS_ACCESS_TOKEN=<token>` line, be regular, owned by you and mode 600; symlink components refuse. Target parent directories must already exist, belong to you and not be group/world writable.

```json
{
  "sources": {
    "org-a": {
      "token_file": "<path-to-token-a>",
      "project": "<org-a-project-id>"
    },
    "org-b": {
      "token_file": "<path-to-token-b>",
      "project": "<org-b-project-id>",
      "server": "https://<org-b-server-host>"
    }
  },
  "files": {
    "hive.env": {
      "source": "org-a",
      "variables": {
        "HIVE_API_KEY": "HIVE_API_KEY"
      }
    },
    "vercel.env": {
      "source": "org-a",
      "variables": {
        "AI_GATEWAY_API_KEY": "AI_GATEWAY_API_KEY"
      }
    },
    "cloudflare.env": {
      "source": "org-a",
      "variables": {
        "CLOUDFLARE_API_TOKEN": "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ACCOUNT_ID": "CLOUDFLARE_ACCOUNT_ID"
      }
    },
    "openrouter.env": {
      "source": "org-a",
      "variables": {
        "OPENROUTER_API_KEY": "OPENROUTER_API_KEY"
      }
    },
    "github.env": {
      "source": "org-a",
      "variables": {
        "GITHUB_TOKEN": "GITHUB_TOKEN"
      }
    },
    "copilot.env": {
      "source": "org-a",
      "variables": {
        "COPILOT_API_TOKEN": "COPILOT_API_TOKEN"
      }
    },
    "<home>/.omp/agent/.env": {
      "source": "org-a",
      "variables": {
        "AGENTROUTER_API_KEY": "AGENTROUTER_API_KEY",
        "THEHIVE_API_KEY": "HIVE_API_KEY"
      }
    },
    "<config>/ocis-mcp/client.env": {
      "source": "org-b",
      "variables": {
        "OCIS_MCP_HTTP_SECRET": "OCIS_MCP_HTTP_SECRET"
      }
    },
    "<config>/ocis-mcp/cloudflare-client.env": {
      "source": "org-b",
      "variables": {
        "OCIS_MCP_HTTP_SECRET": "OCIS_MCP_HTTP_SECRET",
        "OCIS_CF_ACCESS_CLIENT_SECRET": "OCIS_CF_ACCESS_CLIENT_SECRET"
      }
    },
    "<config>/gws/client_secret.json": {
      "source": "org-a",
      "content": "GWS_CLIENT_SECRET_JSON"
    }
  }
}
```

The example uses public provider-file names traced by current repository consumers; it is not an operational inventory. Main must retain the provider entries it needs and fill the actual mapping separately. OMP's THEHIVE_API_KEY aliases the provider HIVE_API_KEY secret. Both ownCloud files share OCIS_MCP_HTTP_SECRET; the Cloudflare file also maps OCIS_CF_ACCESS_CLIENT_SECRET. Existing OCIS_CF_ACCESS_CLIENT_ID and all OMP comments/blank lines remain untouched. Remove the optional GWS entry if that whole-file secret is not configured.

## Validate and run

Run `npm run test:secrets-refresh` for offline synthetic validation. The suite checks separate sources, aliases, exact content, preserved lines, ownership/modes and unchanged targets on unsafe or failed inputs. It never uses real bws.

After integration, main can populate the operator file and run `npm run secrets:refresh` within its separate operational authorization. Success prints target names/paths and a file count only. Generic failure exits non-zero without revealing credentials. All validation and collection failures preserve targets; a filesystem failure after renames begin can leave a partial refresh. No multi-file transaction or automatic interrupted-run recovery is promised.
