"""Integration tests for git changed files functionality via CLI."""
import subprocess
import tempfile
import json
from pathlib import Path


def run_linter(project_path: Path, *args) -> tuple[int, str, str]:
    """Run the linter CLI and return exit code, stdout, and stderr."""
    cmd = ["uv", "run", "python", "-m", "proboscis_linter.cli", str(project_path)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def init_git_repo(path: Path):
    """Initialize a git repository in the given path."""
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True, capture_output=True)


@pytest.mark.integration
def test_changed_only_flag_no_git():
    """Test --changed-only flag when not in a git repository."""
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
        
        # Run linter with --changed-only
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--changed-only")
        
        # Should fail with error about not being in git repo
        assert exit_code != 0
        assert "Not in a git repository" in stderr or "Not in a git repository" in stdout


@pytest.mark.integration
def test_changed_only_with_unstaged_changes():
    """Test --changed-only flag with unstaged changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create initial files and commit
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        file1 = src_dir / "unchanged.py"
        file1.write_text(
            "def unchanged_func():\n"
            "    return 1\n"
        )
        
        file2 = src_dir / "changed.py"
        file2.write_text(
            "def original_func():\n"
            "    return 2\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Modify file2
        file2.write_text(
            "def original_func():\n"
            "    return 2\n"
            "\n"
            "def new_func():\n"
            "    return 3\n"
        )
        
        # Run linter with --changed-only
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--changed-only", "--format", "json")
        
        # Parse JSON output
        violations = json.loads(stdout)["violations"]
        
        # Should only have violations from changed.py
        assert all("changed.py" in v["file"] for v in violations)
        assert not any("unchanged.py" in v["file"] for v in violations)
        
        # Should include violations for new_func
        assert any(v["function"] == "new_func" for v in violations)


@pytest.mark.integration
def test_changed_only_with_staged_changes():
    """Test --changed-only flag with staged changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create initial files and commit
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        file1 = src_dir / "file1.py"
        file1.write_text(
            "def func1():\n"
            "    return 1\n"
        )
        
        file2 = src_dir / "file2.py"
        file2.write_text(
            "def func2():\n"
            "    return 2\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Modify and stage file1
        file1.write_text(
            "def func1():\n"
            "    return 1\n"
            "\n"
            "def func1_new():\n"
            "    return 11\n"
        )
        subprocess.run(["git", "add", str(file1)], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Modify file2 but don't stage it
        file2.write_text(
            "def func2():\n"
            "    return 2\n"
            "\n"
            "def func2_new():\n"
            "    return 22\n"
        )
        
        # Run linter with --changed-only
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--changed-only", "--format", "json")
        
        # Parse JSON output
        violations = json.loads(stdout)["violations"]
        
        # Should have violations from both files (staged and unstaged)
        assert any("file1.py" in v["file"] for v in violations)
        assert any("file2.py" in v["file"] for v in violations)


@pytest.mark.integration
def test_changed_only_with_untracked_files():
    """Test --changed-only flag with untracked files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create and commit initial file
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        committed_file = src_dir / "committed.py"
        committed_file.write_text(
            "def committed_func():\n"
            "    return 1\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Create new untracked file
        untracked_file = src_dir / "untracked.py"
        untracked_file.write_text(
            "def untracked_func():\n"
            "    return 42\n"
        )
        
        # Run linter with --changed-only
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--changed-only", "--format", "json")
        
        # Parse JSON output
        violations = json.loads(stdout)["violations"]
        
        # Should only have violations from untracked.py
        assert all("untracked.py" in v["file"] for v in violations)
        assert not any("committed.py" in v["file"] for v in violations)
        assert any(v["function"] == "untracked_func" for v in violations)


@pytest.mark.integration
def test_changed_only_no_changes():
    """Test --changed-only flag when there are no changes."""
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
        
        # Run linter with --changed-only (no changes)
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--changed-only")
        
        # Should report no violations since no files were checked
        assert exit_code == 0
        assert "No violations found" in stdout


@pytest.mark.integration
def test_changed_only_combined_with_noqa():
    """Test --changed-only flag combined with noqa comments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Initialize git repo
        init_git_repo(tmpdir_path)
        
        # Create and commit initial file
        src_dir = tmpdir_path / "src"
        src_dir.mkdir()
        
        source_file = src_dir / "module.py"
        source_file.write_text(
            "def existing_func():\n"
            "    return 1\n"
        )
        
        subprocess.run(["git", "add", "."], cwd=tmpdir_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir_path, check=True, capture_output=True)
        
        # Modify file with noqa comment
        source_file.write_text(
            "def existing_func():\n"
            "    return 1\n"
            "\n"
            "def new_func_with_noqa():  #noqa PL001\n"
            "    return 2\n"
            "\n"
            "def new_func_without_noqa():\n"
            "    return 3\n"
        )
        
        # Run linter with --changed-only
        exit_code, stdout, stderr = run_linter(tmpdir_path, "--changed-only", "--format", "json")
        
        # Parse JSON output
        violations = json.loads(stdout)["violations"]
        
        # Should not have PL001 violations for new_func_with_noqa
        assert not any(v["function"] == "new_func_with_noqa" and "PL001" in v["rule"] for v in violations)
        
        # Should have violations for new_func_without_noqa
        assert any(v["function"] == "new_func_without_noqa" for v in violations)