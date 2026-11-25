import typer
from arena.orchestrator import ArenaOrchestrator

app = typer.Typer(help="Sandboxed Adversarial Multi-Agent Arena CLI")


@app.callback()
def main() -> None:
    """Sandboxed Adversarial Multi-Agent Arena CLI."""


@app.command()
def run(
    scenario: str = typer.Option("prompt_injection", help="Scenario name"),
    rounds: int = typer.Option(5, min=1, max=100, help="Number of rounds"),
    seed: int = typer.Option(42, help="Random seed"),
) -> None:
    report = ArenaOrchestrator().run_arena(scenario=scenario, rounds=rounds, seed=seed)
    typer.echo(f"Run ID:              {report.run_id}")
    typer.echo(f"Scenario:            {report.scenario}")
    typer.echo(f"Rounds Completed:    {report.total_rounds}")
    typer.echo(f"Attack Success Rate: {report.attack_success_rate:.1%}")
    typer.echo(f"Detection Rate:      {report.detection_rate:.1%}")
    typer.echo(f"Total Tokens:        {report.total_tokens}")
    typer.echo(f"Est. Token Cost:     ${report.estimated_token_cost_usd:.6f}")


if __name__ == "__main__":
    app()