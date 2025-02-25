# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
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
from tests.op_test import OpTest

paddle.enable_static()


class TestMeanOp(OpTest):
    def set_npu(self):
        self.__class__.use_custom_device = True

    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random((5, 6, 10)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=0)}

    def test_check_output(self):
        self.check_output_with_place(paddle.CustomPlace("npu", 0))

    def test_check_grad(self):
        self.check_grad_with_place(paddle.CustomPlace("npu", 0), ["X"], "Out")


class TestMeanOpFP16(OpTest):
    def set_npu(self):
        self.__class__.use_custom_device = True

    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random((5, 6, 10)).astype("float16")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=0)}

    def test_check_output(self):
        self.check_output_with_place(paddle.CustomPlace("npu", 0))

    def test_check_grad(self):
        self.check_grad_with_place(paddle.CustomPlace("npu", 0), ["X"], "Out")


class TestMeanOpNumel1(OpTest):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random((1, 1, 1)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=0)}


class TestMeanOp5D(TestMeanOp):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random((1, 2, 5, 6, 10)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=0)}


class TestMeanOp6D(TestMeanOp):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random((1, 1, 2, 5, 6, 10)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=0)}


class TestMeanOp8D(TestMeanOp):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {
            "X": np.random.random((1, 3, 1, 2, 1, 4, 3, 10)).astype("float32")
        }
        self.attrs = {"dim": (0, 3)}
        self.outputs = {"Out": self.inputs["X"].mean(axis=(0, 3))}


class Test1DReduce(TestMeanOp):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random(120).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=0)}


class Test2DReduce0(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.attrs = {"dim": [0]}
        self.inputs = {"X": np.random.random((20, 10)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=0)}


class Test2DReduce1(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.attrs = {"dim": [1]}
        self.inputs = {"X": np.random.random((20, 10)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=tuple(self.attrs["dim"]))}


class Test3DReduce0(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.attrs = {"dim": [1]}
        self.inputs = {"X": np.random.random((5, 6, 7)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=tuple(self.attrs["dim"]))}


class Test3DReduce1(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.attrs = {"dim": [2]}
        self.inputs = {"X": np.random.random((5, 6, 7)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=tuple(self.attrs["dim"]))}


class Test3DReduce2(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.attrs = {"dim": [-2]}
        self.inputs = {"X": np.random.random((5, 6, 7)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=tuple(self.attrs["dim"]))}


class Test3DReduce3(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.attrs = {"dim": [1, 2]}
        self.inputs = {"X": np.random.random((5, 6, 7)).astype("float32")}
        self.outputs = {"Out": self.inputs["X"].mean(axis=tuple(self.attrs["dim"]))}


class TestKeepDimReduce(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random((5, 6, 10)).astype("float32")}
        self.attrs = {"dim": [1], "keep_dim": True}
        self.outputs = {
            "Out": self.inputs["X"].mean(
                axis=tuple(self.attrs["dim"]), keepdims=self.attrs["keep_dim"]
            )
        }


class TestKeepDim8DReduce(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {
            "X": np.random.random((2, 5, 3, 2, 2, 3, 4, 2)).astype("float32")
        }
        self.attrs = {"dim": (3, 4, 5), "keep_dim": True}
        self.outputs = {
            "Out": self.inputs["X"].mean(
                axis=tuple(self.attrs["dim"]), keepdims=self.attrs["keep_dim"]
            )
        }


class TestReduceAll(Test1DReduce):
    def setUp(self):
        self.set_npu()
        self.op_type = "reduce_mean"
        self.inputs = {"X": np.random.random((5, 6, 2, 10)).astype("float32")}
        self.attrs = {"reduce_all": True}
        self.outputs = {"Out": self.inputs["X"].mean()}


if __name__ == "__main__":
    unittest.main()
