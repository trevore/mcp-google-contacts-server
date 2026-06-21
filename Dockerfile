# Build + run the contacts MCP server (HTTP transport, OAuth resource server).
# The deploy fronts it with Caddy (TLS + Anthropic-IP allowlist); the OAuth env
# (AUTH0_*) must be set or HTTP transport refuses to start.
FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY mcp_google_contacts_server ./mcp_google_contacts_server
RUN uv pip install --system -r requirements.txt && uv pip install --system .

# Unprivileged user; HOME holds the mounted token.json at ~/.config/...
RUN useradd -m -u 1000 app && mkdir -p /app/.config/google-contacts-mcp && chown -R app /app
ENV HOME=/app
USER app
EXPOSE 8000
CMD ["mcp-google-contacts", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
