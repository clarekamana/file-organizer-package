import pytest

from file_organizer import __version__
from file_organizer.cli import main
from conftest import snapshot


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "organize" in out and "preview" in out


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_organize_dry_run(make_files, capsys):
    root = make_files("photo.jpg", "report.pdf")
    before = snapshot(root)
    assert main(["organize", str(root), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "photo.jpg" in out and "Images/" in out
    assert "2 files would be moved." in out
    assert snapshot(root) == before


def test_preview_command(make_files, capsys):
    root = make_files("a.mp3")
    before = snapshot(root)
    assert main(["preview", str(root)]) == 0
    assert "1 file would be moved." in capsys.readouterr().out
    assert snapshot(root) == before


def test_organize_real(make_files, capsys):
    root = make_files("a.jpg", "b.pdf")
    assert main(["organize", str(root)]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" not in out
    assert "2 files moved." in out
    assert (root / "Images" / "a.jpg").exists()


def test_conflict_skip_option(make_files, capsys):
    root = make_files("a.jpg", "Images/a.jpg")
    assert main(["organize", str(root), "--conflict", "skip"]) == 0
    out = capsys.readouterr().out
    assert "1 skipped" in out
    assert (root / "a.jpg").exists()


def test_conflict_rename_shows_new_name(make_files, capsys):
    root = make_files("a.jpg", "Images/a.jpg")
    main(["organize", str(root), "--dry-run"])
    assert "Images/a_1.jpg" in capsys.readouterr().out


def test_invalid_conflict_choice():
    with pytest.raises(SystemExit) as exc:
        main(["organize", ".", "--conflict", "overwrite"])
    assert exc.value.code == 2


def test_include_hidden_option(make_files):
    root = make_files(".x.jpg")
    main(["organize", str(root), "--include-hidden"])
    assert (root / "Images" / ".x.jpg").exists()


def test_invalid_path_exit_code(tmp_path, capsys):
    assert main(["organize", str(tmp_path / "missing")]) == 2
    assert "does not exist" in capsys.readouterr().err
