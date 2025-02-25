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

import paddle
import paddle.fluid.core as core
import paddle.fluid as fluid
from paddle.fluid import compiler, Program, program_guard
from op_test import OpTest, convert_uint16_to_float, convert_float_to_uint16
from paddle.fluid.framework import _test_eager_guard

paddle.enable_static()


def get_places(self):
    return [paddle.CustomPlace('custom_cpu', 0)]


OpTest._get_places = get_places


class TestConcatOp(OpTest):
    def setUp(self):
        self.op_type = "concat"
        self.python_api = paddle.concat
        self.dtype = self.get_dtype()
        self.init_test_data()
        self.inputs = {
            'X': [('x0', self.x0), ('x1', self.x1), ('x2', self.x2)]}
        self.attrs = {'axis': self.axis}
        if self.axis < 0:
            self.actual_axis = self.axis + len(self.x0.shape)
            self.actual_axis = self.actual_axis if self.actual_axis > 0 else 0
        else:
            self.actual_axis = self.axis

        self.outputs = {
            'Out': np.concatenate(
                (self.x0, self.x1, self.x2), axis=self.actual_axis
            )
        }

    def get_dtype(self):
        return "float64"

    def test_check_output(self):
        self.check_output(check_eager=True)

    def test_check_grad(self):
        self.check_grad(['x0'], 'Out', check_eager=True)
        self.check_grad(['x1'], 'Out', check_eager=True)
        self.check_grad(['x2'], 'Out', check_eager=True)

    def init_test_data(self):
        self.x0 = np.random.random((5, 1, 4, 5)).astype(self.dtype)
        self.x1 = np.random.random((5, 2, 4, 5)).astype(self.dtype)
        self.x2 = np.random.random((5, 3, 4, 5)).astype(self.dtype)
        self.axis = 1


class TestConcatOp2(TestConcatOp):
    def init_test_data(self):
        self.x0 = np.random.random((2, 3, 4, 5)).astype(self.dtype)
        self.x1 = np.random.random((2, 3, 4, 5)).astype(self.dtype)
        self.x2 = np.random.random((2, 3, 4, 5)).astype(self.dtype)
        self.axis = 1


if __name__ == '__main__':
    unittest.main()
