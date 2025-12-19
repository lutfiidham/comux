# Comux AI Tools Reference

Comux menyediakan berbagai tools AI untuk membantu tugas coding Anda. Berikut adalah daftar lengkap tools yang tersedia:

## 📁 **File System Operations**

### `read_file`
Membaca konten file.
```json
{
  "tool": "read_file",
  "args": {
    "path": "relative/path/to/file"
  }
}
```

### `write_file`
Menulis konten ke file (akan menimpa jika file sudah ada).
```json
{
  "tool": "write_file",
  "args": {
    "path": "relative/path/to/file",
    "content": "complete file content"
  }
}
```

### `patch_file`
Mengaplikasikan unified diff patch ke file.
```json
{
  "tool": "patch_file",
  "args": {
    "path": "relative/path/to/file",
    "patch": "unified diff format"
  }
}
```

### `list_files`
Menampilkan daftar file dan direktori.
```json
{
  "tool": "list_files",
  "args": {
    "path": "."  // optional, default: "."
  }
}
```

### `create_directory`
Membuat direktori baru.
```json
{
  "tool": "create_directory",
  "args": {
    "path": "folder/name"
  }
}
```

### `delete_file`
Menghapus file.
```json
{
  "tool": "delete_file",
  "args": {
    "path": "file/to/delete"
  }
}
```

### `delete_directory`
Menghapus direktori.
```json
{
  "tool": "delete_directory",
  "args": {
    "path": "folder/to/delete",
    "recursive": false  // optional, default: false
  }
}
```

### `copy_file`
Menyalin file.
```json
{
  "tool": "copy_file",
  "args": {
    "source": "from/path",
    "destination": "to/path"
  }
}
```

### `move_file`
Memindahkan/mengganti nama file.
```json
{
  "tool": "move_file",
  "args": {
    "source": "old/path",
    "destination": "new/path"
  }
}
```

### `file_exists`
Memeriksa apakah file/direktori ada.
```json
{
  "tool": "file_exists",
  "args": {
    "path": "check/this/file"
  }
}
```

### `get_file_info`
Mendapatkan informasi detail tentang file.
```json
{
  "tool": "get_file_info",
  "args": {
    "path": "file/path"
  }
}
```

## 🔍 **Code Search & Analysis**

### `search_in_files`
Mencari pola dalam multiple files.
```json
{
  "tool": "search_in_files",
  "args": {
    "pattern": "regex or text",
    "path": ".",  // optional, default: "."
    "file_types": ["py", "js", "ts"]  // optional
  }
}
```

## 🏃‍♂️ **Shell Operations**

### `run_command`
Menjalankan perintah shell.
```json
{
  "tool": "run_command",
  "args": {
    "command": "shell command",
    "capture_output": true  // optional, default: true
  }
}
```

## 🔄 **Git Operations**

### `git_status`
Melihat status git repository.
```json
{
  "tool": "git_status",
  "args": {}
}
```

### `git_diff`
Melihat perbedaan file.
```json
{
  "tool": "git_diff",
  "args": {
    "file_path": "file.py",  // optional
    "staged": false  // optional, default: false
  }
}
```

### `git_log`
Melihat commit history.
```json
{
  "tool": "git_log",
  "args": {
    "limit": 10,  // optional, default: 10
    "file": "file.py"  // optional
  }
}
```

### `git_add`
Menambahkan file ke staging area.
```json
{
  "tool": "git_add",
  "args": {
    "files": ["file1.py", "file2.py"]  // optional, default: all files
  }
}
```

### `git_commit`
Membuat commit.
```json
{
  "tool": "git_commit",
  "args": {
    "message": "Commit message"
  }
}
```

### File Reference dengan @ Symbol

Anda bisa mereferensikan file dengan menggunakan `@filename`:
```json
{
  "tool": "read_file",
  "args": {
    "path": "@comux.py"
  }
}
```

**Autocomplete di Comux:**
```bash
>>> Baca @RE[TAB]         # → @README.md
>>> Edit @com[TAB]        # → @comux.py
>>> Lihat @sr[TAB]        # → @src/ (jika ada folder src)
>>> Cari @[TAB]           # Menampilkan semua file
```

**Fitur Autocomplete:**
- **Case-sensitive**: `@RE` → `@README.md`
- **Case-insensitive**: `@re` → `@README.md` (fallback)
- **Subdirectories**: `@src/mai[TAB]` → `@src/main.py`
- **Multiple matches**: Tekan Tab berulang untuk cycle melalui options

## 💡 **Contoh Penggunaan**

### Membuat project baru
```
User: Buatkan saya struktur project Node.js baru

AI: {
  "tool": "create_directory",
  "args": {
    "path": "my-node-app"
  }
}

AI: {
  "tool": "write_file",
  "args": {
    "path": "my-node-app/package.json",
    "content": "{\n  \"name\": \"my-node-app\",\n  \"version\": \"1.0.0\",\n  \"main\": \"index.js\"\n}"
  }
}
```

### Mencari kode
```
User: Cari fungsi yang menghandle API calls

AI: {
  "tool": "search_in_files",
  "args": {
    "pattern": "fetch|axios|request",
    "file_types": ["js", "ts"]
  }
}
```

### Git workflow
```
User: Commit perubahan terakhir

AI: {
  "tool": "git_status",
  "args": {}
}

AI: {
  "tool": "git_add",
  "args": {}
}

AI: {
  "tool": "git_commit",
  "args": {
    "message": "Add new features"
  }
}
```

## 📱 **Termux Support**

Comux memiliki dukungan penuh untuk Termux di Android:

### Autocomplete di Termux:
```bash
# Instalasi jika tidak ada
pkg install python
pip install gnureadline  # Jika autocomplete tidak bekerja

# Penggunaan
comux
>>> @fi[TAB]  # Akan menampilkan file yang cocok
```

### Requirements untuk Termux:
- Python >= 3.7
- `gnureadline` (opsional, untuk autocomplete)

## 📝 **Catatan Penting**

1. **Security**: Semua operasi file dibatasi dalam working directory saat ini
2. **Confirmation**: Operasi berisiko (seperti delete) akan meminta konfirmasi
3. **Path**: Gunakan relative path dari direktori saat ini
4. **JSON Format**: Respons harus JSON valid saat menggunakan tools
5. **Error Handling**: Semua error akan ditampilkan dengan pesan yang jelas
6. **Termux**: File paths menggunakan forward slash (/) untuk konsistensi lintas platform

## 🚀 **Tips & Best Practices**

- Gunakan `search_in_files` untuk explorasi codebase
- Gunakan `git_diff` sebelum melakukan patch
- Gunakan `list_files` untuk navigasi direktori
- Gunakan `run_command` untuk menjalankan build/test
- Gunakan `get_file_info` untuk melihat metadata file