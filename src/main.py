import os
from typing import Optional

import typer
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

app = typer.Typer()


class AppConfig(BaseModel):
    """Configuration model using Pydantic"""

    api_key: Optional[str] = None


@app.command(name="hello")
def hello(name: str = typer.Option("World", help="Name to greet")):
    """
    Simple hello world command to verify the setup works.
    """
    # Example of loading from .env
    api_key = os.getenv("GEMINI_API_KEY")

    config = AppConfig(api_key=api_key)

    typer.echo(f"Hello {name}!")
    typer.echo("Setup verified! ✓")

    if config.api_key:
        typer.echo(f"Gemini API Key loaded: {config.api_key[:8]}...")
    else:
        typer.echo("No Gemini API key found in .env file")


def main():
    app()


if __name__ == "__main__":
    app()
