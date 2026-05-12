"""
Pre-deployment checklist and setup script for Streamlit Cloud.
Run this before pushing to GitHub and deploying to Streamlit Cloud.
"""

import os
import sys
from pathlib import Path
import subprocess


class DeploymentChecker:
    """Check project readiness for deployment."""
    
    def __init__(self, project_root='.'):
        self.root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.success_items = []
    
    def check_all(self):
        """Run all checks."""
        print("=" * 60)
        print("🚀 DEPLOYMENT READINESS CHECK")
        print("=" * 60)
        
        self.check_gitignore()
        self.check_requirements()
        self.check_main_files()
        self.check_streamlit_config()
        self.check_folder_structure()
        self.check_large_files()
        self.check_git_status()
        
        return self.print_results()
    
    def check_gitignore(self):
        """Check .gitignore configuration."""
        gitignore_path = self.root / '.gitignore'
        if not gitignore_path.exists():
            self.issues.append("❌ .gitignore file not found")
            return
        
        with open(gitignore_path) as f:
            content = f.read()
        
        required_patterns = [
            'data_warehouse/*.csv',
            '*.db',
            '__pycache__',
            'venv/',
        ]
        
        missing = [p for p in required_patterns if p not in content]
        if missing:
            self.warnings.append(f"⚠️  .gitignore missing patterns: {missing}")
        else:
            self.success_items.append("✅ .gitignore properly configured")
    
    def check_requirements(self):
        """Check requirements.txt."""
        req_path = self.root / 'requirements.txt'
        if not req_path.exists():
            self.issues.append("❌ requirements.txt not found")
            return
        
        required_packages = ['streamlit', 'pandas', 'plotly']
        with open(req_path) as f:
            content = f.read().lower()
        
        missing = [p for p in required_packages if p not in content]
        if missing:
            self.warnings.append(f"⚠️  Missing packages: {missing}")
        else:
            self.success_items.append("✅ requirements.txt contains all essential packages")
    
    def check_main_files(self):
        """Check main application files."""
        required_files = ['app.py', 'warehouse_ui.py', 'requirements.txt']
        
        for file in required_files:
            path = self.root / file
            if path.exists():
                self.success_items.append(f"✅ {file} exists")
            else:
                self.issues.append(f"❌ {file} is missing")
    
    def check_streamlit_config(self):
        """Check Streamlit configuration."""
        streamlit_dir = self.root / '.streamlit'
        if not streamlit_dir.exists():
            self.warnings.append("⚠️  .streamlit directory doesn't exist")
            streamlit_dir.mkdir()
            print("   ✓ Created .streamlit directory")
        
        config_path = streamlit_dir / 'config.toml'
        if config_path.exists():
            self.success_items.append("✅ .streamlit/config.toml exists")
        else:
            self.warnings.append("⚠️  .streamlit/config.toml not found")
        
        # Check secrets.toml is NOT in repo
        secrets_path = streamlit_dir / 'secrets.toml'
        secrets_gitignore = self.root / '.gitignore'
        if secrets_path.exists():
            with open(secrets_gitignore) as f:
                if '.streamlit/secrets.toml' not in f.read():
                    self.warnings.append("⚠️  secrets.toml might be tracked by git")
    
    def check_folder_structure(self):
        """Check required folder structure."""
        required_dirs = ['data_warehouse']
        
        for dir_name in required_dirs:
            dir_path = self.root / dir_name
            if not dir_path.exists():
                dir_path.mkdir()
                print(f"   ✓ Created {dir_name}/ directory")
            self.success_items.append(f"✅ {dir_name}/ directory exists")
            
            # Check .gitkeep
            gitkeep_path = dir_path / '.gitkeep'
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                print(f"   ✓ Created {dir_name}/.gitkeep")
    
    def check_large_files(self):
        """Check for large files that might exceed GitHub limits."""
        max_size_mb = 100
        large_files = []
        
        # Read .gitignore to exclude ignored files
        gitignore_patterns = []
        gitignore_path = self.root / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        gitignore_patterns.append(line)
        
        def is_ignored(filepath):
            """Check if file matches any gitignore pattern."""
            relative_path = str(filepath.relative_to(self.root))
            for pattern in gitignore_patterns:
                # Simple pattern matching (could be improved with fnmatch)
                if pattern in relative_path or relative_path.startswith(pattern.rstrip('/')):
                    return True
            return False
        
        for file_path in self.root.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size > max_size_mb * 1024 * 1024:
                if not is_ignored(file_path):
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    large_files.append((file_path.relative_to(self.root), size_mb))
        
        if large_files:
            for file, size in large_files:
                self.issues.append(f"❌ Large file ({size:.1f}MB): {file}")
        else:
            self.success_items.append("✅ No excessively large files found")
    
    def check_git_status(self):
        """Check git status."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                if result.stdout:
                    print("\n📝 Uncommitted changes:")
                    print(result.stdout[:500])  # Show first 500 chars
                else:
                    self.success_items.append("✅ Git working directory is clean")
            else:
                self.warnings.append("⚠️  Could not check git status")
        except Exception as e:
            self.warnings.append(f"⚠️  Git check failed: {str(e)}")
    
    def print_results(self):
        """Print check results."""
        print("\n" + "=" * 60)
        
        if self.issues:
            print("\n🔴 CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  {issue}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.success_items:
            print("\n✅ SUCCESS:")
            for item in self.success_items[:5]:  # Show first 5
                print(f"  {item}")
            if len(self.success_items) > 5:
                print(f"  ... and {len(self.success_items) - 5} more checks passed")
        
        print("\n" + "=" * 60)
        
        if not self.issues:
            print("\n✨ Project is ready for deployment!")
            print("\nNext steps:")
            print("1. git add .")
            print("2. git commit -m 'Prepare for deployment'")
            print("3. git push origin main")
            print("4. Deploy on Streamlit Cloud: https://streamlit.io/cloud")
            return True
        else:
            print("\n❌ Please fix critical issues before deploying.")
            return False


def main():
    """Run deployment checks."""
    checker = DeploymentChecker()
    success = checker.check_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
