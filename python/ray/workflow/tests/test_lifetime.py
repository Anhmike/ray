import os
import ray
import time
import pytest
from ray._private.test_utils import (
    run_string_as_driver_nonblocking,
    run_string_as_driver,
)
from ray.tests.conftest import *  # noqa
from ray import workflow
from unittest.mock import patch

driver_script = """
import time
import ray
from ray import workflow


@ray.remote
def foo(x):
    time.sleep(1)
    if x < 20:
        return workflow.continuation(foo.bind(x + 1))
    else:
        return 20


if __name__ == "__main__":
    ray.init(storage="{}")
    output = workflow.create(foo.bind(0)).run_async(workflow_id="driver_terminated")
    time.sleep({})
"""


def test_workflow_lifetime_1(workflow_start_cluster):
    # Case 1: driver exits normally
    address, storage_uri = workflow_start_cluster
    with patch.dict(os.environ, {"RAY_ADDRESS": address}):
        ray.init(storage=storage_uri)
        run_string_as_driver(driver_script.format(storage_uri, 5))
        output = workflow.get_output("driver_terminated")
        assert ray.get(output) == 20


def test_workflow_lifetime_2(workflow_start_cluster):
    # Case 2: driver terminated
    address, storage_uri = workflow_start_cluster
    with patch.dict(os.environ, {"RAY_ADDRESS": address}):
        ray.init(storage=storage_uri)
        proc = run_string_as_driver_nonblocking(driver_script.format(storage_uri, 100))
        time.sleep(10)
        proc.kill()
        time.sleep(1)
        output = workflow.get_output("driver_terminated")
        assert ray.get(output) == 20


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
