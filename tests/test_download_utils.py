from logging import fatal
import os
from pathlib import Path
import shutil
import zipfile
import re

from mirdata import download_utils, core

import pytest


@pytest.fixture
def mock_download_from_remote(mocker):
    return mocker.patch.object(download_utils, "download_from_remote")


@pytest.fixture
def mock_downloader(mocker):
    return mocker.patch.object(download_utils, "downloader")


@pytest.fixture
def mock_untar(mocker):
    return mocker.patch.object(download_utils, "untar")


@pytest.fixture
def mock_unzip(mocker):
    return mocker.patch.object(download_utils, "unzip")


@pytest.fixture
def mock_path(mocker, mock_download_from_remote):
    return mocker.patch.object(Path, "mkdir")


def test_downloader(mocker, mock_path):
    mock_zip = mocker.patch.object(download_utils, "download_zip_file")
    mock_tar = mocker.patch.object(download_utils, "download_tar_file")
    mock_download_from_remote = mocker.patch.object(
        download_utils, "download_from_remote"
    )

    zip_remote = download_utils.RemoteFileMetadata(
        filename="remote.zip", url="a", checksum=("1234")
    )
    tar_remote = download_utils.RemoteFileMetadata(
        filename="remote.tar.gz", url="a", checksum=("1234")
    )

    file_remote = download_utils.RemoteFileMetadata(
        filename="remote.txt", url="a", checksum=("1234")
    )
    index = core.Index("asdf.json")

    # Zip only
    download_utils.downloader("a", index=index, remotes={"b": zip_remote})
    mock_zip.assert_called_once_with(zip_remote, "a", False, False, False)
    mocker.resetall()

    # tar only
    download_utils.downloader("a", index=index, remotes={"b": tar_remote})
    mock_tar.assert_called_once_with(tar_remote, "a", False, False, False)
    mocker.resetall()

    # file only
    download_utils.downloader("a", index=index, remotes={"b": file_remote})
    mock_download_from_remote.assert_called_once_with(file_remote, "a", False, False)
    mocker.resetall()

    # zip and tar
    download_utils.downloader(
        "a", index=index, remotes={"b": zip_remote, "c": tar_remote}
    )
    mock_zip.assert_called_once_with(zip_remote, "a", False, False, False)
    mock_tar.assert_called_once_with(tar_remote, "a", False, False, False)
    mocker.resetall()

    # zip and file
    download_utils.downloader(
        "a", index=index, remotes={"b": zip_remote, "c": file_remote}
    )
    mock_zip.assert_called_once_with(zip_remote, "a", False, False, False)
    mock_download_from_remote.assert_called_once_with(file_remote, "a", False, False)
    mocker.resetall()

    # tar and file
    download_utils.downloader(
        "a", index=index, remotes={"b": tar_remote, "c": file_remote}
    )
    mock_tar.assert_called_once_with(tar_remote, "a", False, False, False)
    mock_download_from_remote.assert_called_once_with(file_remote, "a", False, False)
    mocker.resetall()

    # zip and tar and file
    download_utils.downloader(
        "a", index=index, remotes={"b": zip_remote, "c": tar_remote, "d": file_remote}
    )
    mock_zip.assert_called_once_with(zip_remote, "a", False, False, False)
    mock_download_from_remote.assert_called_once_with(file_remote, "a", False, False)
    mock_tar.assert_called_once_with(tar_remote, "a", False, False, False)
    mocker.resetall()

    # test partial download
    download_utils.downloader(
        "a",
        index=index,
        remotes={"b": zip_remote, "c": tar_remote, "d": file_remote},
        partial_download=["b", "d"],
    )
    mock_zip.assert_called_once_with(zip_remote, "a", False, False, False)
    mock_download_from_remote.assert_called_once_with(file_remote, "a", False, False)
    mocker.resetall()

    # test bad type partial download
    with pytest.raises(ValueError):
        download_utils.downloader(
            "a",
            index=index,
            remotes={"b": zip_remote, "c": tar_remote, "d": file_remote},
            partial_download="b",
        )

    with pytest.raises(ValueError):
        download_utils.downloader(
            "a",
            index=index,
            remotes={"b": zip_remote, "c": tar_remote, "d": file_remote},
            partial_download=["d", "e"],
        )

    # test info message
    download_utils.downloader("a", index=index, info_message="I am a message!")
    mocker.resetall()

    # test download twice - defaults
    download_utils.downloader(
        "a", index=index, remotes={"b": zip_remote, "c": tar_remote, "d": file_remote}
    )
    download_utils.downloader(
        "a", index=index, remotes={"b": zip_remote, "c": tar_remote, "d": file_remote}
    )

    # test download twice - cleanup=True
    download_utils.downloader(
        "a",
        index=index,
        remotes={"b": zip_remote, "c": tar_remote, "d": file_remote},
        cleanup=True,
    )
    download_utils.downloader(
        "a", index=index, remotes={"b": zip_remote, "c": tar_remote, "d": file_remote}
    )


def test_download_index_cases(mocker, mock_path):
    mock_zip = mocker.patch.object(download_utils, "download_zip_file")
    mock_download_from_remote = mocker.patch.object(
        download_utils, "download_from_remote"
    )

    zip_remote = download_utils.RemoteFileMetadata(
        filename="remote.zip", url="a", checksum=("1234")
    )
    file_remote = download_utils.RemoteFileMetadata(
        filename="remote.txt", url="a", checksum=("1234")
    )
    index = core.Index("asdf.json")
    index_partial = core.Index("asdf.json", partial_download=["b"])
    remote_index = core.Index("asdf.json", url="b", checksum="4567")

    # no remotes, no remote index
    download_utils.downloader("a", index=index, remotes=None, partial_download=None)
    mock_zip.assert_not_called()
    mock_download_from_remote.assert_not_called()
    mocker.resetall()

    # remotes, partial download index
    download_utils.downloader(
        "a",
        index=index_partial,
        remotes={"b": zip_remote, "d": file_remote},
        partial_download=None,
    )
    mock_zip.assert_called_once_with(zip_remote, "a", False, False, False)
    mock_download_from_remote.assert_not_called()
    mocker.resetall()

    # remotes, partial download index overwrite
    download_utils.downloader(
        "a",
        index=index_partial,
        remotes={"b": zip_remote, "d": file_remote},
        partial_download=["d"],
    )
    mock_zip.assert_not_called()
    mock_download_from_remote.assert_called_once_with(file_remote, "a", False, False)
    mocker.resetall()

    # no remotes, remote index
    download_utils.downloader(
        "a", index=remote_index, remotes=None, partial_download=None
    )
    mock_zip.assert_not_called()
    mock_download_from_remote.assert_called_once_with(
        remote_index.remote, "a", False, False
    )
    mocker.resetall()

    # remotes, remote index
    download_utils.downloader(
        "a", index=remote_index, remotes={"b": zip_remote}, partial_download=None
    )
    mock_zip.assert_called_once_with(zip_remote, "a", False, False, False)
    mock_download_from_remote.assert_called_once_with(
        remote_index.remote, "a", False, False
    )
    mocker.resetall()

    mock_download_from_remote = mocker.patch.object(
        download_utils, "download_from_remote"
    )

    index_remote = download_utils.RemoteFileMetadata(
        filename="index.json", url="a", checksum="1234"
    )
    file_remote = download_utils.RemoteFileMetadata(
        filename="remote.txt", url="b", checksum="5678"
    )
    index = core.Index("asdf.json")

    # Test with remotes containing "index"
    remotes = {"index": index_remote, "file": file_remote}
    download_utils.downloader(
        "a", index=index, remotes=remotes, partial_download=["file"]
    )

    # Verify that "index" is downloaded
    mock_download_from_remote.assert_any_call(index_remote, "a", False, False)
    mock_download_from_remote.assert_any_call(file_remote, "a", False, False)


def _clean(fpath):
    if os.path.exists(fpath):
        shutil.rmtree(fpath)


def test_downloader_with_server_file(httpserver):
    index = core.Index("asdf.json")
    httpserver.serve_content(open("tests/resources/remote.wav").read())

    TEST_REMOTE = download_utils.RemoteFileMetadata(
        filename="remote.wav",
        url=httpserver.url,
        checksum=("3f77d0d69dc41b3696f074ad6bf2852f"),
    )

    save_dir = "tests/resources/tmp_download_test"

    _clean(save_dir)
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})
    # test downloading twice
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})

    _clean(save_dir)
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, cleanup=True
    )
    # test downloading twice
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})

    _clean(save_dir)
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})
    # test downloading twice
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, force_overwrite=True
    )

    _clean(save_dir)

    # test with wrong checksum: raises error
    TEST_REMOTE = download_utils.RemoteFileMetadata(
        filename="remote.wav", url=httpserver.url, checksum=("wrongchecksum")
    )

    with pytest.raises(OSError):
        _clean(save_dir)
        download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})

    with pytest.raises(OSError):
        _clean(save_dir)
        download_utils.downloader(
            save_dir, index=index, remotes={"b": TEST_REMOTE}, cleanup=True
        )

    with pytest.raises(OSError):
        _clean(save_dir)
        download_utils.downloader(
            save_dir, index=index, remotes={"b": TEST_REMOTE}, force_overwrite=True
        )

    # test with wrong checksum: ignore error
    with pytest.warns(UserWarning):
        _clean(save_dir)
        download_utils.downloader(
            save_dir,
            index=index,
            remotes={"b": TEST_REMOTE},
            allow_invalid_checksum=True,
        )

    with pytest.warns(UserWarning):
        _clean(save_dir)
        download_utils.downloader(
            save_dir,
            index=index,
            remotes={"b": TEST_REMOTE},
            cleanup=True,
            allow_invalid_checksum=True,
        )

    with pytest.warns(UserWarning):
        _clean(save_dir)
        download_utils.downloader(
            save_dir,
            index=index,
            remotes={"b": TEST_REMOTE},
            force_overwrite=True,
            allow_invalid_checksum=True,
        )


def test_downloader_with_server_zip(httpserver):
    index = core.Index("asdf.json")
    httpserver.serve_content(open("tests/resources/remote.zip", "rb").read())

    TEST_REMOTE = download_utils.RemoteFileMetadata(
        filename="remote.zip",
        url=httpserver.url,
        checksum=("7a31ccfa28bfa3fb112d16c96e9d9a89"),
    )

    save_dir = "tests/resources/_tmp_test_download_utils"

    _clean(save_dir)
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})
    # test downloading twice
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})

    _clean(save_dir)
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, cleanup=True
    )
    # test downloading twice
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})

    _clean(save_dir)
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})
    # test downloading twice
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, force_overwrite=True
    )

    _clean(save_dir)
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, cleanup=True
    )
    # test downloading twice
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, force_overwrite=True
    )

    _clean(save_dir)


def test_downloader_with_server_tar(httpserver):
    index = core.Index("asdf.json")
    httpserver.serve_content(open("tests/resources/remote.tar.gz", "rb").read())

    TEST_REMOTE = download_utils.RemoteFileMetadata(
        filename="remote.tar.gz",
        url=httpserver.url,
        checksum=("9042f5eebdcd0b94aa7a3c9bf12dc51d"),
    )

    save_dir = "tests/resources/_tmp_test_download_utils"

    _clean(save_dir)
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})
    # test downloading twice
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})

    _clean(save_dir)
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, cleanup=True
    )
    # test downloading twice
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})

    _clean(save_dir)
    download_utils.downloader(save_dir, index=index, remotes={"b": TEST_REMOTE})
    # test downloading twice
    download_utils.downloader(
        save_dir, index=index, remotes={"b": TEST_REMOTE}, force_overwrite=True
    )

    _clean(save_dir)


def test_download_from_remote(httpserver, tmpdir):
    httpserver.serve_content(open("tests/resources/remote.wav").read())

    TEST_REMOTE = download_utils.RemoteFileMetadata(
        filename="remote.wav",
        url=httpserver.url,
        checksum=("3f77d0d69dc41b3696f074ad6bf2852f"),
    )

    download_path = download_utils.download_from_remote(
        TEST_REMOTE, str(tmpdir), False, False
    )


def test_download_from_remote_destdir(httpserver, tmpdir):
    httpserver.serve_content(open("tests/resources/remote.wav").read())

    TEST_REMOTE = download_utils.RemoteFileMetadata(
        filename="remote.wav",
        url=httpserver.url,
        checksum=("3f77d0d69dc41b3696f074ad6bf2852f"),
        destination_dir="subfolder",
    )

    download_path = download_utils.download_from_remote(
        TEST_REMOTE, str(tmpdir), False, False
    )
    expected_download_path = os.path.join(str(tmpdir), "subfolder", "remote.wav")
    assert expected_download_path == download_path


def test_download_from_remote_raises_IOError(httpserver, tmpdir):
    httpserver.serve_content("File not found!", 404)

    TEST_REMOTE = download_utils.RemoteFileMetadata(
        filename="remote.wav", url=httpserver.url, checksum=("1234")
    )

    with pytest.raises(IOError):
        download_utils.download_from_remote(TEST_REMOTE, str(tmpdir), False, False)


def test_unzip():
    download_utils.unzip("tests/resources/file.zip", cleanup=False)
    expected_file_location = os.path.join("tests", "resources", "file.txt")
    assert os.path.exists(expected_file_location)
    os.remove(expected_file_location)


def test_untar():
    download_utils.untar("tests/resources/file.tar.gz", cleanup=False)
    expected_file_location = os.path.join("tests", "resources", "file", "file.txt")
    assert os.path.exists(expected_file_location)
    os.remove(expected_file_location)


def test_download_zip_file(mocker, mock_download_from_remote, mock_unzip):
    mock_download_from_remote.return_value = "foo"
    download_utils.download_zip_file("a", "b", False, False, False)

    mock_download_from_remote.assert_called_once_with("a", "b", False, False)
    mock_unzip.assert_called_once_with("foo", cleanup=False)
    _clean("a")


def test_download_zip_file_ignorechecksum(
    mocker, mock_download_from_remote, mock_unzip
):
    mock_download_from_remote.return_value = "foo"
    download_utils.download_zip_file("a", "b", False, False, True)

    mock_download_from_remote.assert_called_once_with("a", "b", False, True)
    mock_unzip.assert_called_once_with("foo", cleanup=False)
    _clean("a")


def test_download_tar_file(mocker, mock_download_from_remote, mock_untar):
    mock_download_from_remote.return_value = "foo"
    download_utils.download_tar_file("a", "b", False, False, False)

    mock_download_from_remote.assert_called_once_with("a", "b", False, False)
    mock_untar.assert_called_once_with("foo", cleanup=False)
    _clean("a")


def test_download_tar_file_ignorechecksum(
    mocker, mock_download_from_remote, mock_untar
):
    mock_download_from_remote.return_value = "foo"
    download_utils.download_tar_file("a", "b", False, False, True)

    mock_download_from_remote.assert_called_once_with("a", "b", False, True)
    mock_untar.assert_called_once_with("foo", cleanup=False)
    _clean("a")


def test_extractall_unicode(mocker, mock_download_from_remote, mock_unzip):
    zip_files = ("tests/resources/utfissue.zip", "tests/resources/utfissuewin.zip")
    expected_files_all = (
        ["pic👨‍👩‍👧‍👦🎂.jpg", "Benoît.txt", "Icon"],
        ["pic👨‍👩‍👧‍👦🎂.jpg", "BenoŒt.txt", "Icon"],
    )
    for zipf, expected_files in zip(zip_files, expected_files_all):
        zfile = zipfile.ZipFile(zipf, "r")
        download_utils.extractall_unicode(zfile, os.path.dirname("tests/resources/"))
        zfile.close()
        for expected_file in expected_files:
            expected_file_location = os.path.join(
                "tests", "resources", "utfissue", expected_file
            )
            assert os.path.exists(expected_file_location)
            os.remove(expected_file_location)


def test_extractall_cp437(mocker, mock_download_from_remote, mock_unzip):
    zfile = zipfile.ZipFile("tests/resources/utfissue.zip", "r")
    zfile.extractall(os.path.dirname("tests/resources/"))
    zfile.close()
    expected_files = ["pic👨‍👩‍👧‍👦🎂.jpg", "Benoît.txt", "Icon"]
    for expected_file in expected_files:
        expected_file_location = os.path.join("tests", "resources", expected_file)
        assert not os.path.exists(expected_file_location)
    shutil.rmtree(os.path.join("tests", "resources", "__MACOSX"))
    shutil.rmtree(os.path.join("tests", "resources", "utfissue"))


def test_index_duplicate_prevention(mocker, mock_path):
    """Test that index is not added twice when already in partial_download"""
    mock_download = mocker.patch.object(download_utils, "download_from_remote")

    index_remote = download_utils.RemoteFileMetadata("index.json", "url", "1234")
    index = core.Index("test.json")

    # Index already in partial_download - should not be duplicated
    download_utils.downloader(
        "save_dir",
        index=index,
        remotes={"index": index_remote},
        partial_download=["index"],
    )

    # Should be called exactly once, not twice
    mock_download.assert_called_once_with(index_remote, "save_dir", False, False)


def test_zipped_index_detection_and_extraction(mocker, tmpdir):
    """Test zipped index file detection and extraction"""
    import zipfile

    # Create a zip file with PK magic bytes
    zip_path = tmpdir.join("index.zip")
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        zf.writestr("test.json", '{"test": "data"}')

    mocker.patch.object(
        download_utils, "download_from_remote", return_value=str(zip_path)
    )
    mock_unzip = mocker.patch.object(download_utils, "unzip")

    index_remote = download_utils.RemoteFileMetadata("test.json", "url", "1234")
    index = core.Index("test.json")

    download_utils.downloader(str(tmpdir), index=index, remotes={"index": index_remote})

    # Verify zip detection and extraction
    mock_unzip.assert_called_once_with(str(zip_path), cleanup=False)


def test_zipped_index_exception_handling(mocker, tmpdir):
    """Test exception handling when checking if index is zipped"""
    problem_file = tmpdir.join("problem.json")
    problem_file.write("content")

    mocker.patch.object(
        download_utils, "download_from_remote", return_value=str(problem_file)
    )
    # Mock open to raise exception (covers exception handling line)
    mocker.patch("builtins.open", side_effect=IOError("Error"))

    index_remote = download_utils.RemoteFileMetadata("test.json", "url", "1234")
    index = core.Index("test.json")

    # Should not raise exception, just log warning
    download_utils.downloader(str(tmpdir), index=index, remotes={"index": index_remote})
