# logdiff

> Command-line utility to diff structured JSON log files and surface meaningful field-level changes across deployments.

---

## Installation

```bash
pip install logdiff
```

Or install from source:

```bash
git clone https://github.com/youruser/logdiff.git
cd logdiff
pip install -e .
```

---

## Usage

Compare two JSON log files and surface field-level differences:

```bash
logdiff logs/deploy-v1.json logs/deploy-v2.json
```

**Example output:**

```
[2024-06-01T12:00:00Z] event: "request_handled"
  ~ status_code : 200 → 500
  + error_message: "upstream timeout"
  - response_time_ms: 42

3 changes detected across 1 matching log entries.
```

### Options

| Flag | Description |
|------|-------------|
| `--key FIELD` | Match log entries by a specific field (default: `id`) |
| `--ignore FIELD` | Exclude a field from comparison |
| `--format [text\|json]` | Output format (default: `text`) |
| `--only-changes` | Show only entries that differ |

```bash
logdiff before.json after.json --key request_id --ignore timestamp --format json
```

---

## Requirements

- Python 3.8+

---

## License

MIT © 2024 [youruser](https://github.com/youruser)