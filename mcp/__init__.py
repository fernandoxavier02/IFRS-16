"""
MCP Servers para IFRS 16
========================

Servidores MCP (Model Context Protocol) para integração direta com:
- Stripe (pagamentos)
- Firebase (auth, firestore, storage)
- Google Cloud SQL (PostgreSQL)

Uso:
    from mcp.stripe_mcp_server import StripeMCPServer
    from mcp.firebase_mcp_server import FirebaseMCPServer
    from mcp.cloudsql_mcp_server import CloudSQLMCPServer
"""

from .stripe_mcp_server import StripeMCPServer
from .firebase_mcp_server import FirebaseMCPServer
from .cloudsql_mcp_server import CloudSQLMCPServer

__all__ = [
    "StripeMCPServer",
    "FirebaseMCPServer", 
    "CloudSQLMCPServer",
]

__version__ = "1.0.0"
