# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
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
from tests.op import Operator
from paddle.static import Program, program_guard

paddle.enable_static()


class TestScaleOp(OpTest):
    def setUp(self):
        self.op_type = "scale"
        self.place = paddle.CustomPlace("mlu", 0)
        self.__class__.use_custom_device = True
        self.dtype = np.float32
        self.init_dtype_type()
        self.inputs = {"X": np.random.random((10, 10)).astype(self.dtype)}
        self.attrs = {"scale": -2.3}
        self.outputs = {"Out": self.inputs["X"] * self.dtype(self.attrs["scale"])}

    def init_dtype_type(self):
        pass

    def test_check_output(self):
        self.check_output_with_place(self.place)


class TestScaleOpScaleVariable(OpTest):
    def setUp(self):
        self.op_type = "scale"
        self.place = paddle.CustomPlace("mlu", 0)
        self.__class__.use_custom_device = True
        self.dtype = np.float32
        self.init_dtype_type()
        self.scale = -2.3
        self.inputs = {
            "X": np.random.random((10, 10)).astype(self.dtype),
            "ScaleTensor": np.array([self.scale]).astype("float32"),
        }
        self.attrs = {}
        self.outputs = {"Out": self.inputs["X"] * self.dtype(self.scale)}

    def init_dtype_type(self):
        pass

    def test_check_output(self):
        self.check_output_with_place(self.place)


class TestScaleOpSelectedRows(unittest.TestCase):
    def init_dtype_type(self):
        pass

    def set_mlu(self):
        self.place = paddle.CustomPlace("mlu", 0)
        self.__class__.use_custom_device = True

    def check_with_place(self, place, in_name, out_name):
        scope = core.Scope()

        self.dtype = np.float32
        self.init_dtype_type()

        # create and initialize Grad Variable
        in_height = 10
        in_rows = [0, 4, 7]
        in_row_numel = 12
        scale = 2.0

        in_selected_rows = scope.var(in_name).get_selected_rows()
        in_selected_rows.set_height(in_height)
        in_selected_rows.set_rows(in_rows)
        in_array = np.random.random((len(in_rows), in_row_numel)).astype(self.dtype)

        in_tensor = in_selected_rows.get_tensor()
        in_tensor.set(in_array, place)

        # create and initialize Param Variable
        out_selected_rows = scope.var(out_name).get_selected_rows()
        out_tensor = out_selected_rows.get_tensor()
        out_tensor._set_dims(in_tensor._get_dims())

        # create and run sgd operator
        scale_op = Operator("scale", X=in_name, Out=out_name, scale=scale)
        scale_op.run(scope, place)

        # get and compare result
        out_height = out_selected_rows.height()
        out_rows = out_selected_rows.rows()
        result_array = np.array(out_tensor)

        assert (in_array * scale == result_array).all()
        assert in_height == out_height
        assert in_rows == out_rows

    def test_scale_selected_rows(self):
        self.set_mlu()
        places = [core.CPUPlace()]
        if core.is_compiled_with_custom_device("mlu"):
            places.append(core.CustomPlace("mlu", 0))
        for place in places:
            self.check_with_place(place, "in", "out")

    def test_scale_selected_rows_inplace(self):
        self.set_mlu()
        places = [core.CPUPlace()]
        if core.is_compiled_with_custom_device("mlu"):
            places.append(core.CustomPlace("mlu", 0))
        for place in places:
            self.check_with_place(place, "in", "in")


class TestScaleRaiseError(unittest.TestCase):
    def test_errors(self):
        def test_type():
            paddle.scale([10])

        self.assertRaises(TypeError, test_type)


# Add FP16 test
@unittest.skipIf(
    not core.is_compiled_with_custom_device("mlu"), "core is not compiled with MLU"
)
class TestScaleFp16Op(TestScaleOp):
    def init_dtype_type(self):
        self.dtype = np.float16

    def test_check_output(self):
        self.check_output_with_place(self.place, atol=0.002)


class TestScaleApiStatic(unittest.TestCase):
    def _executed_api(self, x, scale=1.0, bias=0.0):
        return paddle.scale(x, scale, bias)

    def test_api(self):
        paddle.enable_static()
        input = np.random.random([2, 25]).astype("float32")
        main_prog = Program()
        with program_guard(main_prog, Program()):
            x = paddle.static.data(name="x", shape=[2, 25], dtype="float32")
            out = self._executed_api(x, scale=2.0, bias=3.0)

        exe = paddle.static.Executor(place=paddle.CPUPlace())
        out = exe.run(main_prog, feed={"x": input}, fetch_list=[out])
        np.testing.assert_array_equal(out[0], input * 2.0 + 3.0)


class TestScaleInplaceApiStatic(TestScaleApiStatic):
    def _executed_api(self, x, scale=1.0, bias=0.0):
        return x.scale_(scale, bias)


class TestScaleApiDygraph(unittest.TestCase):
    def _executed_api(self, x, scale=1.0, bias=0.0):
        return paddle.scale(x, scale, bias)

    def test_api(self):
        paddle.disable_static()
        input = np.random.random([2, 25]).astype("float32")
        x = paddle.to_tensor(input)
        out = self._executed_api(x, scale=2.0, bias=3.0)
        np.testing.assert_array_equal(out.numpy(), input * 2.0 + 3.0)
        paddle.enable_static()


class TestScaleInplaceApiDygraph(TestScaleApiDygraph):
    def _executed_api(self, x, scale=1.0, bias=0.0):
        return x.scale_(scale, bias)


if __name__ == "__main__":
    unittest.main()
