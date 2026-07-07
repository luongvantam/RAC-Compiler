import subprocess
import sys
import os
import tempfile
import shutil

def check_update():
    try:
        # Check if we are in a git repository
        res = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            return
            
        # Get local commit hash
        local_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True, check=True).stdout.strip()
        
        # Get remote commit hash
        remote_output = subprocess.run(['git', 'ls-remote', 'origin', '-h', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if remote_output.returncode != 0:
            print(f"[!] Error checking remote updates: {remote_output.stderr.strip()}", file=sys.stderr)
            return
            
        remote_hash = remote_output.stdout.split()[0]
        
        if local_hash != remote_hash:
            print("\n" + "="*70)
            print("[!] A new update is available for RAC-Compiler!")
            
            # Check for uncommitted changes
            status_output = subprocess.run(['git', 'status', '--porcelain'], stdout=subprocess.PIPE, text=True).stdout
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
                
                # Backup rsc_ropchain and asm_ropchain
                backup_dir = tempfile.mkdtemp()
                protected_dirs = ['rsc_ropchain', 'asm_ropchain']
                for d in protected_dirs:
                    if os.path.exists(d):
                        shutil.copytree(d, os.path.join(backup_dir, d))
                
                if force_overwrite:
                    print("Fetching and forcefully overwriting local code...")
                    subprocess.run(['git', 'fetch', 'origin'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    pull_res = subprocess.run(['git', 'reset', '--hard', remote_hash], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if pull_res.returncode != 0:
                        print(f"[!] Update failed:\n{pull_res.stderr}")
                        sys.exit(1)
                else:
                    print("Pulling latest updates (git pull)...")
                    # Stash changes to avoid conflict
                    has_stash = False
                    if has_uncommitted:
                        subprocess.run(['git', 'stash', 'push', '-m', 'RAC-Compiler Auto Stash Before Update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        has_stash = True
                    
                    pull_res = subprocess.run(['git', 'pull', '--rebase'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    if pull_res.returncode != 0:
                        print(f"[!] Update failed:\n{pull_res.stderr}")
                        subprocess.run(['git', 'rebase', '--abort'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if has_stash:
                            subprocess.run(['git', 'stash', 'pop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        print("[!] Cannot auto-update due to severe conflicts. Your local code has been restored.")
                        sys.exit(1)
                    else:
                        if has_stash:
                            # Restore stashed changes
                            pop_res = subprocess.run(['git', 'stash', 'pop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            if pop_res.returncode != 0:
                                print("[!] Warning: Conflicts occurred while restoring your local changes. Please check 'git status'.")
                                
                # Restore protected directories from backup
                print("Restoring your preserved files in rsc_ropchain/ and asm_ropchain/...")
                for d in protected_dirs:
                    backup_d = os.path.join(backup_dir, d)
                    if os.path.exists(backup_d):
                        for root, _, files in os.walk(backup_d):
                            for file in files:
                                src = os.path.join(root, file)
                                rel_path = os.path.relpath(src, backup_dir)
                                os.makedirs(os.path.dirname(rel_path), exist_ok=True)
                                shutil.copy2(src, rel_path)
                                
                print("\nUpdate successful! Please run the tool again to apply the new version.")
                sys.exit(2)
                
            else:
                print("Continuing with the current version...\n")
                
    except Exception as e:
        print(f"[!] Unexpected error while running update checker: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_update()
