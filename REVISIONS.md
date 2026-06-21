# REVISIONS.md - MCP Google Contacts Server

This document details the modifications applied to the `rayanzaki/mcp-google-contacts-server` repository to enable successful installation and operation as a Python package.

## Fork hardening — trevore (2026-06-20)

Security hardening before exposing this server as a remote Claude connector
(2026-06-20 audit). Earlier commits removed stdout credential/PII leaks and set
`token.json` 0600 (`7b9fa40`). This change adds **caller authentication**:

- **OAuth 2.1 resource server.** The HTTP MCP endpoint now requires a valid Auth0
  JWT access token (signature via JWKS, `iss`, `aud`, `exp`) using fastmcp's
  `RemoteAuthProvider` + `JWTVerifier` (`mcp_google_contacts_server/auth.py`).
  Unauthenticated requests get 401 + `WWW-Authenticate`; the server serves RFC 9728
  protected-resource metadata so Claude can discover the AS. HTTP transport
  **refuses to start** without the OAuth env vars (fail closed). Single-user is
  enforced upstream at Auth0; the resource server binds the audience.
- **Migrated to `fastmcp` (v3)** — already declared in the manifest, but the code
  imported the older bundled `mcp.server.fastmcp`. Pinned `fastmcp>=3.4,<4`, fixed
  `requirements.txt` (was the inconsistent `mcp[cli]` + a duplicate `google-auth`),
  and removed the stale `uv.lock` (it pinned `mcp 1.5.0`, no fastmcp) — regenerate
  with `uv lock`.

New env vars: `AUTH0_ISSUER`, `AUTH0_JWKS_URI`, `AUTH0_AUDIENCE`, `MCP_BASE_URL`.
Tests: `pytest tests/test_auth.py`. Unchanged: the 9 tools, Google scopes
(`contacts` + `directory.readonly`), and the server→Google data path.

## Version 0.1.1 (Proposed)

### Fixes:

1.  **Installation Failure (`pip install .`)**: The original `pyproject.toml` expected the package directory to be `mcp_google_contacts_server`, but the source code was located in `src/`. This caused the `pip install .` command to fail with an `error: package directory 'mcp_google_contacts_server' does not exist`.
    *   **Solution**: Renamed the `src/` directory to `mcp_google_contacts_server/`.

2.  **Module Not Found Errors (`ModuleNotFoundError`)**: After initial installation (post-directory rename), running the `mcp-google-contacts` entry point resulted in `ModuleNotFoundError` for internal modules (e.g., `tools`, `config`, `google_contacts_service`, `formatters`). This was due to relative imports being used where absolute imports (relative to the installed package) were required.
    *   **Solution**: Updated all relative import statements in `main.py`, `tools.py`, and `google_contacts_service.py` to use absolute imports (e.g., `from mcp_google_contacts_server.tools import ...`).

### Updated Files:

*   `mcp_google_contacts_server/main.py`
*   `mcp_google_contacts_server/tools.py`
*   `mcp_google_contacts_server/google_contacts_service.py`
*   `pyproject.toml` (version bump)
*   `README.md` (installation instructions updated)

### Installation Steps (Corrected):

To install this package from source after cloning the repository:

1.  **Rename the source directory:**
    ```bash
    mv src mcp_google_contacts_server
    ```
2.  **Install the package:**
    ```bash
    pip install .
    ```

These changes ensure that the package can be installed correctly and its entry point script functions as expected.
