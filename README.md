<p align="center">
  <img src="https://img.shields.io/badge/mwdb--cli-MWDB%20Core%20API%20client-blue?style=for-the-badge" alt="mwdb-cli">
</p>

<h1 align="center">mwdb-cli</h1>

<p align="center">
  <strong>CLI and Python client covering the full MWDB Core API (all 122 operations)</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/mwdb-cli/"><img src="https://img.shields.io/pypi/v/mwdb-cli?style=flat-square&logo=pypi&logoColor=white" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/mwdb-cli/"><img src="https://img.shields.io/pypi/pyversions/mwdb-cli?style=flat-square&logo=python&logoColor=white" alt="Python Versions"></a>
  <a href="https://github.com/seifreed/mwdb-cli/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://docs.oasis-open.org/sarif/sarif/v2.1.0/"><img src="https://img.shields.io/badge/SARIF-2.1.0%20output-brightgreen?style=flat-square" alt="SARIF"></a>
  <a href="https://github.com/toon-format/toon"><img src="https://img.shields.io/badge/TOON-output-orange?style=flat-square" alt="TOON"></a>
</p>

<p align="center">
  <a href="https://github.com/seifreed/mwdb-cli/stargazers"><img src="https://img.shields.io/github/stars/seifreed/mwdb-cli?style=flat-square" alt="GitHub Stars"></a>
  <a href="https://github.com/seifreed/mwdb-cli/issues"><img src="https://img.shields.io/github/issues/seifreed/mwdb-cli?style=flat-square" alt="GitHub Issues"></a>
  <a href="https://buymeacoffee.com/seifreed"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?style=flat-square&logo=buy-me-a-coffee&logoColor=white" alt="Buy Me a Coffee"></a>
</p>

---

## Overview

**mwdb-cli** is a Python toolkit to work with [MWDB Core](https://mwdb.cert.pl)
(CERT.pl's malware database) from the command line or as a library. It covers
**every operation** of the MWDB Core API — all **122 operations** of spec
**2.18.0** — with an async-native core, a synchronous facade, and
machine-readable outputs including JSON, TOON and SARIF 2.1.0.

### Key Features

| Feature | Description |
|---------|-------------|
| **Full API coverage** | All 122 operations of MWDB Core 2.18.0, enforced by a spec regression test |
| **Async + sync** | Async-native client with a synchronous facade over the same implementation |
| **Multi-format output** | Rich tables, JSON, TOON, and SARIF 2.1.0 |
| **Typed models** | Dataclasses for files, configs, blobs and objects, keeping the full raw payload |
| **Concurrent transfers** | Bulk downloads with `--jobs`; blocking I/O offloaded to threads |
| **Resilient transport** | Automatic retry/backoff on 429/5xx and typed exceptions |
| **CLI + Library** | Use the `mwdb` command or import the Python package |
| **100% tested** | Live tests against a real MWDB instance (no mocks), 100% coverage |

### Supported Outputs

```text
Object data     JSON, TOON
Listings        Rich tables, JSON, TOON, SARIF 2.1.0
Findings        SARIF 2.1.0 (samples/objects as results)
Downloads       Streamed files, concurrent (--jobs)
```

---

## Installation

### From PyPI (Recommended)

```bash
pip install mwdb-cli
```

### From Source

```bash
git clone https://github.com/seifreed/mwdb-cli.git
cd mwdb-cli
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e . --group dev
```

---

## Configuration

Settings resolve in order: CLI flags / constructor arguments → environment →
config file → defaults.

```bash
export MWDB_URL="https://mwdb.cert.pl"     # default
export MWDB_API_KEY="<your API key>"
```

or `~/.mwdb.toml`:

```toml
[mwdb]
url = "https://mwdb.cert.pl"
api_key = "<your API key>"
```

---

## Quick Start

```bash
# Ping the server
mwdb server ping

# List the ten most recent samples
mwdb file list --count 10

# Export search results as a SARIF 2.1.0 document
mwdb --format sarif search 'tag:emotet' > results.sarif
```

---

## Usage

### Command Line Interface

```bash
mwdb file get <sha256>
mwdb search 'tag:emotet AND file.size:[* TO 500000]'
mwdb file download <sha256> <sha256> ... --jobs 8 -o samples/
mwdb file download <sha256> --zip -o samples/
mwdb file upload sample.bin --tags my-tag --share-3rd-party false
mwdb tag add <sha256> my-tag
mwdb comment add <sha256> "packed with UPX"
mwdb config list --query 'config.family:emotet'
mwdb attribute add <sha256> source '{"feed": "honeypot"}'
mwdb --json file get <sha256> | jq .tags
```

Every API area has a command group:
`file`, `config`, `blob`, `object`, `tag`, `comment`, `attribute`, `share`,
`relation`, `karton`, `quick-query`, `auth`, `user`, `api-key`, `group`,
`attribute-def`, `metakey`, `oauth`, `remote`, `server`, plus top-level
`search`. Run `mwdb <group> --help` for the operations in each group.

Global options: `--url`, `--api-key`, `--config`, `--format`, `--json`.

### Output Formats

`--format` selects how results are rendered (default: `table`):

| Option | Description |
|--------|-------------|
| `--format table` | Human-readable rich tables (default) |
| `--format json` | Pretty JSON (`--json` is a backward-compatible alias) |
| `--format toon` | [TOON](https://github.com/toon-format/toon): compact, token-efficient for LLMs |
| `--format sarif` | [SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/) findings |

```bash
mwdb --format toon file list           # tabular TOON block
mwdb --format sarif file list          # SARIF 2.1.0 document
mwdb --json file get <sha256>          # same as --format json
```

**SARIF** is a findings schema, so it is available **only** for commands that
return samples or objects (`file`/`config`/`blob`/`object` `list` and `get`,
and `search`). Each object becomes one SARIF result (artifact = sha256,
ruleId = family/tag/type). Other commands report
`SARIF output is not available for this command.`

---

## Python Library

### Async

```python
import asyncio
from pathlib import Path
from mwdb_cli import AsyncMwdbClient

async def main() -> None:
    async with AsyncMwdbClient() as client:  # settings from env/config file
        async for sample in client.files.iterate(query="tag:emotet"):
            print(sample.sha256, sample.file_name)
            await client.files.download(sample.id, Path(sample.id))
            break

asyncio.run(main())
```

### Sync

```python
from mwdb_cli import MwdbClient

with MwdbClient() as client:  # same API surface, runs the async core internally
    for sample in client.files.iterate(query="tag:emotet", chunk_size=50):
        print(sample.sha256)
    stats = client.configs.stats()
```

### Concurrent bulk work

```python
from pathlib import Path
from mwdb_cli import AsyncMwdbClient
from mwdb_cli.bulk import run_limited

async def bulk(client: AsyncMwdbClient) -> None:
    hashes = [f.id async for f in client.files.iterate(query="tag:emotet")]
    await run_limited(
        [lambda h=h: client.files.download(h, Path(h)) for h in hashes],
        limit=8,
    )
```

### TOON and SARIF encoders

```python
from mwdb_cli import sarif, toon, MwdbClient

with MwdbClient() as client:
    samples = client.files.list(query="tag:emotet", count=20)

print(toon.encode([s.raw for s in samples]))     # compact TOON
if sarif.is_supported(samples):
    document = sarif.encode(samples)              # SARIF 2.1.0 dict
```

Errors are typed: `AuthError`, `ForbiddenError`, `NotFoundError`,
`ValidationError`, `ConflictError`, `RateLimitError`, `ServerError`,
`MwdbConnectionError` — all subclasses of `MwdbError`. Rate-limited and
transient 5xx responses are retried automatically with backoff.

---

## Development

Quality gates (all must pass clean, with no suppressions):

```bash
black --check . && ruff check . && mypy .
bandit -r -c pyproject.toml . && pip-audit
MWDB_API_KEY=<key> pytest        # live suite, 100% coverage enforced
```

The test suite talks to a real MWDB instance (no mocks): read operations run
for real; mutating admin operations are exercised against requests the server
rejects (missing capability → 403, nonexistent object → 404), so production
data is never modified. Transport edge cases (retries, malformed bodies) run
against a real in-process HTTP server.

---

## Requirements

- Python 3.14+
- Runtime dependencies: `httpx`, `click`, `rich`
- See [pyproject.toml](pyproject.toml) for the full list

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Support the Project

If this project is useful in your workflows, you can support development:

<a href="https://buymeacoffee.com/seifreed" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="50">
</a>

---

## License

This project is licensed under the MIT license. See [LICENSE](LICENSE).

**Attribution**
- Author: **Marc Rivero López** | [@seifreed](https://github.com/seifreed)
- Repository: [github.com/seifreed/mwdb-cli](https://github.com/seifreed/mwdb-cli)

---

<p align="center">
  <sub>Built for practical malware triage and threat-intelligence automation</sub>
</p>
