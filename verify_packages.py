import sys
import os
from pathlib import Path
import importlib.metadata

REQUIREMENTS_FILE = 'requirements.txt'

def normalize_name(name):
    return name.lower().replace('-', '_')

def parse_requirements_file(path):
    """Parse requirements.txt into a dictionary {package: version}"""
    requirements = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '==' in line:
                pkg, ver = line.split('==')
                requirements[normalize_name(pkg)] = ver
            else:
                requirements[normalize_name(line)] = None
    return requirements

def get_installed_packages():
    """Get installed packages in {package: version} format"""
    installed = {}
    for dist in importlib.metadata.distributions():
        installed[normalize_name(dist.metadata['Name'])] = dist.version
    return installed

def compare(installed, required):
    missing = {}
    mismatched = {}
    for pkg, req_ver in required.items():
        inst_ver = installed.get(pkg)
        if inst_ver is None:
            missing[pkg] = req_ver
        elif req_ver and inst_ver != req_ver:
            mismatched[pkg] = (req_ver, inst_ver)

    extra = {pkg: ver for pkg, ver in installed.items() if pkg not in required}
    return missing, mismatched, extra

def color(text, style=''):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    return f"{colors.get(style, '')}{text}{colors['end'] if style else ''}"

if __name__ == "__main__":
    if not Path(REQUIREMENTS_FILE).exists():
        print(color(f"{REQUIREMENTS_FILE} not found.", 'red'))
        sys.exit(1)

    required = parse_requirements_file(REQUIREMENTS_FILE)
    installed = get_installed_packages()
    missing, mismatched, extra = compare(installed, required)

    print(color("\n🔍 Comparison results:\n", 'blue'))

    if missing:
        print(color("❌ Missing packages:", 'red'))
        for pkg, ver in missing.items():
            print(f"  - {pkg}=={ver if ver else '*'}")
        print("\nSuggested install command:")
        pkgs = ' '.join([f"{k}=={v}" if v else k for k, v in missing.items()])
        print(color(f"  pip install {pkgs}\n", 'yellow'))
    else:
        print(color("✅ No missing packages\n", 'green'))

    if mismatched:
        print(color("⚠️ Version mismatches:", 'yellow'))
        for pkg, (req, inst) in mismatched.items():
            print(f"  - {pkg}: required {req}, installed {inst}")
        print("\nSuggested install command:")
        pkgs = ' '.join([f"{k}=={v[0]}" for k, v in mismatched.items()])
        print(color(f"  pip install --upgrade {pkgs}\n", 'yellow'))
    else:
        print(color("✅ No version mismatches\n", 'green'))

    if extra:
        print(color("🧹 Extra packages (not in requirements.txt):", 'blue'))
        for pkg, ver in extra.items():
            print(f"  - {pkg}=={ver}")
        print("\nSuggested uninstall command:")
        pkgs = ' '.join(extra.keys())
        print(color(f"  pip uninstall -y {pkgs}\n", 'yellow'))
    else:
        print(color("✅ No extra packages\n", 'green'))
