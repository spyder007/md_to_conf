import pytest
import logging
from md_to_conf import ConfluenceConverter, PageInfo, ConfluenceApiClient
from unittest.mock import patch


def test_client_init():
    file = "tests/testfiles/basic.md"
    source = "default"
    title = "title"
    orgname = "orgname"
    use_ssl = True
    ancestor_title = "ancestortitle"
    api_key = "key"
    username = "user"
    space_key = "PO"
    editor_version = 2

    converter = ConfluenceConverter(
        file,
        source,
        title,
        orgname,
        use_ssl,
        username,
        space_key,
        api_key,
        ancestor_title,
        editor_version,
    )

    assert converter.file == file
    assert converter.md_source == source
    assert converter.title == title
    assert converter.org_name == orgname
    assert converter.use_ssl == use_ssl
    assert converter.user_name == username
    assert converter.space_key == space_key
    assert converter.api_key == api_key
    assert converter.ancestor == ancestor_title
    assert converter.version == editor_version


@pytest.fixture
def test_converter():
    return ConfluenceConverter(
        "tests/testfiles/basic.md",
        "default",
        None,
        "orgname",
        True,
        "username",
        "spacekey",
        "apikey",
        "ancestortitle",
        2,
    )


def test_get_title_from_file(test_converter):
    title = test_converter.get_title()
    assert title == "Basic Page"


def test_get_title_supplied(test_converter):
    test_converter.title = "Supplied Title"
    title = test_converter.get_title()
    assert title == "Supplied Title"


def test_get_space_key(test_converter):
    space_key = test_converter.get_space_key()
    assert space_key == "spacekey"


def test_get_space_key_no_space(test_converter):
    test_converter.space_key = None
    space_key = test_converter.get_space_key()
    assert space_key == f"~{test_converter.user_name}"


def test_get_confluence_url(test_converter):
    url = test_converter.get_confluence_api_url()
    assert url == "https://orgname.atlassian.net/wiki"


def test_get_confluence_url_no_ssl(test_converter):
    test_converter.use_ssl = False
    url = test_converter.get_confluence_api_url()
    assert url == "http://orgname.atlassian.net/wiki"


def test_get_confluence_url_local(test_converter):
    test_converter.org_name = "my.local.url"
    url = test_converter.get_confluence_api_url()
    assert url == "https://my.local.url"


@patch.object(ConfluenceApiClient, "get_page", return_value=PageInfo(0, 0, 0, ""))
def test_get_parent_page_no_ancestor(get_page_mock):
    converter = ConfluenceConverter(
        "tests/testfiles/basic.md",
        "default",
        None,
        "orgname",
        True,
        "username",
        "spacekey",
        "apikey",
        None,
        2,
    )

    parent_page_id = converter.get_parent_page()
    assert parent_page_id == 0
    get_page_mock.assert_not_called()


@patch.object(
    ConfluenceApiClient, "get_page", return_value=PageInfo(1, 2, 2, "/link/to/ancestor")
)
def test_get_parent_page_ancestor(get_page_mock):
    converter = ConfluenceConverter(
        "tests/testfiles/basic.md",
        "default",
        None,
        "orgname",
        True,
        "username",
        "spacekey",
        "apikey",
        "ancestortitle",
        2,
    )

    parent_page_id = converter.get_parent_page()
    assert parent_page_id == 1
    get_page_mock.assert_called_once_with("ancestortitle")


@patch.object(ConfluenceApiClient, "get_page", return_value=PageInfo(0, 0, 0, ""))
def test_get_parent_page_missing_ancestor(get_page_mock, caplog):
    with caplog.at_level(logging.ERROR):
        converter = ConfluenceConverter(
            "tests/testfiles/basic.md",
            "default",
            None,
            "orgname",
            True,
            "username",
            "spacekey",
            "apikey",
            "ancestortitle",
            2,
        )

        parent_page_id = converter.get_parent_page()

    assert parent_page_id == 0
    get_page_mock.assert_called_once_with("ancestortitle")
    assert len(caplog.records) == 1
    assert (
        "Error: Parent page does not exist: ancestortitle" == caplog.records[0].message
    )
