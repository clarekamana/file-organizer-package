from file_organizer import organize, preview
from conftest import snapshot


def test_dry_run_changes_nothing(make_files):
    root = make_files("a.jpg", "b.pdf", "sub/c.mp3", "weird.xyz", ".hidden")
    before = snapshot(root)
    result = organize(root, dry_run=True)
    assert snapshot(root) == before
    assert not (root / "Images").exists()
    assert result.dry_run is True
    assert result.files_moved == 3  # a.jpg, b.pdf, weird.xyz
    assert sorted(result.created_directories) == [root / "Documents", root / "Images", root / "Other"]


def test_preview_function_never_modifies(make_files):
    root = make_files("a.jpg")
    before = snapshot(root)
    result = preview(root)
    assert result.dry_run
    assert snapshot(root) == before


def test_preview_ignores_dry_run_option(make_files):
    root = make_files("a.jpg")
    result = preview(root, dry_run=False)
    assert result.dry_run
    assert (root / "a.jpg").exists()


def test_dry_run_plans_conflict_renames(make_files):
    root = make_files("photo.jpg", "Images/photo.jpg")
    result = organize(root, dry_run=True)
    assert result.moves[0].destination.name == "photo_1.jpg"
    assert (root / "photo.jpg").exists()


def test_dry_run_matches_real_run(make_files):
    root = make_files("a.jpg", "b.pdf", "c.xyz", "Images/a.jpg")
    planned = [(m.source, m.destination) for m in organize(root, dry_run=True).moves]
    actual = [(m.source, m.destination) for m in organize(root).moves]
    assert planned == actual


def test_dry_run_on_empty_directory(tmp_path):
    result = organize(tmp_path, dry_run=True)
    assert result.files_moved == 0
    assert list(tmp_path.iterdir()) == []
