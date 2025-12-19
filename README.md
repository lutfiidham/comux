# Comux - Interactive Command-Line Coding Assistant

An offline-first CLI tool for interactive coding sessions with AI assistance, designed for Android/Termux.

## Features

- **Interactive REPL**: Continuous chat sessions with context persistence
- **File Operations**: Read, create, and edit files safely
- **Session Memory**: Automatically saves and resumes conversations
- **Tool Calling**: Structured JSON-based tool invocation
- **Offline-First**: Works without internet except for API calls
- **Minimal Dependencies**: Only requires `requests` library

## Installation

### On Android/Termux

```bash
# Install Python and pip
pkg update && pkg install python

# Clone or download comux
git clone https://github.com/yourusername/comux.git
cd comux

# Install dependencies
pip install -r requirements.txt

# Make comux executable
chmod +x comux.py

# Create global command (optional)
sudo ln -s $(pwd)/comux.py /usr/local/bin/comux
```

### Using pip (recommended)

```bash
pip install comux
```

## Setup

1. Get your API key from [Z.ai](https://z.ai)
2. Set the environment variable:

```bash
export ZAI_API_KEY=your_api_key_here
```

Add this to your `.bashrc` or `.zshrc` to make it permanent:

```bash
echo 'export ZAI_API_KEY=your_api_key_here' >> ~/.bashrc
source ~/.bashrc
```

## Usage

Start an interactive session:

```bash
comux
```

### Example Session

```
🚀 Comux - Interactive Coding Assistant
Type 'help' for commands or 'exit' to quit
>>> Create a Python script that prints "Hello, World!"

{
  "tool": "write_file",
  "args": {
    "path": "hello.py",
    "content": "#!/usr/bin/env python3\n\nprint(\"Hello, World!\")\n"
  }
}

File written: /data/data/com.termux/files/home/hello.py

>>> Now run the script

{
  "tool": "read_file",
  "args": {
    "path": "hello.py"
  }
}

File content:
#!/usr/bin/env python3

print("Hello, World!")

The script has been created. You can run it with:
python hello.py
```

### Commands

- `exit` or `quit` - Exit the session
- `help` - Show help information
- `clear` - Clear the screen

### Tool Calling Contract

When the assistant needs to interact with files, it responds with JSON:

```json
{
  "tool": "read_file|write_file|patch_file|list_files",
  "args": {
    ...
  }
}
```

Available tools:
- `read_file`: Read file contents
- `write_file`: Create or overwrite a file
- `patch_file`: Apply a unified diff patch
- `list_files`: List directory contents

## Session Management

Comux automatically saves your session to `.comux_session.json` in the current directory. This allows you to:

- Resume conversations after closing the app
- Maintain context across multiple sessions
- Reference previous discussions

## Security

- Never accesses files outside the current project directory
- Asks for confirmation before applying patches
- Shows diffs before modifying files
- API key is stored only in environment variables

## Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $ZAI_API_KEY

# Set API key temporarily
export ZAI_API_KEY=your_key_here

# Set API key permanently
echo 'export ZAI_API_KEY=your_key_here' >> ~/.bashrc
```

### Permission Issues

```bash
# Make comux executable
chmod +x comux.py

# Or install globally
sudo pip install comux
```

### Network Issues

Comux requires internet connection only for API calls. All file operations work offline.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.