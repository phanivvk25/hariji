"""Main entrypoint for AI Agent Platform: supports interactive CLI or FastAPI server."""

import sys
import asyncio
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.models_catalog import model_catalog
from src.core.providers.factory import ProviderFactory
from src.agents.supervisor import SupervisorAgent
from src.rag.store import VectorStore
from src.rag.loader import DocumentLoader
from src.rag.chunker import RecursiveCharacterChunker
from src.config import settings

console = Console()


async def run_cli():
    console.print(Panel.fit(
        "[bold cyan]AI Agent Platform[/bold cyan]\n"
        "[dim]Accommodating General LLM Agents & Agentic RAG Agents[/dim]\n"
        f"[green]Active Provider:[/green] {settings.DEFAULT_LLM_PROVIDER} | [green]Model:[/green] {settings.GEMINI_MODEL}",
        border_style="cyan"
    ))

    # Index seed documents
    loader = DocumentLoader()
    raw_docs = loader.load_directory(settings.DOCS_RAW_DIR)
    chunker = RecursiveCharacterChunker()
    chunks = chunker.chunk_documents(raw_docs)
    vector_store = VectorStore()
    await vector_store.add_documents(chunks)

    agent = SupervisorAgent()
    console.print(f"[dim]Knowledge base ready with {len(chunks)} chunks from {len(raw_docs)} documents.[/dim]\n")
    console.print("[yellow]Type your question or task below (type 'exit' to quit):[/yellow]\n")

    while True:
        try:
            user_input = input("\nUser > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[dim]Goodbye![/dim]")
                break

            console.print("\n[bold blue]Agent Thinking & Execution:[/bold blue]")
            async for step in agent.run(user_input, mode="auto"):
                if step.step_type == "thought":
                    console.print(f"  [dim cyan]• Thought:[/dim cyan] {step.content}")
                elif step.step_type == "action":
                    console.print(f"  [yellow]⚡ Action:[/yellow] {step.content}")
                elif step.step_type == "observation":
                    console.print(f"  [magenta]👁 Observation:[/magenta] {step.content}")
                elif step.step_type == "citation":
                    console.print(f"  [green]📖 Citation:[/green] [{step.metadata.get('source')} | Score: {step.metadata.get('score')}] {step.content[:100]}...")
                elif step.step_type == "final_answer":
                    console.print(Panel(step.content, title="[bold green]Final Response[/bold green]", border_style="green"))

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    parser = argparse.ArgumentParser(description="Multi-Provider AI Agent Platform")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI web server")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI server (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for FastAPI server")
    args = parser.parse_args()

    if args.server:
        import uvicorn
        uvicorn.run("src.api.app:app", host=args.host, port=args.port, reload=True)
    else:
        asyncio.run(run_cli())


if __name__ == "__main__":
    main()
