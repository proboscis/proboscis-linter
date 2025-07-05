"""Unit tests for git changed files functionality."""
import subprocess
import tempfile
from pathlib import Path
import pytest
from proboscis_linter.linter import ProboscisLinter
from proboscis_linter.config import ProboscisConfig


def init_git_repo(path: Path):
    """Initialize a git repository in the given path."""
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True, capture_output=True)


@pytest.mark.unit
def test_lint_changed_files_no_git_repo():
    """Test that lint_changed_files raises error when not in a git repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a source file
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def my_function():\n"
            "    return 42\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Should raise error when not in git repo
        with pytest.raises(RuntimeError, match="Not in a git repository"):
            linter.lint_changed_files(tmpdir_path)


@pytest.mark.unit
def test_lint_changed_files_unstaged():
    """Test linting files with unstaged changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create a source file and commit it
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def existing_function():\n"
            "    return 1\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Modify the file (unstaged change)
        source_file.write_text(
            "def existing_function():\n"
            "    return 1\n"
            "\n"
            "def new_function():\n"
            "    return 42\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint only changed files
        violations = linter.lint_changed_files(tmpdir_path)
        
        # Should find violations for new_function
        assert any(v.function_name == "new_function" for v in violations)
        # Might also have violations for existing_function since the whole file is considered changed


@pytest.mark.unit
def test_lint_changed_files_staged():
    """Test linting files with staged changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create initial files and commit
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        file1 = src_dir / "module1.py"
        file1.write_text(
            "def func1():\n"
            "    return 1\n"
        )
        
        file2 = src_dir / "module2.py"
        file2.write_text(
            "def func2():\n"
            "    return 2\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Modify file1 and stage it
        file1.write_text(
            "def func1():\n"
            "    return 1\n"
            "\n"
            "def func1_new():\n"
            "    return 11\n"
        )
        subprocess.run(["git", "add", str(file1)], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint only changed files
        violations = linter.lint_changed_files(tmpdir_path)
        
        # Should only check file1, not file2
        assert all(str(file1) in str(v.file_path) for v in violations)
        assert not any(str(file2) in str(v.file_path) for v in violations)


@pytest.mark.unit
def test_lint_changed_files_untracked():
    """Test linting untracked files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create and commit initial file
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        existing_file = src_dir / "existing.py"
        existing_file.write_text(
            "def existing():\n"
            "    return 1\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Create new untracked file
        new_file = src_dir / "new_file.py"
        new_file.write_text(
            "def untracked_function():\n"
            "    return 42\n"
        )
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint only changed files
        violations = linter.lint_changed_files(tmpdir_path)
        
        # Should find violations only in the new untracked file
        assert any(v.function_name == "untracked_function" for v in violations)
        assert not any("existing.py" in str(v.file_path) for v in violations)


@pytest.mark.unit
def test_lint_changed_files_no_changes():
    """Test linting when there are no changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create and commit a file
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def my_function():\n"
            "    return 42\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Create linter
        config = ProboscisConfig()
        linter = ProboscisLinter(config)
        
        # Lint only changed files (there are none)
        violations = linter.lint_changed_files(tmpdir_path)
        
        # Should have no violations since no files were checked
        assert len(violations) == 0