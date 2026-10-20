import os
import sys

import pytest

from file_organizer import InvalidOptionError, InvalidPathError, Organizer, organize
from conftest import snapshot


def test_basic_organization(make_files):
    root = make_files("photo.jpg", "report.pdf", "song.mp3", "movie.mp4")
    result = organize(root)
    assert result.files_moved == 4
    assert (root / "Images" / "photo.jpg").is_file()
    assert (root / "Documents" / "report.pdf").is_file()
    assert (root / "Music" / "song.mp3").is_file()
    assert (root / "Videos" / "movie.mp4").is_file()
    assert not (root / "photo.jpg").exists()
    assert len(result.created_directories) == 4


def test_content_is_preserved(make_files):
    root = make_files("a.txt", content="hello")
    organize(root)
    assert (root / "Documents" / "a.txt").read_text() == "hello"


def test_unknown_and_missing_extensions_go_to_other(make_files):
    root = make_files("weird.xyz", "Makefile")
    organize(root)
    assert (root / "Other" / "weird.xyz").is_file()
    assert (root / "Other" / "Makefile").is_file()


def test_directories_are_not_moved(make_files):
    root = make_files("photo.jpg", "project/code.py", "document.pdf")
    result = organize(root)
    assert result.files_moved == 2
    assert (root / "project" / "code.py").is_file()


def test_empty_directory(tmp_path):
    result = organize(tmp_path)
    assert result.files_moved == 0
    assert list(tmp_path.iterdir()) == []


def test_hidden_files_skipped_by_default(make_files):
    root = make_files(".env", ".hidden.jpg")
    result = organize(root)
    assert result.files_moved == 0
    assert result.files_skipped == 2
    assert (root / ".env").exists()


def test_include_hidden(make_files):
    root = make_files(".hidden.jpg")
    organize(root, include_hidden=True)
    assert (root / "Images" / ".hidden.jpg").exists()


def test_custom_categories(make_files):
    root = make_files("model.blend", "mesh.OBJ", "photo.jpg")
    Organizer(categories={".blend": "3D", ".obj": "3D"}).organize(root)
    assert (root / "3D" / "model.blend").exists()
    assert (root / "3D" / "mesh.OBJ").exists()
    assert (root / "Images" / "photo.jpg").exists()


def test_case_insensitive_extensions(make_files):
    root = make_files("a.JPG", "b.jpg", "c.JpG")
    organize(root)
    assert sorted(p.name for p in (root / "Images").iterdir()) == ["a.JPG", "b.jpg", "c.JpG"]


def test_tilde_and_relative_paths(make_files, monkeypatch):
    root = make_files("a.jpg", "b.pdf")
    monkeypatch.chdir(root)
    organize(".")
    assert (root / "Images" / "a.jpg").exists()
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.setenv("USERPROFILE", str(root))
    (root / "c.png").write_text("x")
    organize("~")
    assert (root / "Images" / "c.png").exists()


def test_string_and_path_inputs(make_files):
    root = make_files("a.jpg")
    assert organize(str(root)).files_moved == 1


def test_missing_path_raises(tmp_path):
    with pytest.raises(InvalidPathError, match="does not exist"):
        organize(tmp_path / "nope")


def test_file_path_raises(make_files):
    root = make_files("a.jpg")
    with pytest.raises(InvalidPathError, match="not a directory"):
        organize(root / "a.jpg")


def test_invalid_conflict_option(tmp_path):
    with pytest.raises(InvalidOptionError):
        Organizer(conflict="overwrite")


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="no symlinks")
def test_symlinks_are_skipped(make_files):
    root = make_files("real.jpg")
    try:
        os.symlink(root / "real.jpg", root / "link.jpg")
    except (OSError, NotImplementedError):
        pytest.skip("cannot create symlinks here")
    result = organize(root)
    assert (root / "link.jpg").is_symlink()
    assert [s.path.name for s in result.skipped] == ["link.jpg"]
    assert result.files_moved == 1


def test_move_failure_is_recorded_not_raised(make_files, monkeypatch):
    root = make_files("a.jpg", "b.jpg")
    import shutil

    real_move = shutil.move

    def flaky(src, dst):
        if src.endswith("a.jpg"):
            raise PermissionError("denied")
        return real_move(src, dst)

    monkeypatch.setattr("file_organizer.organizer.shutil.move", flaky)
    result = organize(root)
    assert result.files_moved == 1
    assert result.files_failed == 1
    assert result.errors[0].path.name == "a.jpg"
    assert "denied" in result.errors[0].message
    assert (root / "a.jpg").exists()


def test_file_disappearing_is_recorded(make_files, monkeypatch):
    root = make_files("a.jpg")
    import shutil

    def vanish(src, dst):
        raise FileNotFoundError(src)

    monkeypatch.setattr("file_organizer.organizer.shutil.move", vanish)
    result = organize(root)
    assert result.files_failed == 1
    assert "disappeared" in result.errors[0].message


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores modes")
def test_read_only_target_dir(make_files):
    root = make_files("a.jpg")
    images = root / "Images"
    images.mkdir()
    images.chmod(0o500)
    try:
        result = organize(root)
    finally:
        images.chmod(0o700)
    assert result.files_failed == 1
    assert (root / "a.jpg").exists()


def test_category_folder_name_taken_by_a_file(make_files):
    # A symlink is never moved, so it keeps blocking the name "Images".
    root = make_files("target.txt", "a.jpg")
    try:
        os.symlink(root / "target.txt", root / "Images")
    except (OSError, NotImplementedError):
        pytest.skip("cannot create symlinks here")
    result = organize(root)
    assert result.files_failed == 1
    assert (root / "a.jpg").exists()
    assert (root / "Images").is_symlink()


# -- recursive mode -------------------------------------------------------


def test_recursive_off_by_default(make_files):
    root = make_files("sub/a.jpg")
    organize(root)
    assert (root / "sub" / "a.jpg").exists()


def test_recursive_moves_nested_files(make_files):
    root = make_files("top.pdf", "sub/a.jpg", "sub/deeper/b.mp3")
    result = organize(root, recursive=True)
    assert result.files_moved == 3
    assert (root / "Images" / "a.jpg").exists()
    assert (root / "Music" / "b.mp3").exists()
    assert (root / "sub").is_dir()  # directories are never removed


def test_recursive_is_idempotent(make_files):
    root = make_files("a.jpg", "sub/b.jpg", "sub/c.pdf")
    organize(root, recursive=True)
    after_first = snapshot(root)
    second = organize(root, recursive=True)
    assert second.files_moved == 0
    assert snapshot(root) == after_first


def test_recursive_same_names_do_not_collide(make_files):
    root = make_files("a/photo.jpg", "b/photo.jpg", "photo.jpg")
    result = organize(root, recursive=True)
    assert result.files_moved == 3
    assert sorted(p.name for p in (root / "Images").iterdir()) == [
        "photo.jpg",
        "photo_1.jpg",
        "photo_2.jpg",
    ]


def test_recursive_skips_hidden_dirs(make_files):
    root = make_files(".git/objects/a.jpg", "b.jpg")
    organize(root, recursive=True)
    assert (root / ".git" / "objects" / "a.jpg").exists()


def test_recursive_ignores_existing_category_folders(make_files):
    root = make_files("Images/old.pdf")
    result = organize(root, recursive=True)
    assert result.files_moved == 0
    assert (root / "Images" / "old.pdf").exists()


def test_recursive_dry_run_matches_real_run(make_files):
    root = make_files("a/photo.jpg", "b/photo.jpg", "x.pdf")
    planned = [(m.source, m.destination) for m in organize(root, recursive=True, dry_run=True).moves]
    done = [(m.source, m.destination) for m in organize(root, recursive=True).moves]
    assert planned == done


# -- symlink handling without needing real symlinks (e.g. Windows) ----------


@pytest.fixture
def pretend_symlinks(monkeypatch):
    """Make Path.is_symlink() return True for the given file names."""
    from pathlib import Path

    real = Path.is_symlink

    def install(*names):
        monkeypatch.setattr(
            Path, "is_symlink", lambda self: self.name in names or real(self)
        )

    return install


def test_symlinks_skipped_simulated(make_files, pretend_symlinks):
    root = make_files("link.jpg", "real.jpg")
    pretend_symlinks("link.jpg")
    result = organize(root)
    assert (root / "link.jpg").exists()
    assert [(s.path.name, s.reason) for s in result.skipped] == [("link.jpg", "symlink")]
    assert result.files_moved == 1


def test_symlinks_skipped_simulated_recursive(make_files, pretend_symlinks):
    root = make_files("sub/link.jpg")
    pretend_symlinks("link.jpg")
    result = organize(root, recursive=True)
    assert (root / "sub" / "link.jpg").exists()
    assert result.files_skipped == 1


def test_category_name_blocked_by_non_directory(make_files, pretend_symlinks):
    root = make_files("Images", "a.jpg")
    pretend_symlinks("Images")  # keeps the "Images" file from being moved to Other
    result = organize(root)
    assert result.files_failed == 1
    assert (root / "a.jpg").exists()
