import sys, subprocess, os, shutil

def find_python():
    for exe in ("python", "python3"):
        path = shutil.which(exe)
        if path:
            return path
    return None

def resolve_file(name):
    candidates = [
        os.path.join("rsc_ropchain", name),
        os.path.join("rsc_ropchain", name + ".rsc"),
        name,
        name + ".rsc"
    ]
    for path in candidates: 
        if os.path.exists(path): return path
    return None

if len(sys.argv) < 3:
    print("Usage: python rac.py <model> <name>")
    sys.exit(1)

name = sys.argv[2]
model = sys.argv[1]
file_path = resolve_file(name)

if file_path is None:
    print("File not found in:")
    print(" - rsc_ropchain/")
    print(" - current directory")
    sys.exit(1)

python_exe = find_python()
if find_python() is None:
    print("Python is not installed or not in PATH.")
    sys.exit(1)

subprocess.run([python_exe, "main.py", "-f", "hex", model, file_path])