import subprocess
import sys
import os
import tempfile
import shutil
import time
from utils import get_os_info

def check_update(auto_mode=False):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cache_file = os.path.join(base_dir, '.last_update_check')
        skip_file = os.path.join(base_dir, '.skipped_update')
        
        if auto_mode:
            if os.path.exists(cache_file):
                if time.time() - os.path.getmtime(cache_file) < 12 * 3600:
                    return
        
        os_info = get_os_info()
        if not auto_mode: print(f"[*] OS Detected: {os_info}")
        print("[*] Checking for new updates from GitHub...")
        
        res = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
        if res.returncode != 0:
            if not auto_mode: print("[!] Not a git repository. Cannot check for updates.")
            return
            
        local_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True, check=True, cwd=base_dir).stdout.strip()
        
        remote_output = subprocess.run(['git', 'ls-remote', 'origin', '-h', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5, cwd=base_dir)
        if remote_output.returncode != 0:
            if not auto_mode: print(f"[!] Error checking remote updates: {remote_output.stderr.strip()}", file=sys.stderr)
            return
            
        remote_hash = remote_output.stdout.split()[0]
        
        if local_hash != remote_hash:
            if auto_mode and os.path.exists(skip_file):
                with open(skip_file, 'r') as f:
                    skipped_hash = f.read().strip()
                if skipped_hash == remote_hash:
                    # Chặn hỏi lại vì người dùng đã skip mã này
                    return
            
            if auto_mode: print(f"[*] OS Detected: {os_info}")
            print("\n" + "="*70)
            print("[!] A new update is available for RAC-Compiler!")
            
            status_output = subprocess.run(['git', 'status', '--porcelain'], stdout=subprocess.PIPE, text=True, cwd=base_dir).stdout
            has_uncommitted = bool(status_output.strip())
            
            if has_uncommitted:
                print("\n[!] WARNING: You have uncommitted local changes in:")
                for line in status_output.splitlines():
                    print("  " + line)
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
                
                print("Backing up rsc_ropchain/ and asm_ropchain/...")
                
                backup_dir = tempfile.mkdtemp()
                protected_dirs = ['rsc_ropchain', 'asm_ropchain']
                for d in protected_dirs:
                    d_path = os.path.join(base_dir, d)
                    if os.path.exists(d_path):
                        shutil.copytree(d_path, os.path.join(backup_dir, d))
                
                if force_overwrite:
                    print("Fetching and forcefully overwriting local code...")
                    subprocess.run(['git', 'fetch', 'origin'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
                    pull_res = subprocess.run(['git', 'reset', '--hard', remote_hash], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=base_dir)
                    if pull_res.returncode != 0:
                        print(f"[!] Update failed:\n{pull_res.stderr}")
                        sys.exit(1)
                else:
                    print("Pulling latest updates (git pull)...")
                    has_stash = False
                    if has_uncommitted:
                        subprocess.run(['git', 'stash', 'push', '-m', 'RAC-Compiler Auto Stash Before Update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
                        has_stash = True
                    
                    pull_res = subprocess.run(['git', 'pull', '--rebase'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=base_dir)
                    
                    if pull_res.returncode != 0:
                        print(f"[!] Update failed:\n{pull_res.stderr}")
                        subprocess.run(['git', 'rebase', '--abort'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
                        if has_stash:
                            subprocess.run(['git', 'stash', 'pop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base_dir)
                        print("[!] Cannot auto-update due to severe conflicts. Your local code has been restored.")
                        sys.exit(1)
                    else:
                        if has_stash:
                            pop_res = subprocess.run(['git', 'stash', 'pop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=base_dir)
                            if pop_res.returncode != 0:
                                print("[!] Warning: Conflicts occurred while restoring your local changes. Please check 'git status'.")
                                
                print("Restoring your preserved files in rsc_ropchain/ and asm_ropchain/...")
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
                                
                if os.path.exists(skip_file): os.remove(skip_file)
                if os.path.exists(cache_file): os.remove(cache_file)
                print("\nUpdate successful! Please run the tool again to apply the new version.")
                sys.exit(2)
                
            else:
                if auto_mode:
                    with open(skip_file, 'w') as f: f.write(remote_hash)
                    with open(cache_file, 'w') as f: f.write(str(time.time()))
                print("Continuing with the current version...\n")
                
        else:
            if not auto_mode:
                print("\n" + "="*70)
                print("[*] You are already on the latest version!")
                print("="*70 + "\n")
            if auto_mode:
                with open(cache_file, 'w') as f: f.write(str(time.time()))
                
    except Exception as e:
        print(f"[!] Unexpected error while running update checker: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_update(auto_mode=False)
