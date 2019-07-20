from __future__ import absolute_import

import numpy as np
import os
import pytest
from mirdata import salami, utils
from tests.test_utils import (mock_download, mock_unzip,
                              mock_validator, mock_force_delete_all,
                              DEFAULT_DATA_HOME)


def test_track():
    # test data home None
    track_default = salami.Track('2')
    assert track_default._data_home == os.path.join(DEFAULT_DATA_HOME, 'Salami')

    # test specific data home
    data_home = 'tests/resources/mir_datasets/Salami'

    with pytest.raises(ValueError):
        salami.Track('asdfasdf', data_home=data_home)

    track = salami.Track('2', data_home=data_home)

    # test attributes are loaded as expected
    assert track.track_id == '2'
    assert track._data_home == data_home
    assert track._track_paths == {
        'audio': [
            'audio/2.mp3',
            '76789a17bda0dd4d1d7e77424099c814'
        ],
        'annotator_1_uppercase': [
            'salami-data-public-master/annotations/2/parsed/textfile1_uppercase.txt',
            '54ba0804f720d85d195dcd7ffaec0794'
        ],
        'annotator_1_lowercase': [
            'salami-data-public-master/annotations/2/parsed/textfile1_lowercase.txt',
            '30ff127ff68c61039b94a44ab6ddda34'
        ],
        'annotator_2_uppercase': [
            'salami-data-public-master/annotations/2/parsed/textfile2_uppercase.txt',
            'e9dca8577f028d3505ff1e5801397b2f'
        ],
        'annotator_2_lowercase': [
            'salami-data-public-master/annotations/2/parsed/textfile2_lowercase.txt',
            '546a783c7b8bf96f2d718c7a4f114699'
        ]
    }
    assert track.audio_path == 'tests/resources/mir_datasets/Salami/' + \
        'audio/2.mp3'

    assert track.source == 'Codaich'
    assert track.annotator_1_id == '5'
    assert track.annotator_2_id == '8'
    assert track.duration_sec == '264'
    assert track.title == 'For_God_And_Country'
    assert track.artist == 'The_Smashing_Pumpkins'
    assert track.annotator_1_time == '37'
    assert track.annotator_2_time == '45'
    assert track.broad_genre == 'popular'
    assert track.genre == 'Alternative_Pop___Rock'

    # test that cached properties don't fail and have the expected type
    assert type(track.sections_annotator_1_uppercase) is utils.SectionData
    assert type(track.sections_annotator_1_lowercase) is utils.SectionData
    assert type(track.sections_annotator_2_uppercase) is utils.SectionData
    assert type(track.sections_annotator_2_lowercase) is utils.SectionData

    # # test audio loading functions
    # y, sr = track.audio
    # assert sr == 44100
    # assert y.shape == (89856, )


def test_track_ids():
    track_ids = salami.track_ids()
    assert type(track_ids) is list
    assert len(track_ids) == 1359


def test_load():
    data_home = 'tests/resources/mir_datasets/Salami'
    salami_data = salami.load(data_home=data_home, silence_validator=True)
    assert type(salami_data) is dict
    assert len(salami_data.keys()) == 1359

    # data home default
    salami_data_default = salami.load(silence_validator=True)
    assert type(salami_data_default) is dict
    assert len(salami_data_default.keys()) == 1359


def test_load_sections():
    # load a file which exists
    sections_path = 'tests/resources/mir_datasets/Salami/' + \
        'salami-data-public-master/annotations/2/parsed/textfile1_uppercase.txt'
    section_data = salami._load_sections(sections_path)

    # check types
    assert type(section_data) == utils.SectionData
    assert type(section_data.start_times) is np.ndarray
    assert type(section_data.end_times) is np.ndarray
    assert type(section_data.sections) is np.ndarray

    # check valuess
    assert np.array_equal(section_data.start_times, np.array(
        [0.0, 0.464399092, 14.379863945, 263.205419501]))
    assert np.array_equal(section_data.end_times, np.array(
        [0.464399092, 14.379863945, 263.205419501, 264.885215419]))
    assert np.array_equal(section_data.sections, np.array(
        ['Silence', 'A', 'B', 'Silence']))

    # load a file which doesn't exist
    section_data_none = salami._load_sections('fake/file/path')
    assert section_data_none is None

    # load none
    section_data_none2 = salami._load_sections('asdf/asdf')
    assert section_data_none2 is None


def test_load_metadata():
    data_home = 'tests/resources/mir_datasets/Salami'
    metadata = salami._load_metadata(data_home)
    assert metadata['data_home'] == data_home
    assert metadata['2'] == {
        'source': 'Codaich',
        'annotator_1_id': '5',
        'annotator_2_id': '8',
        'duration_sec': '264',
        'title': 'For_God_And_Country',
        'artist': 'The_Smashing_Pumpkins',
        'annotator_1_time': '37',
        'annotator_2_time': '45',
        'class': 'popular',
        'genre': 'Alternative_Pop___Rock',
    }

    none_metadata = salami._load_metadata('asdf/asdf')
    assert none_metadata is None


def test_cite():
    salami.cite()


@pytest.fixture
def mock_validate(mocker):
    return mocker.patch.object(salami, 'validate')


@pytest.fixture
def mock_load_sections(mocker):
    return mocker.patch.object(salami, '_load_sections')


@pytest.fixture
def data_home(tmpdir):
    return str(tmpdir)


@pytest.fixture
def mock_salami_exists(mocker):
    return mocker.patch.object(os.path, 'exists')


def test_download_already_exists(data_home, mocker,
                                 mock_force_delete_all,
                                 mock_salami_exists,
                                 mock_validator,
                                 mock_download,
                                 mock_unzip):
    mock_salami_exists.return_value = True

    salami.download(data_home)

    mock_force_delete_all.assert_not_called()
    mock_salami_exists.assert_called_once()
    mock_download.assert_not_called()
    mock_unzip.assert_not_called()
    mock_validator.assert_not_called()


def test_download_clean(data_home,
                        mocker,
                        mock_force_delete_all,
                        mock_salami_exists,
                        mock_download,
                        mock_unzip,
                        mock_validate):

    mock_salami_exists.return_value = False
    mock_download.return_value = 'foobar'
    mock_unzip.return_value = ''
    mock_validate.return_value = (False, False)

    salami.download(data_home)

    mock_force_delete_all.assert_not_called()
    mock_salami_exists.assert_called_once()
    mock_download.assert_called_once()
    mock_unzip.assert_called_once_with(mock_download.return_value, data_home, cleanup=True)
    mock_validate.assert_called_once_with(data_home)


def test_download_force_overwrite(data_home,
                          mocker,
                          mock_force_delete_all,
                          mock_salami_exists,
                          mock_download,
                          mock_unzip,
                          mock_validate):

    mock_salami_exists.return_value = False
    mock_download.return_value = 'foobar'
    mock_unzip.return_value = ''
    mock_validate.return_value = (False, False)

    salami.download(data_home, force_overwrite=True)

    mock_force_delete_all.assert_called_once_with(salami.ANNOTATIONS_REMOTE, data_home=data_home)
    mock_salami_exists.assert_called_once()
    mock_download.assert_called_once()
    mock_unzip.assert_called_once_with(mock_download.return_value, data_home, cleanup=True)
    mock_validate.assert_called_once_with(data_home)


def test_validate_invalid(data_home, mocker, mock_validator):
    mock_validator.return_value = (True, True)

    missing_files, invalid_checksums = salami.validate(data_home)
    assert missing_files and invalid_checksums
    mock_validator.assert_called_once()


def test_validate_valid(data_home, mocker, mock_validator):
    mock_validator.return_value = (False, False)

    missing_files, invalid_checksums = salami.validate(data_home)
    assert not (missing_files or invalid_checksums)
    mock_validator.assert_called_once()


def test_load_track_invalid_track_id():
    with pytest.raises(ValueError):
        salami.Track('a_fake_track')


def test_track_ids():
    assert salami.track_ids() == list(salami.INDEX.keys())