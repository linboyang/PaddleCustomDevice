#   Copyright (c) 2023 PaddlePaddle Authors. All Rights Reserved.
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

import unittest

import numpy as np
from tests.op_test import OpTest

import paddle
import paddle.fluid as fluid


paddle.enable_static()


class TestFlipOp_API(unittest.TestCase):
    """Test flip api."""

    def test_static_graph(self):
        paddle.enable_static()
        startup_program = fluid.Program()
        train_program = fluid.Program()
        with fluid.program_guard(train_program, startup_program):
            axis = [0]
            input = paddle.static.data(name="input", dtype="float32", shape=[2, 3])
            output = paddle.flip(input, axis)
            output = paddle.flip(output, -1)
            output = output.flip(0)
            place = paddle.CustomPlace("npu", 0)
            exe = fluid.Executor(place)
            exe.run(startup_program)
            img = np.array([[1, 2, 3], [4, 5, 6]]).astype(np.float32)
            res = exe.run(train_program, feed={"input": img}, fetch_list=[output])
            out_np = np.array(res[0])
            out_ref = np.array([[3, 2, 1], [6, 5, 4]]).astype(np.float32)
            self.assertTrue(
                (out_np == out_ref).all(),
                msg="flip output is wrong, out =" + str(out_np),
            )

    def test_dygraph(self):
        paddle.disable_static(paddle.CustomPlace("npu", 0))
        img = np.array([[1, 2, 3], [4, 5, 6]]).astype(np.float32)
        with fluid.dygraph.guard():
            inputs = fluid.dygraph.to_variable(img)
            ret = paddle.flip(inputs, [0])
            ret = ret.flip(0)
            ret = paddle.flip(ret, 1)
            out_ref = np.array([[3, 2, 1], [6, 5, 4]]).astype(np.float32)

            self.assertTrue(
                (ret.numpy() == out_ref).all(),
                msg="flip output is wrong, out =" + str(ret.numpy()),
            )
        paddle.enable_static()


class TestFlipOp(OpTest):
    def setUp(self):
        self.set_npu()
        self.op_type = "flip"
        self.init_test_case()
        self.inputs = {"X": np.random.random(self.in_shape).astype("float64")}
        self.init_attrs()
        self.outputs = {"Out": self.calc_ref_res()}

    def set_npu(self):
        self.__class__.use_custom_device = True
        self.place = paddle.CustomPlace("npu", 0)

    def init_attrs(self):
        self.attrs = {"axis": self.axis}

    def test_check_output(self):
        self.check_output_with_place(self.place)

    def test_check_grad(self):
        pass

    def init_test_case(self):
        self.in_shape = (6, 4, 2, 3)
        self.axis = [0, 1]

    def calc_ref_res(self):
        res = self.inputs["X"]
        if isinstance(self.axis, int):
            return np.flip(res, self.axis)
        for axis in self.axis:
            res = np.flip(res, axis)
        return res


class TestFlipOpAxis1(TestFlipOp):
    def init_test_case(self):
        self.in_shape = (2, 4, 4)
        self.axis = [0]


class TestFlipOpAxis2(TestFlipOp):
    def init_test_case(self):
        self.in_shape = (4, 4, 6, 3)
        self.axis = [0, 2]


class TestFlipOpAxis3(TestFlipOp):
    def init_test_case(self):
        self.in_shape = (4, 3, 1)
        self.axis = [0, 1, 2]


class TestFlipOpAxis4(TestFlipOp):
    def init_test_case(self):
        self.in_shape = (6, 4, 2, 2)
        self.axis = [0, 1, 2, 3]


class TestFlipOpNegAxis(TestFlipOp):
    def init_test_case(self):
        self.in_shape = (6, 4, 2, 2)
        self.axis = [-1]


if __name__ == "__main__":
    paddle.enable_static()
    unittest.main()
