from typing import List

from graph_builder.backend.webgpu.allocator import MemoryLayout
from graph_builder.backend.webgpu.kernel import Kernel, GPUSize
from graph_builder.backend.webgpu.kernels import util
from graph_builder.backend.webgpu.meta_buffer_injector import MetaBufferInjector
from graph_builder.graph.operators import AxiswiseScale
from graph_builder.graph.operators.attributes import Axis
from graph_builder.graph.variables import attributes as VA

template = """
kernel void %%FUNC_NAME%%(const device float *weight_buffer[[buffer(0)]],
                          device float *data_buffer[[buffer(1)]],
                          const device int * %%META_NAME%% [[buffer(2)]],
                          uint index[[thread_position_in_grid]],
                          uint num_threads[[threads_per_grid]])
{
    const device float *X = data_buffer + %%META_LOAD(axiswise_scale_X_offset)%%;
    device float *Y = data_buffer + %%META_LOAD(axiswise_scale_Y_offset)%%;
    const device float *S = weight_buffer + %%META_LOAD(axiswise_scale_S_offset)%%;
    const int N = %%META_LOAD(axiswise_scale_N)%%;
    const int C = %%META_LOAD(axiswise_scale_C)%%;
  
    for (int gid = index; gid < N; gid += num_threads) {
        int c = gid % C;

        float result = X[gid] * S[c];
        //Y[gid] = %%CHANNELWISE_ATTACHABLE(result, c)%%;
        Y[gid] = result;
    }
}
"""


def axiswise_scale(op: AxiswiseScale,
                   constants_layout: MemoryLayout,
                   variables_layout: MemoryLayout,
                   metabuffer_injector: MetaBufferInjector = None) -> List[Kernel]:
    x = variables_layout[op.inputs["x"]]
    s = constants_layout[op.inputs["s"]]
    y = variables_layout[op.outputs["y"]]

    if metabuffer_injector is None:
        metabuffer_injector = MetaBufferInjector()

    assert x.variable.axis_order == VA.OrderNC \
           or x.variable.axis_order == VA.OrderNHWC \
           or x.variable.axis_order == VA.OrderHWNC, \
        f"[WebGPU] AxiswiseScale operator supports OrderNC, OrderNHWC, and OrderHWNC for data order of input variable. " + \
        f"Actual data order is {x.variable.axis_order}"

    assert y.variable.axis_order == VA.OrderNC \
           or y.variable.axis_order == VA.OrderNHWC \
           or y.variable.axis_order == VA.OrderHWNC, \
        f"[WebGPU] AxiswiseScale operator supports OrderNC, OrderNHWC, and OrderHWNC for data order of output variable. " + \
        f"Actual data order is {y.variable.axis_order}"

    assert op.parameters["axis"] == Axis.C, "[WebGPU] AxiswiseScale supports only channelwise bias."

    metabuffer_injector.register({
        "axiswise_scale_X_offset": x.offset,
        "axiswise_scale_Y_offset": y.offset,
        "axiswise_scale_S_offset": s.offset,
        "axiswise_scale_N": y.variable.size,
        "axiswise_scale_C": y.variable.shape_dict[Axis.C],
    })

    source = metabuffer_injector.inject(template)
    func_name = util.add_canonical_suffix("axiswise_scale", source)
    source = source.replace("%%FUNC_NAME%%", func_name)

    kernel = Kernel(
        {func_name: source},
        func_name,
        GPUSize(8, 1, 1),
        GPUSize(1024, 1, 1),
        metabuffer_injector.generate_buffer()
    )

    return [kernel]
