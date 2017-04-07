namespace WebDNN {
  export class WebGPUHandler {
    static isBrowserSupported: boolean;
    private context: WebGPURenderingContext;
    private commandQueue: WebGPUCommandQueue;
    private pipelineStates: Map<string, WebGPUComputePipelineState>;

    constructor() {
    }

    async init(): Promise<void> {
      // asynchronous operation may be added in future
      if (!WebGPUHandler.isBrowserSupported) {
        throw new Error('This browser does not support WebGPU');
      }
      this.context = <WebGPURenderingContext>(<any>document.createElement('canvas').getContext('webgpu'));//force cast
      this.commandQueue = this.context.createCommandQueue();
      this.pipelineStates = new Map();
    }

    createBuffer(arrayBuffer: ArrayBufferView): WebGPUBuffer {
      return this.context.createBuffer(arrayBuffer);
    }

    loadKernel(librarySource: string, namespace: string = ''): void {
      let library = this.context.createLibrary(librarySource);

      for (let name of library.functionNames) {
        let kernelFunction = library.functionWithName(name);
        let pipelineStates = this.context.createComputePipelineState(kernelFunction);

        this.pipelineStates.set(namespace + '.' + name, pipelineStates);
      }
    }

    createCommandBuffer(): WebGPUCommandBuffer {
      return this.commandQueue.createCommandBuffer();
    }

    getPipelineStateByName(name: string): WebGPUComputePipelineState {
      if (!this.pipelineStates.has(name)) {
        throw TypeError(`Kernel function "${name}" is not loaded.`);
      }

      return this.pipelineStates.get(name);
    }

    executeSinglePipelineState(name: string, threadgroupsPerGrid: WebGPUSize, threadsPerThreadgroup: WebGPUSize, buffers: (WebGPUBuffer | MatrixWebGPU)[]): void {
      let commandBuffer = this.createCommandBuffer();
      let commandEncoder = commandBuffer.createComputeCommandEncoder();

      commandEncoder.setComputePipelineState(this.getPipelineStateByName(name));
      for (let i = 0; i < buffers.length; i++) {
        let buffer = buffers[i];
        let wgbuf: WebGPUBuffer;
        if (buffer instanceof MatrixWebGPU) {
          wgbuf = buffer.webgpuBuffer;
        } else {
          // cannot perform (buffer instanceof WebGPUBuffer) currently
          wgbuf = buffer;
        }

        commandEncoder.setBuffer(wgbuf, 0, i);
      }
      commandEncoder.dispatch(threadgroupsPerGrid, threadsPerThreadgroup);
      commandEncoder.endEncoding();
      commandBuffer.commit();
    }
  }

  WebGPUHandler.isBrowserSupported = 'WebGPURenderingContext' in window;
}

declare interface WebGPURenderingContext {
  createCommandQueue(): WebGPUCommandQueue;
  createBuffer(data: ArrayBufferView): WebGPUBuffer;
  createLibrary(sourceCode: string): WebGPULibrary;
  createComputePipelineState(function_: WebGPUFunction): WebGPUComputePipelineState;
}

declare interface WebGPUFunction {
}

declare interface WebGPULibrary {
  functionNames: string[];
  functionWithName(name: string): WebGPUFunction;
}

declare interface WebGPUBuffer {
  contents: any;
}

declare interface WebGPUSize {
  width: number;
  height: number;
  depth: number;
}

declare interface WebGPUCommandQueue {
  createCommandBuffer(): WebGPUCommandBuffer;
}

declare interface WebGPUCommandBuffer {
  createComputeCommandEncoder(): WebGPUComputeCommandEncoder;
  commit(): void;
  completed(): Promise<void>;
}

declare interface WebGPUCommandEncoder {
  endEncoding(): void;
}

declare interface WebGPUComputeCommandEncoder extends WebGPUCommandEncoder {
  setComputePipelineState(state: WebGPUComputePipelineState): void;
  setBuffer(buffer: WebGPUBuffer, offset: number, index: number): void;
  dispatch(threadgroupsPerGrid: WebGPUSize, threadsPerThreadgroup: WebGPUSize): void;
}

declare interface WebGPUComputePipelineState {
}