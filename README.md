# Comux - Interactive Command-Line Coding Assistant

An offline-first CLI tool for interactive coding sessions with AI assistance, designed for Android/Termux.

## Features

- **Interactive REPL**: Continuous chat sessions with context persistence
- **File Operations**: Read, create, copy, move, and delete files
- **Directory Management**: Create, list, and delete directories
- **Code Search**: Search patterns across multiple files
- **Git Integration**: Status, diff, log, add, and commit operations
- **Shell Commands**: Execute system commands safely
- **Session Memory**: Automatically saves and resumes conversations
- **Tool Calling**: Structured JSON-based tool invocation
- **Loading Indicator**: Animated spinner while waiting for AI responses
- **Offline-First**: Works without internet except for API calls
- **Minimal Dependencies**: Only requires `requests` library

## Available Tools

Comux provides 20+ AI-powered tools for coding assistance:

### File System

- `read_file` - Read file contents
- `write_file` - Write or overwrite files
- `patch_file` - Apply unified diff patches
- `list_files` - List directory contents
- `create_directory` - Create new directories
- `delete_file` - Delete files
- `delete_directory` - Delete directories (with recursive option)
- `copy_file` - Copy files
- `move_file` - Move/rename files
- `file_exists` - Check if file/directory exists
- `get_file_info` - Get detailed file information

### Code Analysis

- `search_in_files` - Search patterns across multiple files with regex support

### Shell Operations

- `run_command` - Execute shell commands safely

### Git Operations

- `git_status` - View git repository status
- `git_diff` - View file changes
- `git_log` - View commit history
- `git_add` - Stage files for commit
- `git_commit` - Create commits

For complete documentation, see [TOOLS.md](TOOLS.md).

### File Autocomplete

When typing file references with `@filename`, you can use Tab completion:

```bash
# Type @ followed by partial filename, then Tab
>>> @RE[TAB]         # Autocompletes to: @README.md
>>> @comu[TAB]       # Autocompletes to: @comux.py
>>> @src/[TAB]       # Shows all files in src/ directory
>>> read @[TAB]       # Shows all available files
```

**Features:**
- Case-sensitive matching (primary)
- Case-insensitive fallback
- Works with subdirectories
- Skips hidden files and cache folders

**Requirements:**
- **Linux/Mac**: Built-in readline support
- **Windows**: `pip install pyreadline3`
- **Termux**: Usually built-in, or `pip install gnureadline` if needed

### Terminal Line Wrapping Issues

If you experience issues with long lines not wrapping properly (text overwriting at line start), you can set custom readline settings:

```bash
# For Windows Command Prompt
export COMUX_READLINE_SETTINGS="set preferred-editing-mode vi"

# For older terminals
export COMUX_READLINE_SETTINGS="set horizontal-scroll-mode On"

# For custom terminal behavior
export COMUX_READLINE_SETTINGS="set bell-style none,set editing-mode vi"
```

### Response Streaming

Comux now supports streaming responses for real-time output:

```bash
# Enable streaming (default)
comux

# Disable streaming if needed
export COMUX_STREAM=false
comux
```

With streaming enabled, you'll see responses appear word by word, just like ChatGPT:
```bash
>>> Explain quantum computing
Quantum computing is a revolutionary approach to computation that leverages the principles of quantum mechanics...
```

## Installation

### On Android/Termux

```bash
# Method 1: Automated setup (recommended)
git clone https://github.com/lutfiidham/comux.git
cd comux
chmod +x setup_termux.sh
./setup_termux.sh

# Method 2: Manual setup
# Install Python and required packages
pkg update && pkg install python clang make libffi

# Install Python dependencies
pip install -r requirements.txt
# If autocomplete doesn't work, install: pip install gnureadline

# Install Comux
pip install -e .

# Create command alias
echo 'alias comux="python -m comux"' >> ~/.bashrc
source ~/.bashrc

# Method 3: Create symlink
ln -sf "$(pwd)/comux.py" ~/../usr/bin/comux
chmod +x ~/../usr/bin/comux
```

**Autocomplete in Termux:**

- Most Termux environments have readline built-in
- If autocomplete doesn't work, install: `pip install gnureadline`
- Use Tab after `@` for file completion: `@filename[TAB]`

### Using pip (recommended for non-Termux systems)

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

## Updating Comux

### Method 1: Quick Update (from anywhere)

```bash
# Create a global update command
echo 'alias comux-update="python ~/comux/quick_update.py"' >> ~/.bashrc
source ~/.bashrc

# Now update anytime with
comux-update
```

### Method 2: Manual Update

```bash
cd ~/comux
./update.sh
```

### Method 3: Using Git

```bash
cd ~/comux
git stash  # Save local changes
git pull   # Pull updates
git stash pop  # Restore changes
pip install -e .  # Reinstall
```

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

# On Termux, install without sudo
pip install -e .

# Or create symlink manually
ln -sf "$(pwd)/comux.py" ~/../usr/bin/comux
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
