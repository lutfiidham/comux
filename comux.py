#!/usr/bin/env python3
"""
Comux - Interactive Command-Line Coding Assistant
An offline-first CLI tool for interactive coding sessions with AI assistance.
"""

import json
import os
import re
import sys
import subprocess
import tempfile
import difflib
import threading
import time
import itertools
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import requests

# Set stdout to unbuffered for Termux compatibility
class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)

# Simple color class
class Colors:
    """Simple color class with auto-detection."""

    def __init__(self):
        # Check if terminal supports colors
        self.supports_color = self._check_color_support()
        self._init_colors()

    def _check_color_support(self):
        """Check if terminal supports colors."""
        term = os.getenv('TERM', '').lower()
        colorterm = os.getenv('COLORTERM', '').lower()

        if colorterm in ['truecolor', '24bit']:
            return True
        elif 'color' in term or term in ['xterm-256color', 'screen-256color']:
            return True
        elif os.isatty(1):
            return True
        return False

    def _init_colors(self):
        """Initialize color codes."""
        if self.supports_color:
            self.RESET = '\033[0m'
            self.BOLD = '\033[1m'
            self.DIM = '\033[2m'
            self.RED = '\033[31m'
            self.GREEN = '\033[32m'
            self.YELLOW = '\033[33m'
            self.BLUE = '\033[34m'
            self.MAGENTA = '\033[35m'
            self.CYAN = '\033[36m'
            self.WHITE = '\033[37m'
            self.BRIGHT_RED = '\033[91m'
            self.BRIGHT_GREEN = '\033[92m'
            self.BRIGHT_YELLOW = '\033[93m'
            self.BRIGHT_BLUE = '\033[94m'
            self.BRIGHT_MAGENTA = '\033[95m'
            self.BRIGHT_CYAN = '\033[96m'
            self.BRIGHT_WHITE = '\033[97m'
        else:
            self.RESET = ''
            self.BOLD = ''
            self.DIM = ''
            self.RED = self.GREEN = self.YELLOW = self.BLUE = ''
            self.MAGENTA = self.CYAN = self.WHITE = ''
            self.BRIGHT_RED = self.BRIGHT_GREEN = self.BRIGHT_YELLOW = ''
            self.BRIGHT_BLUE = self.BRIGHT_MAGENTA = self.BRIGHT_CYAN = ''
            self.BRIGHT_WHITE = ''

    def colorize(self, text, color):
        return f"{color}{text}{self.RESET}"

    def success(self, text):
        return self.colorize(text, self.BRIGHT_GREEN)

    def error(self, text):
        return self.colorize(text, self.BRIGHT_RED)

    def warning(self, text):
        return self.colorize(text, self.BRIGHT_YELLOW)

    def info(self, text):
        return self.colorize(text, self.BRIGHT_BLUE)

    def cyan(self, text):
        return self.colorize(text, self.CYAN)

    def magenta(self, text):
        return self.colorize(text, self.MAGENTA)

    def prompt(self, text):
        return self.colorize(text, self.BOLD + self.CYAN)

    def header(self, text):
        return self.colorize(text, self.BOLD + self.BRIGHT_BLUE)

# Create global instance
colors = Colors()

# Make colors accessible as class attributes
Colors.RESET = colors.RESET
Colors.BOLD = colors.BOLD
Colors.DIM = colors.DIM
Colors.RED = colors.RED
Colors.GREEN = colors.GREEN
Colors.YELLOW = colors.YELLOW
Colors.BLUE = colors.BLUE
Colors.MAGENTA = colors.MAGENTA
Colors.CYAN = colors.CYAN
Colors.WHITE = colors.WHITE
Colors.BRIGHT_RED = colors.BRIGHT_RED
Colors.BRIGHT_GREEN = colors.BRIGHT_GREEN
Colors.BRIGHT_YELLOW = colors.BRIGHT_YELLOW
Colors.BRIGHT_BLUE = colors.BRIGHT_BLUE
Colors.BRIGHT_MAGENTA = colors.BRIGHT_MAGENTA
Colors.BRIGHT_CYAN = colors.BRIGHT_CYAN
Colors.BRIGHT_WHITE = colors.BRIGHT_WHITE

# Add class methods
Colors.colorize = classmethod(lambda cls, text, color: colors.colorize(text, color))
Colors.success = classmethod(lambda cls, text: colors.success(text))
Colors.error = classmethod(lambda cls, text: colors.error(text))
Colors.warning = classmethod(lambda cls, text: colors.warning(text))
Colors.info = classmethod(lambda cls, text: colors.info(text))
Colors.cyan = classmethod(lambda cls, text: colors.cyan(text))
Colors.magenta = classmethod(lambda cls, text: colors.magenta(text))
Colors.prompt = classmethod(lambda cls, text: colors.prompt(text))
Colors.header = classmethod(lambda cls, text: colors.header(text))


class LoadingIndicator:
    """Animated loading indicator for long-running operations."""

    def __init__(self, message="Thinking"):
        self.message = Colors.cyan(message)
        self.running = False
        self.thread = None
        # Use colored spinners
        self.spinners = [
            f"{Colors.YELLOW}|{Colors.RESET}",
            f"{Colors.YELLOW}/{Colors.RESET}",
            f"{Colors.YELLOW}-{Colors.RESET}",
            f"{Colors.YELLOW}\\{Colors.RESET}"
        ]
        self.spinner = itertools.cycle(self.spinners)
        self.last_len = 0

    def start(self):
        """Start the loading animation."""
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the loading animation."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.3)
        # Clear the entire line
        self._clear_line()

    def _clear_line(self):
        """Clear the current line."""
        if self.last_len > 0:
            sys.stdout.write('\r' + ' ' * self.last_len + '\r')
            self.last_len = 0

    def _animate(self):
        """Internal animation loop."""
        # Small initial delay
        time.sleep(0.1)
        while self.running:
            # Build the spinner line with colors
            spinner_char = next(self.spinner)
            line = f'{self.message} {spinner_char}'
            self.last_len = len(line)

            # Write with carriage return
            sys.stdout.write('\r' + line)
            # No need to flush with Unbuffered class

            time.sleep(0.2)


class ComuxSession:
    """Manages conversation history and session state."""

    def __init__(self, session_file: Optional[str] = None):
        self.messages = []
        self.session_file = session_file or ".comux_session.json"
        self.load_session()

    def load_session(self):
        """Load previous session if exists."""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    self.messages = data.get('messages', [])
            except Exception as e:
                print(f"Warning: Could not load session file: {e}")

    def save_session(self):
        """Save current session to disk."""
        try:
            with open(self.session_file, 'w') as f:
                json.dump({
                    'messages': self.messages,
                    'last_saved': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session: {e}")

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content
        })
        self.save_session()


class FileOperations:
    """Handles all file system operations safely."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir).resolve()

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents."""
        try:
            full_path = self._resolve_path(path)
            if not full_path.is_file():
                return {"error": f"File not found: {path}"}

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {"content": content, "path": str(full_path)}
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        try:
            full_path = self._resolve_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"error": str(e)}

    def patch_file(self, path: str, patch: str) -> Dict[str, Any]:
        """Apply a unified diff patch to a file."""
        try:
            full_path = self._resolve_path(path)
            if not full_path.is_file():
                return {"error": f"File not found: {path}"}

            # Read original content
            with open(full_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()

            # Parse and apply patch
            patched_lines = self._apply_patch(original_lines, patch)

            # Show diff and ask for confirmation
            diff = ''.join(difflib.unified_diff(
                original_lines, patched_lines,
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                lineterm=''
            ))

            if diff:
                print("\nProposed changes:")
                print(diff)
                if not self._confirm("Apply these changes?"):
                    return {"success": False, "message": "Changes cancelled by user"}

            # Write patched content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(patched_lines)

            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"error": str(e)}

    def list_files(self, path: str = ".") -> Dict[str, Any]:
        """List files in directory."""
        try:
            full_path = self._resolve_path(path)
            if not full_path.is_dir():
                return {"error": f"Directory not found: {path}"}

            files = []
            for item in full_path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })

            return {"files": sorted(files, key=lambda x: (x['type'], x['name']))}
        except Exception as e:
            return {"error": str(e)}

    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to work directory."""
        return (self.work_dir / path).resolve()

    def _apply_patch(self, original_lines: List[str], patch: str) -> List[str]:
        """Apply a unified diff patch."""
        # Simple patch application (for production, use a proper patch library)
        lines = original_lines[:]
        patch_lines = patch.split('\n')

        i = 0
        while i < len(patch_lines):
            line = patch_lines[i]
            if line.startswith('@@'):
                # Parse hunk header
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_start = int(match.group(1)) - 1
                    # Apply hunk
                    i += 1
                    new_lines = []
                    while i < len(patch_lines) and not patch_lines[i].startswith('@@') and not patch_lines[i].startswith('---'):
                        if patch_lines[i].startswith(' '):
                            new_lines.append(patch_lines[i][1:])
                        elif patch_lines[i].startswith('-'):
                            # Remove line
                            pass
                        elif patch_lines[i].startswith('+'):
                            new_lines.append(patch_lines[i][1:])
                        i += 1

                    # Replace lines
                    lines[old_start:old_start + len([l for l in new_lines if not l.startswith('+')])] = \
                        [l + '\n' for l in new_lines if not l.startswith('-') and not l.startswith('+')]
                    continue
            i += 1

        return lines

    def _confirm(self, message: str) -> bool:
        """Ask for user confirmation."""
        response = input(f"{message} [y/N] ").strip().lower()
        return response in ['y', 'yes']


class ZAIClient:
    """Client for Z.ai GLM API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ZAI_API_KEY')
        self.base_url = "https://api.z.ai/api/coding/paas/v4/chat/completions"
        self.model = "glm-4.6"

    def chat(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Send chat request to Z.ai API."""
        if not self.api_key:
            return {"error": "ZAI_API_KEY environment variable not set"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 8000  # Increased to prevent truncation
        }

        # Retry mechanism
        max_retries = 3
        timeouts = [60, 90, 120]  # Progressive timeout

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=timeouts[attempt],
                    stream=False
                )

                # Debug: print status
                if response.status_code != 200:
                    return {"error": f"API returned status {response.status_code}: {response.text[:200]}"}

                return response.json()
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    # Don't print for first retry to avoid noise
                    if attempt > 0:
                        print(f"Timeout, retrying... (attempt {attempt + 2}/{max_retries})")
                    continue
                return {"error": f"API request timed out after {timeouts[-1]} seconds. Try again later."}
            except requests.exceptions.ConnectionError as e:
                return {"error": f"Could not connect to API server: {str(e)}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"API request failed: {str(e)}"}

        return {"error": "Failed after multiple retries"}


class ComuxREPL:
    """Main REPL loop for Comux."""

    def __init__(self):
        self.session = ComuxSession()
        self.file_ops = FileOperations()
        self.client = ZAIClient()
        self.running = False

        # System prompt
        self.system_prompt = """You are Comux, an interactive command-line coding assistant. You help users with coding tasks by reading, creating, and editing files.

IMPORTANT: Your response MUST be either:
1. Plain text for explanations and discussions
2. Valid JSON ONLY when you need to interact with files

When you need to interact with the filesystem, respond with ONLY valid JSON in this exact format:
{
  "tool": "<tool_name>",
  "args": {...}
}

Available tools:
- read_file: {"path": "relative/path/to/file"}
- write_file: {"path": "relative/path/to/file", "content": "complete file content"}
- patch_file: {"path": "relative/path/to/file", "patch": "unified diff"}
- list_files: {"path": "."}

CRITICAL RULES:
- NEVER mix JSON with natural language
- NEVER write explanations outside JSON when making tool calls
- ALWAYS provide COMPLETE file content for write_file
- If you're creating HTML/CSS/JS files, include the FULL code
- Do NOT truncate file content
- Never access files outside the current directory
- For simple questions, respond with plain text only"""

    def start(self):
        """Start the REPL session."""
        self.running = True

        # Colored welcome message
        print(f"\n{Colors.BRIGHT_YELLOW}🚀 {Colors.BRIGHT_CYAN}Comux{Colors.RESET} {Colors.BRIGHT_WHITE}- Interactive Command-Line Coding Assistant{Colors.RESET}")
        print(f"{Colors.DIM}Type {Colors.CYAN}'help'{Colors.DIM} for commands or {Colors.CYAN}'exit'{Colors.DIM} to quit{Colors.RESET}\n")

        # Initialize session with system prompt if empty
        if not self.session.messages:
            self.session.add_message("system", self.system_prompt)

        while self.running:
            try:
                user_input = self._get_input()
                if not user_input:
                    continue

                # Handle special commands
                if self._handle_command(user_input):
                    continue

                # Process file mentions (@filename)
                processed_input = self._process_file_mentions(user_input)

                # Add user message (with expanded file content)
                self.session.add_message("user", processed_input)

                # Get AI response
                response = self._get_ai_response()
                if response:
                    # Debug: check if response looks like JSON but incomplete
                    response_stripped = response.strip()
                    if response_stripped.startswith('{') and not response_stripped.endswith('}'):
                        print(f"\n{Colors.warning('⚠️  Incomplete JSON response from AI')}")
                        print(f"{Colors.DIM}Raw response:{Colors.RESET} {response[:100] + '...' if len(response) > 100 else response}")
                        continue

                    # Handle tool calls or plain text
                    if self._is_tool_call(response):
                        result = self._execute_tool_call(response)
                        if result.startswith("✅") or result.startswith("Created") or result.startswith("File"):
                            print(Colors.success(result))
                        elif result.startswith("❌") or result.startswith("Error"):
                            print(Colors.error(result))
                        else:
                            print(Colors.cyan(result))
                        # Add result to conversation
                        self.session.add_message("assistant", f"Tool result: {result}")
                    else:
                        print(Colors.BRIGHT_WHITE + response)
                        self.session.add_message("assistant", response)

            except KeyboardInterrupt:
                print(f"\n{Colors.WARNING}Use {Colors.CYAN}'exit'{Colors.WARNING} to quit{Colors.RESET}")
            except EOFError:
                break
            except Exception as e:
                print(f"{Colors.error(f'Error: {e}')}{Colors.RESET}")

        print(f"\n{Colors.BRIGHT_YELLOW}👋 Session ended{Colors.RESET}")

    def _get_input(self) -> str:
        """Get input from user."""
        try:
            line = input(Colors.prompt(">>> "))
            return line
        except EOFError:
            return "exit"

    def _process_file_mentions(self, user_input: str) -> str:
        """Process file mentions in user input (e.g., @file.py)."""
        import re

        # Find all @file mentions
        mentions = re.findall(r'@([^\s@]+)', user_input)

        # Process each mention
        for filename in mentions:
            # Try to read the file
            result = self.file_ops.read_file(filename)

            if 'content' in result:
                # Replace @file with file content in a code block
                file_content = result['content']
                # Limit content size to avoid huge prompts
                if len(file_content) > 2000:
                    file_content = file_content[:2000] + "\n... (truncated)"

                # Replace the mention
                user_input = user_input.replace(
                    f"@{filename}",
                    f"\n```file:{filename}\n{file_content}\n```"
                )
            else:
                # File not found, show error
                user_input = user_input.replace(
                    f"@{filename}",
                    f"\n[Error: File '{filename}' not found]"
                )

        return user_input

    def _handle_command(self, user_input: str) -> bool:
        """Handle special REPL commands."""
        cmd = user_input.strip().lower()

        if cmd in ['exit', 'quit']:
            self.running = False
            return True
        elif cmd == 'help':
            self._show_help()
            return True
        elif cmd.startswith('clear'):
            os.system('clear' if os.name == 'posix' else 'cls')
            return True
        elif cmd == 'offline':
            self._offline_mode()
            return True

        return False

    def _offline_mode(self):
        """Create files without API when timeout occurs."""
        print(f"\n{Colors.BRIGHT_CYAN}📝 Offline Mode - Creating file locally...{Colors.RESET}")

        # Get file path from user
        path = input(f"{Colors.CYAN}Enter file path (e.g., index.html): {Colors.RESET}").strip()
        if not path:
            print(f"{Colors.WARNING}No file path provided{Colors.RESET}")
            return

        # Default content based on extension
        ext = path.split('.')[-1].lower()
        content = ""

        if ext == 'html':
            content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beautiful Page</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 3rem;
            border-radius: 10px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 600px;
        }
        h1 {
            color: #333;
            margin-bottom: 1rem;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .button {
            background: #667eea;
            color: white;
            padding: 0.8rem 2rem;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 1rem;
        }
        .button:hover {
            background: #5a67d8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to My Page</h1>
        <p>This is a beautiful page created with Comux!</p>
        <button class="button" onclick="alert('Hello!')">Click Me</button>
    </div>
</body>
</html>"""
        elif ext == 'js':
            content = "// JavaScript file\nconsole.log('Hello World!');"
        elif ext == 'css':
            content = "/* CSS file */\nbody {\n    font-family: Arial;\n}"
        elif ext == 'py':
            content = "# Python file\nprint('Hello World!')"
        else:
            content = f"# {ext} file\n\n# Your content here"

        # Create directory if needed
        if '/' in path:
            dir_path = '/'.join(path.split('/')[:-1])
            os.makedirs(dir_path, exist_ok=True)

        # Write file
        result = self.file_ops.write_file(path, content)
        if result.get('success'):
            print(f"\n{Colors.success(f'✅ Created {path}')}")
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"\n{Colors.error(f'❌ Error: {error_msg}')}")

    def _show_help(self):
        """Show help information."""
        # Header
        print(f"\n{Colors.BRIGHT_CYAN}╭───────── Comux Commands ─────────╮{Colors.RESET}")
        print(f"{Colors.CYAN}│{Colors.RESET} {Colors.BRIGHT_YELLOW}exit, quit{Colors.RESET}    - Exit the session")
        print(f"{Colors.CYAN}│{Colors.RESET} {Colors.BRIGHT_YELLOW}help{Colors.RESET}          - Show this help")
        print(f"{Colors.CYAN}│{Colors.RESET} {Colors.BRIGHT_YELLOW}clear{Colors.RESET}         - Clear the screen")
        print(f"{Colors.CYAN}│{Colors.RESET} {Colors.BRIGHT_YELLOW}offline{Colors.RESET}       - Create files without AI (when API is slow)")
        print(f"{Colors.BRIGHT_CYAN}╰───────────────────────────────────╯{Colors.RESET}")

        # Usage
        print(f"\n{Colors.BRIGHT_BLUE}Usage:{Colors.RESET}")
        print(f"  • Type natural language instructions")
        print(f"  • Use {Colors.GREEN}@filename{Colors.RESET} to include file content in your prompt")

        print(f"\n{Colors.BRIGHT_MAGENTA}Examples:{Colors.RESET}")
        print(f"  • {Colors.DIM}\"Explain what {Colors.GREEN}@script.py{Colors.DIM} does\"{Colors.RESET}")
        print(f"  • {Colors.DIM}\"Fix the bug in {Colors.GREEN}@app.js{Colors.DIM}\"{Colors.RESET}")
        print(f"  • {Colors.DIM}\"Refactor {Colors.GREEN}@utils.py{Colors.DIM} to use list comprehensions\"{Colors.RESET}")
        print(f"  • {Colors.DIM}\"Create a beautiful {Colors.GREEN}index.html{Colors.DIM} file\"{Colors.RESET}")

        print(f"\n{Colors.BRIGHT_BLUE}Features:{Colors.RESET}")
        print(f"  • AI responds with text or JSON tool calls")
        print(f"  • File operations require confirmation")
        print(f"  • Colored output for better readability")

        print(f"\n{Colors.BRIGHT_YELLOW}Tips:{Colors.RESET}")
        print(f"  • If API times out, use {Colors.CYAN}'offline'{Colors.RESET} command to create templates")
        print(f"  • Supports HTML, CSS, JS, Python files in offline mode")

        print(f"\n{Colors.DIM}Environment:{Colors.RESET}")
        print(f"  • {Colors.BRIGHT_CYAN}ZAI_API_KEY{Colors.RESET} - Your Z.ai API key (required)")
        print()

    def _get_ai_response(self) -> Optional[str]:
        """Get response from AI model."""
        loading = LoadingIndicator("Thinking")
        loading.start()

        try:
            response = self.client.chat(self.session.messages)
            if response and 'choices' in response:
                return response['choices'][0]['message']['content']
            elif response and 'error' in response:
                return f"API Error: {response['error']}"
            elif response:
                # Debug: print the actual response
                return f"Unexpected API response: {str(response)[:200]}"
            return "No response from API"
        finally:
            loading.stop()
            # Small delay to ensure line is clear
            time.sleep(0.1)

    def _is_tool_call(self, response: str) -> bool:
        """Check if response is a tool call."""
        try:
            data = json.loads(response)
            # Check if it has required tool call structure
            return 'tool' in data and 'args' in data
        except json.JSONDecodeError:
            return False

    def _execute_tool_call(self, response: str) -> str:
        """Execute a tool call from JSON response."""
        try:
            data = json.loads(response)
            tool = data.get('tool')
            args = data.get('args', {})

            if tool == 'read_file':
                result = self.file_ops.read_file(args['path'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"File content:\n{result['content']}"

            elif tool == 'write_file':
                result = self.file_ops.write_file(args['path'], args['content'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"File written: {result['path']}"

            elif tool == 'patch_file':
                result = self.file_ops.patch_file(args['path'], args['patch'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"File patched: {result['path']}" if result.get('success') else result.get('message', 'Patch failed')

            elif tool == 'list_files':
                result = self.file_ops.list_files(args.get('path', '.'))
                if 'error' in result:
                    return f"Error: {result['error']}"

                output = []
                for item in result['files']:
                    icon = "📁" if item['type'] == 'directory' else "📄"
                    output.append(f"{icon} {item['name']}")
                return '\n'.join(output)

            else:
                return f"Unknown tool: {tool}"

        except Exception as e:
            return f"Tool execution error: {e}"


def main():
    """Entry point for comux CLI."""
    # Check for API key
    if not os.getenv('ZAI_API_KEY'):
        print("Error: ZAI_API_KEY environment variable not set")
        print("Get your API key from https://z.ai and set it with:")
        print("  export ZAI_API_KEY=your_api_key_here")
        sys.exit(1)

    # Start REPL
    repl = ComuxREPL()
    repl.start()


if __name__ == "__main__":
    main()