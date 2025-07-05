"""End-to-end tests for auto-fix functionality."""
import pytest
import subprocess
from pathlib import Path
from textwrap import dedent


@pytest.mark.e2e
def test_AutoFixer_apply_fixes(tmp_path):
    """End-to-end test for the apply_fixes method of AutoFixer class via CLI."""
    # Create a test project
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    test_dir = tmp_path / "test" / "unit"
    test_dir.mkdir(parents=True)
    
    # Create source file
    src_file = src_dir / "sample.py"
    src_file.write_text(dedent('''
        def process_data(data):
            return data * 2
    ''').strip())
    
    # Create test file without markers
    test_file = test_dir / "test_sample.py"
    test_file.write_text(dedent('''
        import pytest
        from src.sample import process_data
        
        @pytest.mark.e2e
        def test_process_data():
            assert process_data(5) == 10
        
        @pytest.mark.e2e
        def test_process_data_zero():
            assert process_data(0) == 0
    ''').strip())
    
    # Create pyproject.toml to enable PL004
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(dedent('''
        [tool.proboscis]
        test_directories = ["test"]
        
        [tool.proboscis.rules]
        PL001 = false
        PL002 = false
        PL003 = false
        PL004 = true
    ''').strip())
    
    # Run linter with --fix flag
    result = subprocess.run(
        ["uv", "run", "proboscis-linter", str(tmp_path), "--fix"],
        cwd=Path(__file__).parent.parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    # Check that fixes were applied
    assert "Fixed" in result.stderr or "Applying automatic fixes" in result.stderr
    
    # Verify the test file now has markers
    updated_content = test_file.read_text()
    assert "@pytest.mark.unit" in updated_content
    assert updated_content.count("@pytest.mark.unit") == 2
    
    # Verify the fixed file is valid Python
    expected = dedent('''
        import pytest
        from src.sample import process_data
        
        @pytest.mark.e2e
        @pytest.mark.unit
        def test_process_data():
            assert process_data(5) == 10
        
        @pytest.mark.e2e
        @pytest.mark.unit
        def test_process_data_zero():
            assert process_data(0) == 0
    ''').strip()
    assert test_file.read_text() == expected