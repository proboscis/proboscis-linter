"""End-to-end tests for __main__ module."""
import tempfile
import subprocess
import sys
import os
from pathlib import Path
import pytest


class TestMainE2E:
    """End-to-end tests for __main__ module in real-world scenarios."""
    
    @pytest.fixture
    def real_world_project(self):
        """Create a real-world-like project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "myproject"
            root.mkdir()
            
            # Create project files
            (root / "README.md").write_text("""
# MyProject

A sample Python project for testing proboscis-linter.
""")
            
            (root / "setup.py").write_text("""
from setuptools import setup, find_packages

setup(
    name="myproject",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
""")
            
            (root / "pyproject.toml").write_text("""
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.proboscis]
test_directories = ["tests"]
exclude_patterns = ["**/__pycache__/**", "**/build/**", "**/dist/**"]
fail_on_error = false

[tool.proboscis.rules]
PL001 = true
PL002 = true
PL003 = false
""")
            
            # Create source code
            src = root / "src" / "myproject"
            src.mkdir(parents=True)
            
            (src / "__init__.py").write_text('__version__ = "0.1.0"')
            
            (src / "main.py").write_text("""
import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="MyProject CLI")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()


def run():
    args = parse_args()
    if args.version:
        from . import __version__
        print(f"myproject {__version__}")
        return 0
    
    if args.debug:
        print("Debug mode enabled")
    
    print("MyProject is running!")
    return 0


def main():
    sys.exit(run())
""")
            
            (src / "utils.py").write_text("""
import os
import json


def load_config(config_path):
    if not os.path.exists(config_path):
        return {}
    
    with open(config_path, 'r') as f:
        return json.load(f)


def save_config(config_path, config):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def validate_config(config):
    required_keys = ['name', 'version']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    return True
""")
            
            # Create tests
            tests = root / "tests"
            tests.mkdir()
            
            (tests / "test_main.py").write_text("""
import pytest
from myproject.main import parse_args, run


def test_parse_args():
    # Test basic functionality
    pass


def test_run():
    # Test run function
    pass
""")
            
            (tests / "test_utils.py").write_text("""
import pytest
from myproject.utils import validate_config


def test_validate_config():
    config = {"name": "test", "version": "1.0"}
    assert validate_config(config) is True
""")
            
            yield root
    
    def test_run_as_module(self, real_world_project):
        """Test running proboscis_linter as a module on a real project."""
        result = subprocess.run(
            [sys.executable, '-m', 'proboscis_linter', str(real_world_project)],
            capture_output=True,
            text=True,
            cwd=str(real_world_project.parent)
        )
        
        # Should complete successfully
        assert result.returncode == 0
        
        # Should find violations
        assert "violations" in result.stdout
        assert "load_config" in result.stdout  # Missing tests
        assert "save_config" in result.stdout  # Missing tests
        
        # Should not report tested functions
        assert "Function 'validate_config' missing unit test" not in result.stdout
    
    def test_run_with_python_path(self, real_world_project):
        """Test running __main__.py directly with proper Python path."""
        # Find the actual __main__.py file
        main_file = Path(__file__).parent.parent.parent / "src" / "proboscis_linter" / "__main__.py"
        
        if main_file.exists():
            # Set PYTHONPATH to include src directory
            env = os.environ.copy()
            src_dir = main_file.parent.parent
            env['PYTHONPATH'] = str(src_dir) + os.pathsep + env.get('PYTHONPATH', '')
            
            result = subprocess.run(
                [sys.executable, str(main_file), str(real_world_project), '--format', 'json'],
                capture_output=True,
                text=True,
                env=env
            )
            
            assert result.returncode == 0
            assert '"total_violations"' in result.stdout
    
    def test_ci_pipeline_simulation(self, real_world_project):
        """Simulate a CI pipeline using proboscis-linter."""
        # Create a CI script
        ci_script = real_world_project / ".github" / "workflows" / "lint.yml"
        ci_script.parent.mkdir(parents=True)
        
        # Create a shell script that would be run by CI
        lint_script = real_world_project / "scripts" / "lint.sh"
        lint_script.parent.mkdir(parents=True)
        lint_script.write_text("""#!/bin/bash
set -e

echo "Running proboscis-linter..."
python -m proboscis_linter . --fail-on-error

echo "Linting completed!"
""")
        lint_script.chmod(0o755)
        
        # Run the lint script
        result = subprocess.run(
            ['bash', str(lint_script)],
            capture_output=True,
            text=True,
            cwd=str(real_world_project)
        )
        
        # Should fail because there are violations and --fail-on-error is set
        assert result.returncode != 0
        assert "Running proboscis-linter..." in result.stdout
        assert "violations" in result.stdout or "violations" in result.stderr
    
    def test_pre_commit_hook_simulation(self, real_world_project):
        """Simulate using proboscis-linter as a pre-commit hook."""
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=real_world_project, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                      cwd=real_world_project, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                      cwd=real_world_project, capture_output=True)
        
        # Create pre-commit hook
        hooks_dir = real_world_project / ".git" / "hooks"
        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text("""#!/bin/bash
# Pre-commit hook to run proboscis-linter on changed files

echo "Running proboscis-linter on changed files..."
python -m proboscis_linter . --changed-only --format json

if [ $? -ne 0 ]; then
    echo "Linting failed! Please fix violations before committing."
    exit 1
fi

echo "Linting passed!"
exit 0
""")
        pre_commit.chmod(0o755)
        
        # Stage some files
        subprocess.run(['git', 'add', '.'], cwd=real_world_project, capture_output=True)
        
        # Try to commit (should run pre-commit hook)
        result = subprocess.run(
            ['git', 'commit', '-m', 'Initial commit'],
            capture_output=True,
            text=True,
            cwd=str(real_world_project)
        )
        
        # Check that linter was run
        assert "Running proboscis-linter on changed files..." in result.stdout
    
    def test_docker_simulation(self):
        """Simulate running proboscis-linter in a Docker-like environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a simple project
            app = root / "app"
            app.mkdir()
            
            (app / "server.py").write_text("""
def start_server(host='0.0.0.0', port=8080):
    print(f"Starting server on {host}:{port}")
    return True


def stop_server():
    print("Stopping server")
    return True


def health_check():
    return {"status": "healthy"}
""")
            
            # Create Dockerfile that would include linting
            dockerfile = root / "Dockerfile"
            dockerfile.write_text("""
FROM python:3.9

WORKDIR /app
COPY . .

# Install dependencies
RUN pip install proboscis-linter

# Run linter as part of build
RUN python -m proboscis_linter /app || true

CMD ["python", "app/server.py"]
""")
            
            # Simulate the linting step
            result = subprocess.run(
                [sys.executable, '-m', 'proboscis_linter', str(app)],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "start_server" in result.stdout
            assert "stop_server" in result.stdout
            assert "health_check" in result.stdout
    
    def test_vscode_integration_simulation(self, real_world_project):
        """Simulate VSCode integration scenario."""
        # Create VSCode tasks.json that would run linter
        vscode_dir = real_world_project / ".vscode"
        vscode_dir.mkdir()
        
        tasks_json = vscode_dir / "tasks.json"
        tasks_json.write_text("""{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Lint with Proboscis",
            "type": "shell",
            "command": "python",
            "args": [
                "-m",
                "proboscis_linter",
                "${workspaceFolder}",
                "--format",
                "json"
            ],
            "group": {
                "kind": "test",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "problemMatcher": []
        }
    ]
}""")
        
        # Simulate running the task
        result = subprocess.run(
            [sys.executable, '-m', 'proboscis_linter', str(real_world_project), '--format', 'json'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        # Parse JSON output
        import json
        output_data = json.loads(result.stdout)
        assert 'total_violations' in output_data
        assert 'violations' in output_data
    
    def test_makefile_integration(self, real_world_project):
        """Test integration with Makefile workflow."""
        makefile = real_world_project / "Makefile"
        makefile.write_text("""
.PHONY: lint test check all

lint:
\t@echo "Running proboscis-linter..."
\t@python -m proboscis_linter . || true

test:
\t@echo "Running tests..."
\t@pytest tests/

check: lint test
\t@echo "All checks completed!"

all: check
""")
        
        # Run make lint
        result = subprocess.run(
            ['make', 'lint'],
            capture_output=True,
            text=True,
            cwd=str(real_world_project)
        )
        
        # Make might not be available on all systems
        if result.returncode == 0:
            assert "Running proboscis-linter..." in result.stdout
        else:
            # If make is not available, test the command directly
            result = subprocess.run(
                [sys.executable, '-m', 'proboscis_linter', '.'],
                capture_output=True,
                text=True,
                cwd=str(real_world_project)
            )
            assert result.returncode == 0
    
    def test_performance_large_project(self):
        """Test performance on a large project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a large project structure
            for pkg_idx in range(10):
                package = root / f"package_{pkg_idx}"
                package.mkdir()
                
                for mod_idx in range(20):
                    module = package / f"module_{mod_idx}.py"
                    
                    content = ['"""Module docstring."""']
                    for func_idx in range(10):
                        content.append(f"""
def function_{pkg_idx}_{mod_idx}_{func_idx}(x, y):
    \"\"\"Function docstring.\"\"\"
    return x + y
""")
                    
                    module.write_text('\n'.join(content))
            
            # Time the execution
            import time
            start_time = time.time()
            
            result = subprocess.run(
                [sys.executable, '-m', 'proboscis_linter', str(root)],
                capture_output=True,
                text=True
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result.returncode == 0
            assert execution_time < 120  # Should complete within 2 minutes
            
            # Should find many violations
            assert "violations" in result.stdout
            
            print(f"Linted large project (200 files, 2000 functions) in {execution_time:.2f} seconds")