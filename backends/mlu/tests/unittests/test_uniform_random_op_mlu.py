#   Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import unittest
import numpy as np
from tests.op_test import OpTest
import paddle
import paddle.fluid.core as core
import paddle
from tests.op import Operator
import paddle.fluid as fluid

paddle.enable_static()


class TestUniformRandomOp(OpTest):
    def setUp(self):
        self.op_type = "uniform_random"
        self.python_api = paddle.uniform
        self.inputs = {}
        self.init_attrs()
        self.outputs = {"Out": np.zeros((1000, 784)).astype("float32")}

    def init_attrs(self):
        self.attrs = {"shape": [1000, 784], "min": -5.0, "max": 10.0, "seed": 10}
        self.output_hist = output_hist

    def test_check_output(self):
        self.check_output_customized(self.verify_output)

    def verify_output(self, outs):
        hist, prob = self.output_hist(np.array(outs[0]))
        np.testing.assert_allclose(hist, prob, rtol=0, atol=0.01)

    def func_test_check_api(self):
        places = self._get_places()
        for place in places:
            with fluid.dygraph.base.guard(place=place):
                out = self.python_api(
                    self.attrs["shape"],
                    "float32",
                    self.attrs["min"],
                    self.attrs["max"],
                    self.attrs["seed"],
                )


class TestUniformRandomOpSelectedRows(unittest.TestCase):
    def get_places(self):
        places = [core.CPUPlace()]
        if core.is_compiled_with_custom_device("mlu"):
            places.append(paddle.CustomPlace("mlu", 0))
        return places

    def test_check_output(self):
        for place in self.get_places():
            self.check_with_place(place)

    def check_with_place(self, place):
        scope = core.Scope()
        out = scope.var("X").get_selected_rows()
        paddle.seed(10)
        op = Operator(
            "uniform_random", Out="X", shape=[1000, 784], min=-5.0, max=10.0, seed=10
        )
        op.run(scope, place)
        self.assertEqual(out.get_tensor().shape(), [1000, 784])
        hist, prob = output_hist(np.array(out.get_tensor()))
        np.testing.assert_allclose(hist, prob, rtol=0, atol=0.01)


def output_hist(out):
    hist, _ = np.histogram(out, range=(-5, 10))
    hist = hist.astype("float32")
    hist /= float(out.size)
    prob = 0.1 * np.ones((10))
    return hist, prob


class TestMLUUniformRandomOp(OpTest):
    def setUp(self):
        self.set_mlu()
        self.op_type = "uniform_random"
        self.init_dtype()
        self.inputs = {}
        self.init_attrs()
        self.outputs = {"Out": np.zeros((1000, 784)).astype(self.dtype)}

    def init_attrs(self):
        self.attrs = {"shape": [1000, 784], "min": -5.0, "max": 10.0, "seed": 10}
        self.output_hist = output_hist

    def set_mlu(self):
        self.__class__.use_custom_device = True
        self.place = paddle.CustomPlace("mlu", 0)

    def init_dtype(self):
        self.dtype = np.float32

    def test_check_output(self):
        self.check_output_customized(self.verify_output, self.place)

    def verify_output(self, outs):
        hist, prob = self.output_hist(np.array(outs[0]))
        np.testing.assert_allclose(hist, prob, rtol=0, atol=0.01)


class TestMLUUniformRandomOpSelectedRows(unittest.TestCase):
    def get_places(self):
        places = [core.CPUPlace()]
        if core.is_compiled_with_custom_device("mlu"):
            places.append(paddle.CustomPlace("mlu", 0))
        return places

    def test_check_output(self):
        for place in self.get_places():
            self.check_with_place(place)

    def check_with_place(self, place):
        scope = core.Scope()
        out = scope.var("X").get_selected_rows()
        paddle.seed(10)
        op = Operator(
            "uniform_random", Out="X", shape=[1000, 784], min=-5.0, max=10.0, seed=10
        )
        op.run(scope, place)
        self.assertEqual(out.get_tensor().shape(), [1000, 784])
        hist, prob = output_hist(np.array(out.get_tensor()))
        np.testing.assert_allclose(hist, prob, rtol=0, atol=0.01)


if __name__ == "__main__":
    unittest.main()
