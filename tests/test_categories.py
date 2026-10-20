from pathlib import Path

import pytest

from file_organizer import default_categories
from file_organizer.categories import build_category_map, category_for, normalize_extension


@pytest.mark.parametrize(
    "name, expected",
    [
        ("a.jpg", "Images"),
        ("a.pdf", "Documents"),
        ("a.csv", "Spreadsheets"),
        ("a.pptx", "Presentations"),
        ("a.mp3", "Music"),
        ("a.mp4", "Videos"),
        ("a.zip", "Archives"),
        ("a.exe", "Programs"),
        ("a.py", "Code"),
        ("a.woff2", "Fonts"),
        ("a.xyz", "Other"),
        ("README", "Other"),
    ],
)
def test_default_categories(name, expected):
    assert category_for(Path(name), build_category_map()) == expected


@pytest.mark.parametrize("name", ["photo.JPG", "photo.jpg", "photo.JpG"])
def test_extension_is_case_insensitive(name):
    assert category_for(Path(name), build_category_map()) == "Images"


def test_custom_categories_extend_defaults():
    mapping = build_category_map({".blend": "3D", "FBX": "3D"})
    assert mapping[".blend"] == "3D"
    assert mapping[".fbx"] == "3D"
    assert mapping[".jpg"] == "Images"


def test_custom_categories_override_defaults():
    assert build_category_map({".txt": "Notes"})[".txt"] == "Notes"


def test_default_categories_returns_copy():
    default_categories()[".jpg"] = "Hacked"
    assert default_categories()[".jpg"] == "Images"


@pytest.mark.parametrize("folder", ["", "..", "a/b", "/abs"])
def test_custom_folder_must_be_plain_name(folder):
    with pytest.raises(ValueError):
        build_category_map({".x": folder})


def test_normalize_extension():
    assert normalize_extension("JPG") == ".jpg"
    assert normalize_extension("..Png") == ".png"
    with pytest.raises(ValueError):
        normalize_extension(".")
