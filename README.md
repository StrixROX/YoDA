# Centralised System Automations Platform with LLM - YoDA

The aim with this project is to create a platform with features that can help empower system automations with LLM assistance.

## Environment Setup

#### Create a Development Environment

```bash
python -m venv dev
```

#### Load the Environment

```bash
source dev/Scripts/activate
```

## Building

#### For Development

```bash
pip install -e .
```

#### For Production / Testing

```bash
pip install build # install the build package

python -m build # build your project
```

## Current Scope

- System greeting on logon.
- Giving Memory to the application - should remember things between system sessions.
- Simple automations such as remember which apps to run on startup (managed by the app itself) and runnning them.
- CLI to interact with the app.

## Future Scope

- Give the app a display interface where it can show results/images/emotes.
- Give the app screen context to answer questions about the screen.

_**Note**: Currently accepting suggestions for expanding the scope._
