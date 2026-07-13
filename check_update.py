import subprocess
import sys
import os
import tempfile
import shutil
import time
from libcompiler.utils import get_os_info

def get_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, '.config')
    config = {}
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    config[k] = v
    return config, config_file

def save_config(config, config_file):
    with open(config_file, 'w') as f:
        for k, v in config.items():
            f.write(f"{k}={v}\n")

def check_update_available(auto_mode=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config, config_file = get_config()
    last_check = config.get("UPDATE_LAST_CHECK")
    skipped_hash = config.get("UPDATE_SKIP_HASH")
    
    if auto_mode and last_check:
        try:
            if time.time() - float(last_check) < 12 * 3600:
                return False, None, False
        except ValueError:
            pass
            
    res = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
    if res.returncode != 0:
        return False, None, False
        
    local_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True, check=True, cwd=base_dir).stdout.strip()
    
    remote_output = subprocess.run(['git', 'ls-remote', 'origin', '-h', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5, cwd=base_dir)
    if remote_output.returncode != 0:
        return False, None, False
        
    remote_hash = remote_output.stdout.split()[0]
    
    if local_hash != remote_hash:
        if auto_mode and skipped_hash == remote_hash:
            return False, None, False
            
        status_output = subprocess.run(['git', 'status', '--porcelain'], stdout=subprocess.PIPE, text=True, cwd=base_dir).stdout
        has_uncommitted = bool(status_output.strip())
        return True, remote_hash, has_uncommitted
        
    if auto_mode:
        config["UPDATE_LAST_CHECK"] = str(time.time())
        save_config(config, config_file)
    return False, None, False

def perform_update(remote_hash, force_overwrite, log_callback=None):
    if log_callback is None:
        log_callback = print
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config, config_file = get_config()
    
    log_callback("Backing up rsc_ropchain/ and asm_ropchain/...")
    backup_dir = tempfile.mkdtemp()
    protected_dirs = ['rsc_ropchain', 'asm_ropchain']
    for d in protected_dirs:
        d_path = os.path.join(base_dir, d)
        if os.path.exists(d_path):
            shutil.copytree(d_path, os.path.join(backup_dir, d))
            
    status_output = subprocess.run(['git', 'status', '--porcelain'], stdout=subprocess.PIPE, text=True, cwd=base_dir).stdout
    has_uncommitted = bool(status_output.strip())
    
    try:
        if force_overwrite:
            log_callback("Fetching and forcefully overwriting local code...")
            subprocess.run(['git', 'fetch', 'origin'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
            pull_res = subprocess.run(['git', 'reset', '--hard', remote_hash], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=base_dir)
            if pull_res.returncode != 0:
                raise Exception(f"Update failed:\n{pull_res.stderr}")
        else:
            log_callback("Pulling latest updates (git pull)...")
            has_stash = False
            if has_uncommitted:
                subprocess.run(['git', 'stash', 'push', '-m', 'RAC-Compiler Auto Stash Before Update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
                has_stash = True
            
            pull_res = subprocess.run(['git', 'pull', '--rebase'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=base_dir)
            
            if pull_res.returncode != 0:
                subprocess.run(['git', 'rebase', '--abort'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
                if has_stash:
                    subprocess.run(['git', 'stash', 'pop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
                raise Exception(f"Cannot auto-update due to severe conflicts.\n{pull_res.stderr}")
            else:
                if has_stash:
                    pop_res = subprocess.run(['git', 'stash', 'pop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=base_dir)
                    if pop_res.returncode != 0:
                        log_callback("[!] Warning: Conflicts occurred while restoring your local changes. Please check 'git status'.")
                        
        log_callback("Restoring your preserved files in rsc_ropchain/ and asm_ropchain/...")
        for d in protected_dirs:
            backup_d = os.path.join(backup_dir, d)
            if os.path.exists(backup_d):
                for root, _, files in os.walk(backup_d):
                    for file in files:
                        src = os.path.join(root, file)
                        rel_path = os.path.relpath(src, backup_dir)
                        dest = os.path.join(base_dir, rel_path)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        shutil.copy2(src, dest)
                        
        if "UPDATE_SKIP_HASH" in config: del config["UPDATE_SKIP_HASH"]
        if "UPDATE_LAST_CHECK" in config: del config["UPDATE_LAST_CHECK"]
        save_config(config, config_file)
        log_callback("Update successful!")
        return True
    except Exception as e:
        log_callback(str(e))
        return False

def check_update(auto_mode=False):
    try:
        os_info = get_os_info()
        if not auto_mode: print(f"[*] OS Detected: {os_info}")
        print("[*] Checking for new updates from GitHub...")
        
        is_available, remote_hash, has_uncommitted = check_update_available(auto_mode)
        
        if is_available:
            if auto_mode: print(f"[*] OS Detected: {os_info}")
            print("\n" + "="*70)
            print("[!] A new update is available for RAC-Compiler!")
            if has_uncommitted:
                print("\n[!] WARNING: You have uncommitted local changes.")
                print("Your files in rsc_ropchain/ and asm_ropchain/ will be safely preserved,")
                print("and ONLY NEW FILES from the update will be added to these directories.")
            print("="*70 + "\n")
            
            response = input("Would you like to update now? (y/n): ").strip().lower()
            if response == 'y':
                force_overwrite = False
                if has_uncommitted:
                    print("\nSince you have local modifications, updating might cause conflicts.")
                    ow_resp = input("Do you want to forcefully overwrite your local code modifications? (Files in rsc_ropchain/ and asm_ropchain/ will still be preserved) (y/n): ").strip().lower()
                    if ow_resp == 'y':
                        force_overwrite = True
                        
                success = perform_update(remote_hash, force_overwrite)
                if success:
                    print("\nUpdate successful! Please run the tool again to apply the new version.")
                    sys.exit(2)
                else:
                    sys.exit(1)
            else:
                if auto_mode:
                    config, config_file = get_config()
                    config["UPDATE_SKIP_HASH"] = remote_hash
                    config["UPDATE_LAST_CHECK"] = str(time.time())
                    save_config(config, config_file)
                print("Continuing with the current version...\n")
        else:
            if not auto_mode:
                print("\n" + "="*70)
                print("[*] You are already on the latest version!")
                print("="*70 + "\n")
    except Exception as e:
        print(f"[!] Unexpected error while running update checker: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_update(auto_mode=False)
