// Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "kernels/funcs/npu_funcs.h"
#include "kernels/funcs/npu_op_runner.h"

namespace custom_kernel {

constexpr int64_t kNoPadding = -1;

template <typename T, typename Context>
void EmbeddingKernel(const Context& dev_ctx,
                     const phi::DenseTensor& inputx,
                     const phi::DenseTensor& weight,
                     int64_t padding_idx,
                     phi::DenseTensor* out) {
  auto stream = dev_ctx.stream();

  dev_ctx.template Alloc<T>(out);

  if (padding_idx == kNoPadding) {
    NpuOpRunner runner;
    runner.SetType("GatherV2")
        .AddInput(weight)
        .AddInput(inputx)
        .AddInput(dev_ctx, std::vector<int32_t>{0})
        .AddAttrs({{"batch_dims", 0}})
        .AddOutput(*out);
    runner.Run(stream);
  } else {
    phi::DenseTensor tmp_table_t;
    phi::DenseTensorMeta table_meta = {weight.dtype(), weight.dims()};
    tmp_table_t.set_meta(table_meta);
    dev_ctx.template Alloc<T>(&tmp_table_t);

    T update = static_cast<T>(0);
    padding_idx =
        padding_idx < 0 ? padding_idx + weight.dims()[0] : padding_idx;
    AsyncMemCpyD2D(nullptr,
                   reinterpret_cast<C_Stream>(stream),
                   tmp_table_t.data<T>(),
                   weight.data<T>(),
                   weight.numel() * sizeof(T));
    ACL_CHECK(
        aclrtMemsetAsync(&tmp_table_t.data<T>()[padding_idx * weight.dims()[1]],
                         weight.dims()[1] * sizeof(T),
                         0,
                         weight.dims()[1] * sizeof(T),
                         stream));
    NpuOpRunner runner;
    runner.SetType("GatherV2")
        .AddInput(tmp_table_t)
        .AddInput(inputx)
        .AddInput(dev_ctx, std::vector<int32_t>{0})
        .AddAttrs({{"batch_dims", 0}})
        .AddOutput(*out);
    runner.Run(stream);
  }
}

template <typename T, typename Context>
void EmbeddingGradKernel(const Context& dev_ctx,
                         const phi::DenseTensor& input,
                         const phi::DenseTensor& weight,
                         const phi::DenseTensor& out_grad,
                         int64_t padding_idx,
                         phi::DenseTensor* weight_grad) {
  dev_ctx.template Alloc<T>(weight_grad);

  auto stream = dev_ctx.stream();

  if (input.dtype() == phi::DataType::INT64) {
    phi::DenseTensor input_int32;
    input_int32.Resize(input.dims());
    dev_ctx.template Alloc<int32_t>(&input_int32);
    const auto& cast_runner =
        NpuOpRunner("Cast", {input}, {input_int32}, {{"dst_type", ACL_INT32}});
    cast_runner.Run(stream);
    const auto& runner_scatter =
        NpuOpRunner("EmbeddingDenseGrad",
                    {out_grad, input_int32},
                    {*weight_grad},
                    {{"num_weights", weight_grad->dims()[0]},
                     {"padding_idx", padding_idx}});
    runner_scatter.Run(stream);
  } else {
    const auto& runner_scatter =
        NpuOpRunner("EmbeddingDenseGrad",
                    {out_grad, input},
                    {*weight_grad},
                    {{"num_weights", weight_grad->dims()[0]},
                     {"padding_idx", padding_idx}});
    runner_scatter.Run(stream);
  }
}

}  // namespace custom_kernel

PD_REGISTER_PLUGIN_KERNEL(embedding,
                          npu,
                          ALL_LAYOUT,
                          custom_kernel::EmbeddingKernel,
                          float,
                          int,
                          phi::dtype::float16) {}
PD_REGISTER_PLUGIN_KERNEL(embedding_grad,
                          npu,
                          ALL_LAYOUT,
                          custom_kernel::EmbeddingGradKernel,
                          float,
                          int,
                          phi::dtype::float16) {}
