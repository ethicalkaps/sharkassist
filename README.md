# 🦈 SharkAssist

A floating Python desktop app that sits alongside Wireshark and converts plain English into Wireshark display filters using a local [Ollama](https://ollama.com) model.

## Features

- **Plain English → Wireshark filter** powered by `mistral` running locally
- **Explanation** of what each filter captures
- **Next steps** suggestions for deeper investigation
- **Session history** — click any previous filter to re-display it
- **Floating window** — always on top, stays visible next to Wireshark
- No internet required — fully local inference via Ollama

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running on `localhost:11434`
- `mistral` model pulled: `ollama pull mistral`

## Installation

```bash
git clone https://github.com/ethicalkaps/sharkassist.git
cd sharkassist
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS / Linux
pip install requests
```

## Usage

```bash
python main.py
```

Type a plain-English description of the traffic you want to filter, then press **Enter**.

**Examples:**
- `show me all HTTP traffic to port 80`
- `filter DNS queries from 192.168.1.5`
- `display only TCP SYN packets`

## Project Structure

```
sharkassist/
├── main.py            # Entry point
├── gui.py             # Tkinter UI (dark theme, always-on-top)
├── ollama_client.py   # Ollama REST API wrapper
├── prompt_builder.py  # System prompt + response parser
└── session.py         # In-session filter history
```

## License

MIT
