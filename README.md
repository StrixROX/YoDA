## YoDA — Centralised System Automations with LLM

YoDA is a Python-based platform that empowers system automations with LLM assistance. It aims to provide a reliable, extensible foundation for day-to-day automations, memory across sessions, and a friendly CLI to interact with your system.

### Features

- **Session greeting**: A simple greeting on logon.
- **Persistent memory**: Remembers information across system sessions.
- **Startup automations**: Remembers and launches your preferred apps at startup.
- **CLI tooling**: Interact with the app via a dedicated command-line tool.

### Project Status

This project is in early development (version 0.0.1). The scope is intentionally small and evolving. Feedback and contributions are welcome.

## Quickstart

### Prerequisites

- Python 3.10 or newer
- OpenSSL (for local SSL certificate generation)

### Create and Activate a Virtual Environment

```bash
python -m venv dev
source dev/Scripts/activate
```

On macOS/Linux, activate with:

```bash
source dev/bin/activate
```

### Install (Editable)

```bash
pip install -e .
```

This installs the package and exposes the `yo` CLI.

### Verify Installation

```bash
yo --help
```

## Usage

After installation, use the CLI:

```bash
yo --help
```

Additional examples and commands will be added as the feature set grows.

## Development

### Local Development Setup

1. Create and activate a virtual environment (see Quickstart).
2. Install in editable mode:
   ```bash
   pip install -e .
   ```
3. Run the CLI locally to validate changes:
   ```bash
   yo --help
   ```

### Generating Self-Signed SSL Certificates 

If you need SSL for local testing:

```bash
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt
```

## Building & Distribution

### Build a Wheel and Source Distribution

```bash
pip install build
python -m build
```

Artifacts will be created under `dist/`.

## Project Structure

```
src/
  app_streams/    # Event stream helpers
  cli/            # CLI entrypoints and utilities
  comms/          # Communication/server helpers
  core/           # Core application logic and event handling
  llm/            # LLM-related modules (e.g., TTS)
```

## Future Scope

- Display interface for showing results, images, and emotes.
- Screen context awareness to answer questions about on-screen content.
- Additional automation primitives and integrations.

If you have ideas, please open an issue or a discussion.

## Contributing

Contributions are welcome! Please read `CONTRIBUTING.md` for guidelines on how to propose changes, set up your environment, and submit pull requests.

## Versioning

This project follows semantic versioning where practical: MAJOR.MINOR.PATCH.

## Support & Feedback

- If you encounter a bug, please open an issue with steps to reproduce and environment details.
- For feature requests or questions, start a discussion or open an issue.

## License

License information will be added to the repository. Until then, please treat the project as source-available for evaluation and contribution discussions only.
