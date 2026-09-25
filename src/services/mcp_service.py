"""MCP (Model Context Protocol) Service: Manages MCP server registry,
discovering dynamic tools, transport configurations, and health status.
"""

from typing import Dict, List, Optional, Any
from src.core.portal_models import MCPServerInfo


class MCPService:
    def __init__(self):
        self._servers: Dict[str, MCPServerInfo] = {}
        self._seed_default_servers()

    def _seed_default_servers(self):
        seed_servers = [
            MCPServerInfo(
                id="mcp_db",
                name="PostgreSQL Enterprise DB",
                description="Enterprise relational database queries, table introspection, and read-write operations.",
                transport="sse",
                endpoint="http://127.0.0.1:8001/mcp/sse",
                status="connected",
                tools_count=3,
                tools=[
                    {
                        "name": "execute_sql_query",
                        "description": "Execute a validated SQL SELECT or DML query on the database.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "SQL statement"},
                                "read_only": {"type": "boolean", "default": True},
                            },
                            "required": ["query"],
                        },
                        "risk_level": "medium",
                    },
                    {
                        "name": "describe_schema",
                        "description": "Introspect table structures, foreign keys, and column definitions.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string", "description": "Target table"},
                            },
                        },
                        "risk_level": "low",
                    },
                    {
                        "name": "execute_db_mutation",
                        "description": "Destructive or write operation (UPDATE/DELETE/INSERT). Requires HITL gate.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string", "description": "Mutation query"},
                                "justification": {"type": "string", "description": "Reason for write"},
                            },
                            "required": ["statement", "justification"],
                        },
                        "risk_level": "high",
                    },
                ],
            ),
            MCPServerInfo(
                id="mcp_cloud",
                name="Cloud & Kubernetes Fleet",
                description="Cloud infrastructure telemetry, cluster health, and container management.",
                transport="sse",
                endpoint="http://127.0.0.1:8002/mcp/sse",
                status="connected",
                tools_count=3,
                tools=[
                    {
                        "name": "get_cluster_metrics",
                        "description": "Fetch CPU, memory, and error rates across Kubernetes clusters.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cluster_id": {"type": "string", "default": "prod-east-1"},
                            },
                        },
                        "risk_level": "low",
                    },
                    {
                        "name": "describe_pods",
                        "description": "List pods and their current lifecycle statuses.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "namespace": {"type": "string", "default": "default"},
                            },
                        },
                        "risk_level": "low",
                    },
                    {
                        "name": "delete_cloud_resource",
                        "description": "Terminate a pod or restart cloud resource. High blast radius.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "resource_id": {"type": "string"},
                                "namespace": {"type": "string"},
                            },
                            "required": ["resource_id"],
                        },
                        "risk_level": "high",
                    },
                ],
            ),
            MCPServerInfo(
                id="mcp_knowledge",
                name="Vector Knowledge & Policies",
                description="Semantic context retrieval from indexed enterprise documents, PDF specs, and SOPs.",
                transport="stdio",
                endpoint="local://chroma-knowledge-mcp",
                status="connected",
                tools_count=2,
                tools=[
                    {
                        "name": "semantic_doc_search",
                        "description": "Retrieve relevant context passages based on semantic vector similarity.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "top_k": {"type": "integer", "default": 4},
                            },
                            "required": ["query"],
                        },
                        "risk_level": "low",
                    },
                    {
                        "name": "get_compliance_handbook",
                        "description": "Fetch official compliance policy sections for financial or operational guidelines.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string", "description": "Policy category"},
                            },
                        },
                        "risk_level": "low",
                    },
                ],
            ),
        ]

        for s in seed_servers:
            self._servers[s.id] = s

    def list_servers(self) -> List[MCPServerInfo]:
        return list(self._servers.values())

    def get_server(self, server_id: str) -> Optional[MCPServerInfo]:
        return self._servers.get(server_id)

    def register_server(
        self,
        name: str,
        description: str,
        transport: str,
        endpoint: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> MCPServerInfo:
        s_id = f"mcp_{name.lower().replace(' ', '_')}"
        tools_list = tools or []
        server = MCPServerInfo(
            id=s_id,
            name=name,
            description=description,
            transport=transport,  # type: ignore
            endpoint=endpoint,
            status="connected",
            tools_count=len(tools_list),
            tools=tools_list,
        )
        self._servers[s_id] = server
        return server

    def list_all_tools(self) -> List[Dict[str, Any]]:
        all_tools = []
        for server in self._servers.values():
            for t in server.tools:
                all_tools.append({**t, "server_id": server.id, "server_name": server.name})
        return all_tools


mcp_service = MCPService()
