import pytest
from unittest.mock import MagicMock, patch

from dbt.utils.sql_utils import normalize_compiled_sql
from dbt.artifacts.resources.base import FileHash
from dbt.graph import selector_methods
from dbt.graph.selector_methods import check_modified_graph


class MockNode:
    def __init__(self, compiled_code=None, file_hash=None):
        self.compiled_code = compiled_code
        self.file_hash = file_hash if file_hash else FileHash(name='sha256', checksum='default_hash')
    
    def same_compiled(self, other):
        try:
            from dbt.contracts.graph.nodes import CompiledNode
            if hasattr(CompiledNode, 'same_compiled'):
                return CompiledNode.same_compiled(self, other)
        except (ImportError, AttributeError):
            pass
        
        try:
            from dbt.contracts.graph.nodes import ModelNode
            if hasattr(ModelNode, 'same_compiled'):
                return ModelNode.same_compiled(self, other)
        except (ImportError, AttributeError):
            pass
        
        raise AttributeError("same_compiled method not found on any node class")


def create_mock_node(**kwargs):
    compiled_code = kwargs.get('compiled_code', 'select 1')
    file_hash = kwargs.get('file_hash', FileHash(name='sha256', checksum='default_hash'))
    return MockNode(compiled_code=compiled_code, file_hash=file_hash)


def test_normalize_compiled_sql_removes_surrounding_whitespace():
    input_sql = "\n  SELECT 1 FROM table;  \n"
    expected = "SELECT 1 FROM table;"
    assert normalize_compiled_sql(input_sql) == expected


def test_normalize_compiled_sql_reduces_internal_whitespace():
    input_sql = "SELECT\t1 \n FROM\r\ntable"
    expected = "SELECT 1 FROM table"
    assert normalize_compiled_sql(input_sql) == expected


def test_normalize_compiled_sql_handles_complex_whitespace():
    input_sql = "select 1 from a -- comment \n union \r\n select 2 from b"
    expected = "select 1 from a -- comment union select 2 from b"
    assert normalize_compiled_sql(input_sql) == expected


@patch('dbt.utils.sql_utils.normalize_compiled_sql', autospec=True)
def test_same_compiled_calls_normalize(mock_normalize_compiled_sql):
    mock_normalize_compiled_sql.side_effect = lambda x: x if x else None
    node_a = create_mock_node(compiled_code="select 1")
    node_b = create_mock_node(compiled_code="select 1")
    node_a.same_compiled(node_b)
    assert mock_normalize_compiled_sql.called


def test_same_compiled_returns_true_for_whitespace_diffs_end_to_end():
    node_a = create_mock_node(compiled_code="select 1 from A;")
    node_b = create_mock_node(compiled_code="\n\tselect\n  1 from A ; \r\n")
    assert node_a.same_compiled(node_b) is True


def test_same_compiled_returns_false_for_substantive_diffs():
    node_a = create_mock_node(compiled_code="select 1 from A")
    node_b = create_mock_node(compiled_code="select 2 from A")
    assert node_a.same_compiled(node_b) is False


def test_same_compiled_falls_back_when_other_compiled_code_is_none():
    node_a = create_mock_node(
        compiled_code="select 1",
        file_hash=FileHash(name='sha256', checksum='hash_a')
    )
    node_b = create_mock_node(
        compiled_code=None,
        file_hash=FileHash(name='sha256', checksum='hash_b')
    )
    assert node_a.same_compiled(node_b) is False


def test_same_compiled_falls_back_when_self_compiled_code_is_none():
    node_a = create_mock_node(
        compiled_code=None,
        file_hash=FileHash(name='sha256', checksum='hash_a')
    )
    node_b = create_mock_node(
        compiled_code="select 1",
        file_hash=FileHash(name='sha256', checksum='hash_b')
    )
    assert node_a.same_compiled(node_b) is False


def test_modified_compiled_is_registered():
    assert 'modified.compiled' in selector_methods.SELECTOR_METHODS


@patch('dbt.graph.selector_methods.check_modified_graph', autospec=True)
def test_modified_compiled_returns_correct_callable_and_output(mock_check_modified_graph):
    expected_set = {'model.test_pkg.target_model'}
    mock_selector_fn = MagicMock(return_value=expected_set)
    mock_check_modified_graph.return_value = mock_selector_fn

    selector_fn_factory = selector_methods.SELECTOR_METHODS['modified.compiled']
    mock_manifests = MagicMock()
    raw_selection = 'state:modified.compiled'
    resource_type = 'model'

    selector_fn = selector_fn_factory(mock_manifests, raw_selection, resource_type)
    assert callable(selector_fn)
    selected_nodes = selector_fn()
    assert isinstance(selected_nodes, set)
    assert selected_nodes == expected_set
    mock_check_modified_graph.assert_called_once()
    args, kwargs = mock_check_modified_graph.call_args
    assert args[0] == 'same_compiled'
    assert args[1] is mock_manifests
    assert args[2] == raw_selection
    assert args[3] == resource_type
this is the modified test file according to the repo
