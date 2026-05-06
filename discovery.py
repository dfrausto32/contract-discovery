#!/usr/bin/env python3
"""
discovery.py — Generate targeted LinkedIn search URLs from config.yaml
and open them in the browser for manual review.

No scraping. No automation. 100% LinkedIn TOS compliant.
You do the clicking; this tool does the URL construction.
"""

import webbrowser
import urllib.parse
import yaml
import click
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        click.echo(f"Error: config.yaml not found at {CONFIG_PATH}", err=True)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def build_people_search_url(base: str, keywords: str, location: str) -> str:
    params = {
        "keywords": keywords,
        "origin": "GLOBAL_SEARCH_HEADER",
        "sid": "construction-discovery",
    }
    # LinkedIn people search supports geoUrn but the keyword approach works
    # for manual browsing without requiring API access.
    if location:
        params["keywords"] = f"{keywords} {location}"
    return base + "?" + urllib.parse.urlencode(params)


def build_company_search_url(base: str, keywords: str, location: str) -> str:
    params = {
        "keywords": f"{keywords} {location}".strip(),
        "origin": "GLOBAL_SEARCH_HEADER",
    }
    return base + "?" + urllib.parse.urlencode(params)


def generate_people_urls(config: dict) -> list[dict]:
    """Generate LinkedIn people search URLs for each title + geography combo."""
    urls = []
    base = config["search"]["linkedin_people_search"]
    primary_location = config["geography"]["primary"]
    all_locations = [primary_location] + config["geography"].get("additional", [])
    max_urls = config["search"]["max_urls_per_session"]

    # Build title list ordered by priority tier
    title_groups = [
        ("Owner/Founder", config["titles"]["owner_tier"]),
        ("Operator", config["titles"]["operator_tier"]),
    ]

    for tier_name, titles in title_groups:
        for title in titles:
            for subtype in config["construction_subtypes"]:
                if len(urls) >= max_urls:
                    break
                keyword = f'{title} "{subtype["name"]}"'
                url = build_people_search_url(base, keyword, primary_location)
                urls.append({
                    "label": f"{tier_name}: {title} @ {subtype['name']} — {primary_location}",
                    "url": url,
                    "tier": tier_name,
                })
            if len(urls) >= max_urls:
                break
        if len(urls) >= max_urls:
            break

    return urls[:max_urls]


def generate_company_urls(config: dict) -> list[dict]:
    """Generate LinkedIn company search URLs for each construction subtype."""
    urls = []
    base = config["search"]["linkedin_company_search"]
    primary_location = config["geography"]["primary"]

    for subtype in config["construction_subtypes"]:
        keyword = subtype["name"]
        url = build_company_search_url(base, keyword, primary_location)
        urls.append({
            "label": f'Companies: {subtype["name"]} — {primary_location}',
            "url": url,
            "tier": "company",
        })

    return urls


@click.group()
def cli():
    """LinkedIn discovery URL generator for construction industry outreach."""
    pass


@cli.command("people")
@click.option("--open", "open_browser", is_flag=True, default=False,
              help="Open each URL in the browser automatically.")
@click.option("--limit", default=None, type=int,
              help="Override max URLs from config.")
def people_search(open_browser: bool, limit: int):
    """Generate people search URLs (owners, operators) and print or open them."""
    config = load_config()
    if limit:
        config["search"]["max_urls_per_session"] = limit

    urls = generate_people_urls(config)

    click.echo(f"\n{'='*60}")
    click.echo(f"  PEOPLE SEARCH URLS ({len(urls)} generated)")
    click.echo(f"  Target: {config['geography']['primary']}")
    click.echo(f"{'='*60}\n")

    for i, entry in enumerate(urls, 1):
        click.echo(f"[{i}] {entry['label']}")
        click.echo(f"    {entry['url']}\n")
        if open_browser:
            webbrowser.open(entry["url"])
            click.echo("    -> Opened in browser")

    if not open_browser:
        click.echo("Tip: Run with --open to launch all URLs in your browser.")
    click.echo(f"\nAfter reviewing, log contacts with: python tracker.py add\n")


@cli.command("companies")
@click.option("--open", "open_browser", is_flag=True, default=False,
              help="Open each URL in the browser automatically.")
def company_search(open_browser: bool):
    """Generate company search URLs by construction subtype."""
    config = load_config()
    urls = generate_company_urls(config)

    click.echo(f"\n{'='*60}")
    click.echo(f"  COMPANY SEARCH URLS ({len(urls)} generated)")
    click.echo(f"  Target: {config['geography']['primary']}")
    click.echo(f"{'='*60}\n")

    for i, entry in enumerate(urls, 1):
        click.echo(f"[{i}] {entry['label']}")
        click.echo(f"    {entry['url']}\n")
        if open_browser:
            webbrowser.open(entry["url"])
            click.echo("    -> Opened in browser")

    if not open_browser:
        click.echo("Tip: Run with --open to launch all URLs in your browser.")
    click.echo(f"\nAfter reviewing, log contacts with: python tracker.py add\n")


@cli.command("all")
@click.option("--open", "open_browser", is_flag=True, default=False,
              help="Open every URL in the browser.")
def all_searches(open_browser: bool):
    """Generate both people and company search URLs."""
    config = load_config()
    people = generate_people_urls(config)
    companies = generate_company_urls(config)
    all_urls = people + companies

    click.echo(f"\n{'='*60}")
    click.echo(f"  ALL SEARCH URLS ({len(all_urls)} total)")
    click.echo(f"{'='*60}\n")

    for i, entry in enumerate(all_urls, 1):
        click.echo(f"[{i}] {entry['label']}")
        click.echo(f"    {entry['url']}\n")
        if open_browser:
            webbrowser.open(entry["url"])

    click.echo(f"\nLog contacts with: python tracker.py add\n")


if __name__ == "__main__":
    cli()
