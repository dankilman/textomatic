from tests.framework import with_cases, run_and_assert_process


@with_cases("process_cmd")
def test_process_cmd(case):
    run_and_assert_process(case)


@with_cases("types")
def test_types(case):
    run_and_assert_process(case)


@with_cases("structure")
def test_structure(case):
    run_and_assert_process(case)


@with_cases("input_csv")
def test_input_csv(case):
    run_and_assert_process(case)


@with_cases("input_jsonlines")
def test_input_jsonlines(case):
    run_and_assert_process(case)


@with_cases("input_shell")
def test_input_shell(case):
    run_and_assert_process(case)


@with_cases("outputs")
def test_outputs(case):
    run_and_assert_process(case)


# @with_cases('single')
# def test_single(case):
#     run_and_assert_process(case)
