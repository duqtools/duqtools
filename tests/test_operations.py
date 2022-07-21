from duqtools.operations import Operation, op_queue


def test_touch_operation(tmp_path):
    test_file = tmp_path / 'test'

    action = test_file.touch
    operation = Operation(action=action, description='touching test file')
    op_queue.put(operation)

    assert (not test_file.exists())

    op_queue.apply()

    assert (test_file.exists())


def test_multiple_operation(tmp_path):
    test_file = tmp_path / 'test'
    test_file2 = tmp_path / 'test2'

    op_queue.put(
        Operation(action=test_file.touch, description='touching test file'))
    op_queue.put(
        Operation(action=test_file2.touch, description='touching test file2'))

    assert (not test_file.exists())
    assert (not test_file2.exists())
    op_queue.apply()
    assert (test_file.exists())
    assert (not test_file2.exists())
    op_queue.apply()
    assert (test_file.exists())
    assert (test_file2.exists())


def test_operation_description(tmp_path):
    test_file = tmp_path / 'test'

    op_queue.put(
        Operation(action=test_file.touch, description='touching test file'))

    assert (not test_file.exists())
    op = op_queue.apply()
    assert (op.description == 'touching test file')


def test_operation_apply_all(tmp_path):
    test_file = tmp_path / 'test'
    test_file2 = tmp_path / 'test2'

    op_queue.put(
        Operation(action=test_file.touch, description='touching test file'))
    op_queue.put(
        Operation(action=test_file2.touch, description='touching test file2'))

    assert (not test_file.exists())
    assert (not test_file2.exists())
    op_queue.apply_all()
    assert (test_file.exists())
    assert (test_file2.exists())
