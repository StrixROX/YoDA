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

#### Install the Project and Dependencies in Editable Mode

```bash
pip install -e .
```

#### Generate Self-Signed SSL Certificates

```bash
openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt
```

#### Done!

_You are ready to develop!_

## Building

#### For Development (in editable mode)

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
