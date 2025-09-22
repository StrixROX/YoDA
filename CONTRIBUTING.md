## Contributing to YoDA

Thank you for your interest in contributing! This document outlines the process to get started and the standards we follow to keep the project healthy.

### Code of Conduct

Be kind and respectful. Assume positive intent. We welcome contributors from all backgrounds and experience levels.

### Getting Started

1. Fork the repository and create your branch from `main`.
2. Set up a local environment:

   ```bash
   python -m venv dev

   source dev/Scripts/activate  # Windows Git Bash / PowerShell may differ

   # On macOS/Linux: source dev/bin/activate
   pip install -e .
   ```

3. Run the CLI locally to verify your environment:
   ```bash
   yo --help
   ```

### Development Workflow

- Prefer small, focused pull requests.
- Write clear commit messages and PR descriptions that explain the change and the motivation.
- Keep changes backwards compatible when feasible.

### Style and Quality

- Python 3.10+.
- Follow PEP 8 for style and type-hint where reasonable.
- Keep functions small and focused; avoid deep nesting and unnecessary complexity.

### Project Structure

Place code under `src/` following the existing module organization:

```
src/
  app_streams/          # Event stream helpers and utilities
  cli/                  # Command-line interface and user interaction
  comms/                # Communication and networking
  core/                 # Core application logic and orchestration
    services/           # Core service implementations
  llm/                  # LLM integration and AI capabilities
    agent/              # AI agent implementation
```

Each module has a specific responsibility:

- **app_streams**: Handles event streaming and processing
- **cli**: Manages command-line interface and user interactions
- **comms**: Provides communication and networking functionality
- **core**: Contains main application logic, event handling, and core services
- **llm**: Implements LLM integration, TTS, and AI agent capabilities

> Note: You are free to create more packages/modules and/or re-organise existing packages if necessary. However, it will be treated as a major version update.

### Submitting Changes

1. Ensure your branch is up-to-date with `main`.
2. Run your changes locally and ensure the CLI behaves as expected.
3. Open a pull request:
   - Provide context: the problem, the approach, and alternatives considered.
   - Link related issues if applicable.
   - Add screenshots or terminal output when helpful.

### Reporting Issues

When filing an issue, include:

- Your OS and Python version
- Steps to reproduce
- Expected vs actual behavior
- Logs or stack traces if available

### Release Process (maintainers)

- Update version in `pyproject.toml` following semver.
- Build artifacts with:
  ```bash
  pip install build
  python -m build
  ```
- Create a GitHub release and upload artifacts if applicable.

### Questions

Open a discussion or issue if anything is unclear. We’re happy to help you get started.
