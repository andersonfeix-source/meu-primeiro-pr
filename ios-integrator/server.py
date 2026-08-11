"""Servidor MCP que permite ao Claude executar Atalhos (Shortcuts) no iPhone do usuário via Pushcut."""
import os

import httpx
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("ios-shortcuts")

PUSHCUT_SECRET = os.environ.get("PUSHCUT_SECRET")


@mcp.tool()
async def run_shortcut(shortcut: str, input: str | None = None, timeout: int = 10) -> str:
    """Executa um Atalho do app Atalhos no iPhone do usuário, via Pushcut.

    Args:
        shortcut: nome exato do Atalho, como cadastrado no app Atalhos.
        input: texto opcional a passar como entrada do Atalho.
        timeout: segundos para aguardar o iPhone responder (padrão 10).
    """
    if not PUSHCUT_SECRET:
        raise RuntimeError(
            "PUSHCUT_SECRET não configurada. Veja o README para gerar o webhook secret no app Pushcut."
        )

    params = {"shortcut": shortcut, "timeout": timeout}
    if input is not None:
        params["input"] = input

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.pushcut.io/{PUSHCUT_SECRET}/execute",
            params=params,
        )
        response.raise_for_status()

    return f"Atalho '{shortcut}' executado no iPhone."


if __name__ == "__main__":
    mcp.run()
