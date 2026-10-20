from file_organizer import organize


def test_rename_on_conflict(make_files):
    root = make_files("photo.jpg", "Images/photo.jpg")
    (root / "Images" / "photo.jpg").write_text("original")
    result = organize(root)
    assert (root / "Images" / "photo.jpg").read_text() == "original"
    assert (root / "Images" / "photo_1.jpg").read_text() == "x"
    assert result.moves[0].renamed


def test_rename_counter_increments(make_files):
    root = make_files("photo.jpg", "Images/photo.jpg", "Images/photo_1.jpg", "Images/photo_2.jpg")
    organize(root)
    assert (root / "Images" / "photo_3.jpg").exists()
    assert not (root / "photo.jpg").exists()


def test_skip_on_conflict(make_files):
    root = make_files("photo.jpg", "Images/photo.jpg")
    (root / "Images" / "photo.jpg").write_text("original")
    result = organize(root, conflict="skip")
    assert (root / "photo.jpg").exists()
    assert (root / "Images" / "photo.jpg").read_text() == "original"
    assert result.files_moved == 0
    assert result.files_skipped == 1


def test_no_overwrite_ever_across_repeated_runs(make_files):
    root = make_files("a.txt")
    for i in range(3):
        (root / "a.txt").write_text(f"v{i}")
        organize(root)
    contents = sorted(p.read_text() for p in (root / "Documents").iterdir())
    assert contents == ["v0", "v1", "v2"]


def test_names_without_extension_get_suffix(make_files):
    root = make_files("README", "Other/README")
    organize(root)
    assert (root / "Other" / "README_1").exists()
