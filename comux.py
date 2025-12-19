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

# Try to import readline for better input handling
# Termux and most Unix systems have readline built-in
try:
    import readline
    HAVE_READLINE = True
except ImportError:
    # Try gnureadline for Termux
    try:
        import gnureadline as readline
        HAVE_READLINE = True
    except ImportError:
        # On Windows, try pyreadline3
        try:
            import pyreadline3 as readline
            HAVE_READLINE = True
        except ImportError:
            HAVE_READLINE = False

# Detect environment
IS_TERMUX = os.environ.get('TERMUX_VERSION') is not None
IS_WINDOWS = sys.platform.startswith('win')

# Additional setup for better Termux compatibility
if HAVE_READLINE and IS_TERMUX:
    try:
        # Setup for Termux environment
        # Some Termux environments might need special handling
        # for proper tab completion
        if hasattr(readline, 'set_completer_delims'):
            # Set delimiters to properly detect @ symbol
            readline.set_completer_delims(' \t\n;')
    except:
        pass

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

    # Initialize color support
    _supports_color = None

    @classmethod
    def _check_color_support(cls):
        if cls._supports_color is None:
            term = os.getenv('TERM', '').lower()
            colorterm = os.getenv('COLORTERM', '').lower()

            if colorterm in ['truecolor', '24bit']:
                cls._supports_color = True
            elif 'color' in term or term in ['xterm-256color', 'screen-256color']:
                cls._supports_color = True
            elif os.isatty(1):
                cls._supports_color = True
            else:
                cls._supports_color = False

            # Initialize color codes
            if cls._supports_color:
                cls.RESET = '\033[0m'
                cls.BOLD = '\033[1m'
                cls.DIM = '\033[2m'
                cls.RED = '\033[31m'
                cls.GREEN = '\033[32m'
                cls.YELLOW = '\033[33m'
                cls.BLUE = '\033[34m'
                cls.MAGENTA = '\033[35m'
                cls.CYAN = '\033[36m'
                cls.WHITE = '\033[37m'
                cls.BRIGHT_RED = '\033[91m'
                cls.BRIGHT_GREEN = '\033[92m'
                cls.BRIGHT_YELLOW = '\033[93m'
                cls.BRIGHT_BLUE = '\033[94m'
                cls.BRIGHT_MAGENTA = '\033[95m'
                cls.BRIGHT_CYAN = '\033[96m'
                cls.BRIGHT_WHITE = '\033[97m'
            else:
                cls.RESET = ''
                cls.BOLD = ''
                cls.DIM = ''
                cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ''
                cls.MAGENTA = cls.CYAN = cls.WHITE = ''
                cls.BRIGHT_RED = cls.BRIGHT_GREEN = cls.BRIGHT_YELLOW = ''
                cls.BRIGHT_BLUE = cls.BRIGHT_MAGENTA = cls.BRIGHT_CYAN = ''
                cls.BRIGHT_WHITE = ''

        return cls._supports_color

    @classmethod
    def colorize(cls, text, color):
        cls._check_color_support()
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def success(cls, text):
        return cls.colorize(text, cls.BRIGHT_GREEN)

    @classmethod
    def error(cls, text):
        return cls.colorize(text, cls.BRIGHT_RED)

    @classmethod
    def warning(cls, text):
        return cls.colorize(text, cls.BRIGHT_YELLOW)

    @classmethod
    def info(cls, text):
        return cls.colorize(text, cls.BRIGHT_BLUE)

    @classmethod
    def cyan(cls, text):
        return cls.colorize(text, cls.CYAN)

    @classmethod
    def magenta(cls, text):
        return cls.colorize(text, cls.MAGENTA)

    @classmethod
    def prompt(cls, text):
        return cls.colorize(text, cls.BOLD + cls.CYAN)

    @classmethod
    def header(cls, text):
        return cls.colorize(text, cls.BOLD + cls.BRIGHT_BLUE)

# Initialize colors on import
Colors._check_color_support()


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

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a new directory."""
        try:
            full_path = self._resolve_path(path)
            full_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"error": str(e)}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file."""
        try:
            full_path = self._resolve_path(path)
            if not full_path.is_file():
                return {"error": f"File not found: {path}"}

            full_path.unlink()
            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"error": str(e)}

    def delete_directory(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete a directory."""
        try:
            full_path = self._resolve_path(path)
            if not full_path.is_dir():
                return {"error": f"Directory not found: {path}"}

            if recursive:
                import shutil
                shutil.rmtree(full_path)
            else:
                full_path.rmdir()
            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"error": str(e)}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file."""
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)

            if not src_path.is_file():
                return {"error": f"Source file not found: {source}"}

            import shutil
            shutil.copy2(src_path, dst_path)
            return {"success": True, "source": str(src_path), "destination": str(dst_path)}
        except Exception as e:
            return {"error": str(e)}

    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move/rename a file."""
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)

            if not src_path.exists():
                return {"error": f"Source not found: {source}"}

            src_path.rename(dst_path)
            return {"success": True, "source": str(src_path), "destination": str(dst_path)}
        except Exception as e:
            return {"error": str(e)}

    def file_exists(self, path: str) -> Dict[str, Any]:
        """Check if file/directory exists."""
        try:
            full_path = self._resolve_path(path)
            return {"exists": full_path.exists(), "type": "file" if full_path.is_file() else "directory" if full_path.is_dir() else "unknown"}
        except Exception as e:
            return {"error": str(e)}

    def search_in_files(self, pattern: str, path: str = ".", file_types: List[str] = None) -> Dict[str, Any]:
        """Search for pattern in files."""
        try:
            import fnmatch

            full_path = self._resolve_path(path)
            if file_types is None:
                file_types = ['py', 'js', 'ts', 'java', 'cpp', 'c', 'h', 'html', 'css', 'md', 'txt']

            results = []
            pattern_re = re.compile(pattern, re.IGNORECASE)

            for root, dirs, files in os.walk(full_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if any(file.endswith(f'.{ext}') for ext in file_types):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if pattern_re.search(line):
                                        relative_path = file_path.relative_to(self.work_dir)
                                        results.append({
                                            "file": str(relative_path),
                                            "line": line_num,
                                            "content": line.strip()
                                        })
                        except:
                            continue

            return {"matches": results, "total": len(results)}
        except Exception as e:
            return {"error": str(e)}

    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file information."""
        try:
            full_path = self._resolve_path(path)
            if not full_path.exists():
                return {"error": f"Path not found: {path}"}

            stat = full_path.stat()
            return {
                "name": full_path.name,
                "path": str(full_path),
                "type": "directory" if full_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
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


class ShellOperations:
    """Handles shell command execution safely."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir).resolve()

    def run_command(self, command: str, capture_output: bool = True) -> Dict[str, Any]:
        """Run a shell command."""
        try:
            import shlex

            # Change to work directory
            cwd = str(self.work_dir)

            if capture_output:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=30
                )
                return {
                    "success": result.returncode == 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                # Run without capturing (interactive)
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
                process.wait()
                return {
                    "success": process.returncode == 0,
                    "exit_code": process.returncode
                }

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out after 30 seconds"}
        except Exception as e:
            return {"error": str(e)}


class GitOperations:
    """Handles git operations."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir).resolve()
        self.shell_ops = ShellOperations(work_dir)

    def _is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        git_dir = self.work_dir / '.git'
        return git_dir.exists() or git_dir.is_dir()

    def git_status(self) -> Dict[str, Any]:
        """Get git status."""
        if not self._is_git_repo():
            return {"error": "Not a git repository"}

        result = self.shell_ops.run_command("git status --porcelain", capture_output=True)
        if not result["success"]:
            return {"error": result["stderr"]}

        # Parse porcelain output
        files = []
        for line in result["stdout"].splitlines():
            if line:
                status = line[:2]
                path = line[3:]
                files.append({
                    "status": status,
                    "staged": status[0] if status[0] != " " else None,
                    "unstaged": status[1] if status[1] != " " else None,
                    "path": path
                })

        return {
            "success": True,
            "branch": self._get_current_branch(),
            "files": files,
            "clean": len(files) == 0
        }

    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            result = self.shell_ops.run_command("git rev-parse --abbrev-ref HEAD", capture_output=True)
            if result["success"]:
                return result["stdout"].strip()
            return "unknown"
        except:
            return "unknown"

    def git_diff(self, file_path: str = None, staged: bool = False) -> Dict[str, Any]:
        """Get git diff."""
        if not self._is_git_repo():
            return {"error": "Not a git repository"}

        cmd = "git diff"
        if staged:
            cmd = "git diff --staged"
        if file_path:
            cmd += f" {file_path}"

        result = self.shell_ops.run_command(cmd, capture_output=True)
        if not result["success"]:
            return {"error": result["stderr"]}

        return {"success": True, "diff": result["stdout"]}

    def git_log(self, limit: int = 10, file_path: str = None) -> Dict[str, Any]:
        """Get git log."""
        if not self._is_git_repo():
            return {"error": "Not a git repository"}

        cmd = f"git log --oneline -n {limit} --format=\"%H|%h|%s|%an|%ad\" --date=iso"
        if file_path:
            cmd += f" -- {file_path}"

        result = self.shell_ops.run_command(cmd, capture_output=True)
        if not result["success"]:
            return {"error": result["stderr"]}

        commits = []
        for line in result["stdout"].splitlines():
            if line:
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "short_hash": parts[1],
                        "message": parts[2],
                        "author": parts[3],
                        "date": parts[4]
                    })

        return {"success": True, "commits": commits}

    def git_add(self, files: List[str] = None) -> Dict[str, Any]:
        """Add files to git staging."""
        if not self._is_git_repo():
            return {"error": "Not a git repository"}

        if not files:
            cmd = "git add ."
        else:
            cmd = f"git add {' '.join(files)}"

        result = self.shell_ops.run_command(cmd, capture_output=True)
        return {"success": result["success"], "message": result["stderr"] or "Files staged successfully"}

    def git_commit(self, message: str) -> Dict[str, Any]:
        """Create a git commit."""
        if not self._is_git_repo():
            return {"error": "Not a git repository"}

        cmd = f'git commit -m "{message}"'
        result = self.shell_ops.run_command(cmd, capture_output=True)
        if not result["success"]:
            return {"error": result["stderr"]}

        return {"success": True, "message": "Commit created successfully"}


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
        self.shell_ops = ShellOperations()
        self.git_ops = GitOperations()
        self.client = ZAIClient()
        self.running = False

        # For autocomplete
        self._completion_matches = []

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
- create_directory: {"path": "folder/name"}
- delete_file: {"path": "file/to/delete"}
- delete_directory: {"path": "folder/to/delete", "recursive": false}
- copy_file: {"source": "from/path", "destination": "to/path"}
- move_file: {"source": "old/path", "destination": "new/path"}
- file_exists: {"path": "check/this/file"}
- get_file_info: {"path": "file/path"}
- search_in_files: {"pattern": "regex", "path": ".", "file_types": ["py", "js", "ts"]}
- run_command: {"command": "shell command", "capture_output": true}
- git_status: {}
- git_diff: {"file_path": "file.py", "staged": false}
- git_log: {"limit": 10, "file": "file.py"}
- git_add: {"files": ["file1.py", "file2.py"]}
- git_commit: {"message": "Commit message"}

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
        """Get input from user with autocomplete support."""
        try:
            # If readline is available, use enhanced input
            if HAVE_READLINE:
                # Store original settings
                old_completer = readline.get_completer()
                old_delims = readline.get_completer_delims() if hasattr(readline, 'get_completer_delims') else ' \t\n"\'`@$><=;|&{('

                # Set @ as part of word so we get the whole @filename as 'text'
                readline.set_completer_delims(' \t\n')

                # Custom completer for @filename
                def completer(text, state):
                    # Only complete if the text starts with @ or contains @
                    if '@' in text:
                        # Find the position of @
                        at_pos = text.find('@')

                        if at_pos == 0:
                            # Text starts with @, get the filename part
                            partial = text[1:]  # Remove @
                            prefix = '@'
                        else:
                            # @ is in the middle, extract filename part after @
                            partial = text[at_pos + 1:]
                            prefix = text[:at_pos + 1]  # Include the @

                        # Get matching files
                        matches = []
                        all_files = self._get_project_files()

                        # Case-sensitive match first
                        for file in all_files:
                            if file.startswith(partial):
                                # Always prefix with @
                                matches.append(prefix + file)

                        # If no case-sensitive matches, try case-insensitive
                        if not matches and partial:
                            partial_lower = partial.lower()
                            for file in all_files:
                                if file.lower().startswith(partial_lower):
                                    matches.append(prefix + file)

                        # Return the match for this state
                        if state < len(matches):
                            return matches[state]

                    # Not a @filename completion
                    return None

                # Setup completion
                readline.set_completer(completer)
                readline.parse_and_bind("tab: complete")

                # Configure readline for proper line wrapping
                try:
                    # Turn off horizontal scrolling to enable line wrapping
                    readline.parse_and_bind("set horizontal-scroll-mode Off")
                    # Enable bell (optional)
                    readline.parse_and_bind("set bell-style audible")
                    # Set preferred editing mode
                    readline.parse_and_bind("set editing-mode emacs")

                    # Additional settings for better terminal compatibility
                    # Check for COMUX_READLINE_SETTINGS environment variable
                    custom_settings = os.environ.get('COMUX_READLINE_SETTINGS', '')
                    if custom_settings:
                        for setting in custom_settings.split(','):
                            setting = setting.strip()
                            if setting:
                                readline.parse_and_bind(setting)
                except:
                    pass  # If not supported, continue

                # Handle prompt with proper color code support for readline
                # The issue is that readline doesn't know about ANSI color codes
                # So we need to wrap non-printing characters in \1 and \2
                if Colors._check_color_support():
                    # Build prompt with readline-aware color codes
                    # \1 and \2 tell readline about non-printing characters
                    prompt_parts = [
                        '\1', Colors.BOLD + Colors.CYAN, '\2',  # Start colors
                        '>>> ',                                # Visible text
                        '\1', Colors.RESET, '\2'              # Reset colors
                    ]
                    prompt_str = ''.join(prompt_parts)
                else:
                    # No color support, use plain prompt
                    prompt_str = ">>> "

                # Get input using the properly formatted prompt
                line = input(prompt_str)

                # Restore original settings
                readline.set_completer(old_completer)
                if hasattr(readline, 'set_completer_delims'):
                    readline.set_completer_delims(old_delims)

                return line
            else:
                # Fallback to regular input
                # For terminals without readline, use simple prompt
                line = input(">>> ")
                return line
        except EOFError:
            return "exit"

    
    def _get_project_files(self) -> List[str]:
        """Get all files in the project, excluding common ignore patterns."""
        files = []
        ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', '.venv',
                      'dist', 'build', '.pytest_cache', '.tox', 'coverage'}

        try:
            for root, dirs, filenames in os.walk('.'):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

                for filename in filenames:
                    if not filename.startswith('.'):
                        # Get relative path
                        full_path = Path(root) / filename
                        relative_path = str(full_path.relative_to(Path('.')))

                        # Convert to forward slashes for consistency
                        relative_path = relative_path.replace('\\', '/')

                        files.append(relative_path)
        except Exception as e:
            # If there's an error, return empty list rather than crashing
            pass

        return sorted(files, key=str.lower)

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

            # File operations
            if tool == 'read_file':
                result = self.file_ops.read_file(args['path'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"File content:\n{result['content']}"

            elif tool == 'write_file':
                result = self.file_ops.write_file(args['path'], args['content'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ File written: {result['path']}"

            elif tool == 'patch_file':
                result = self.file_ops.patch_file(args['path'], args['patch'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ File patched: {result['path']}" if result.get('success') else result.get('message', 'Patch failed')

            elif tool == 'list_files':
                result = self.file_ops.list_files(args.get('path', '.'))
                if 'error' in result:
                    return f"Error: {result['error']}"

                output = []
                for item in result['files']:
                    icon = "📁" if item['type'] == 'directory' else "📄"
                    size = f" ({item['size']} bytes)" if item['type'] == 'file' else ""
                    output.append(f"{icon} {item['name']}{size}")
                return '\n'.join(output)

            elif tool == 'create_directory':
                result = self.file_ops.create_directory(args['path'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ Directory created: {result['path']}"

            elif tool == 'delete_file':
                result = self.file_ops.delete_file(args['path'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ File deleted: {result['path']}"

            elif tool == 'delete_directory':
                recursive = args.get('recursive', False)
                result = self.file_ops.delete_directory(args['path'], recursive)
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ Directory deleted: {result['path']}"

            elif tool == 'copy_file':
                result = self.file_ops.copy_file(args['source'], args['destination'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ File copied from {result['source']} to {result['destination']}"

            elif tool == 'move_file':
                result = self.file_ops.move_file(args['source'], args['destination'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ File moved from {result['source']} to {result['destination']}"

            elif tool == 'file_exists':
                result = self.file_ops.file_exists(args['path'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                status = "✓ exists" if result['exists'] else "✗ does not exist"
                return f"Path {args['path']} {status} (type: {result['type']})"

            elif tool == 'get_file_info':
                result = self.file_ops.get_file_info(args['path'])
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"""File Info:
Name: {result['name']}
Path: {result['path']}
Type: {result['type']}
Size: {result['size']} bytes
Modified: {result['modified']}
Permissions: {result['permissions']}"""

            elif tool == 'search_in_files':
                pattern = args['pattern']
                path = args.get('path', '.')
                file_types = args.get('file_types', None)
                result = self.file_ops.search_in_files(pattern, path, file_types)
                if 'error' in result:
                    return f"Error: {result['error']}"

                if result['total'] == 0:
                    return f"No matches found for pattern: {pattern}"

                output = [f"Found {result['total']} matches for pattern: {pattern}"]
                for match in result['matches'][:20]:  # Limit to 20 results
                    output.append(f"  {match['file']}:{match['line']} - {match['content']}")

                if result['total'] > 20:
                    output.append(f"  ... and {result['total'] - 20} more matches")

                return '\n'.join(output)

            # Shell operations
            elif tool == 'run_command':
                command = args['command']
                capture = args.get('capture_output', True)
                result = self.shell_ops.run_command(command, capture)

                if 'error' in result:
                    return f"Error: {result['error']}"

                if capture:
                    output = []
                    output.append(f"Command: {command}")
                    output.append(f"Exit code: {result['exit_code']}")
                    if result['stdout']:
                        output.append(f"Output:\n{result['stdout']}")
                    if result['stderr']:
                        output.append(f"Error:\n{result['stderr']}")
                    return '\n'.join(output)
                else:
                    return f"✓ Command executed: {command}"

            # Git operations
            elif tool == 'git_status':
                result = self.git_ops.git_status()
                if 'error' in result:
                    return f"Error: {result['error']}"

                output = [f"Git Status (branch: {result['branch']})"]
                if result['clean']:
                    output.append("  Working directory clean")
                else:
                    for file in result['files']:
                        status_icons = {
                            'A': '🟢',  # Added
                            'M': '🟡',  # Modified
                            'D': '🔴',  # Deleted
                            'R': '🔄',  # Renamed
                            'C': '🆕',  # Copied
                            '??': '❓',  # Untracked
                            '!!': '🚫',  # Ignored
                        }
                        staged = status_icons.get(file['staged'], '  ') if file['staged'] else '  '
                        unstaged = status_icons.get(file['unstaged'], '  ') if file['unstaged'] else '  '
                        output.append(f"  {staged}{unstaged} {file['path']}")

                return '\n'.join(output)

            elif tool == 'git_diff':
                file_path = args.get('file_path')
                staged = args.get('staged', False)
                result = self.git_ops.git_diff(file_path, staged)
                if 'error' in result:
                    return f"Error: {result['error']}"

                if not result['diff']:
                    return "No differences found"

                return result['diff']

            elif tool == 'git_log':
                limit = args.get('limit', 10)
                file_path = args.get('file')
                result = self.git_ops.git_log(limit, file_path)
                if 'error' in result:
                    return f"Error: {result['error']}"

                output = []
                for commit in result['commits']:
                    output.append(f"  {commit['short_hash']} - {commit['message']} ({commit['author']}, {commit['date'][:10]})")

                return '\n'.join(output)

            elif tool == 'git_add':
                files = args.get('files')
                result = self.git_ops.git_add(files)
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ {result['message']}"

            elif tool == 'git_commit':
                message = args['message']
                result = self.git_ops.git_commit(message)
                if 'error' in result:
                    return f"Error: {result['error']}"
                return f"✓ {result['message']}"

            else:
                return f"❌ Unknown tool: {tool}"

        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON in tool call: {e}"
        except KeyError as e:
            return f"❌ Missing required argument: {e}"
        except Exception as e:
            return f"❌ Tool execution error: {e}"


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