# 配置文件
基于DeepVAC规范的PyTorch项目，可以通过在config.py中添加一些配置项来自动实现特定的功能。

这些配置的作用范围有三种：
- 仅适用于train.py，也就是在train.py执行的时候生效；
- 仅适用于test.py，也就是在test.py执行的时候生效；
- 适用于train.py和test.py，也就是train.py、test.py执行的时候都生效。

### 通用配置 (适用于train.py和test.py)
```python
#单卡训练和测试所使用的device，多卡请开启Deepvac的DDP功能
config.train.device = "cuda"
#是否禁用git branch约束
config.train.disable_git = False
#模型输出和加载所使用的路径，非必要不要改动
config.train.output_dir = "output"
#日志输出的目录，非必要不要改动
config.train.log_dir = "log"
#每多少次迭代打印一次训练日志
config.train.log_every = 10

#用于训练时，加载预训练模型。注意不是checkpoint，可参考 config.train.checkpoint_suffix
#用于测试时，加载测试模型。
config.train.model_path = '/root/.cache/torch/hub/checkpoints/resnet50-19c8e357.pth'

#initNetWithCode()定义的网络如果和权重文件里的parameter name不一致，而在结构上一致，
#从逻辑上来说本应该能加载权重文件，但因为name不匹配而会失败。
#可以开启model_reinterpret_cast来解决此问题。这就带来了此开关的2个使用场景：
#场景1：对原官方开源网络的代码进行deepvac标准化后，为了仍然能够加载原官方预训练模型，可以开启此开关。
#场景2：也可以通过开启此开关，然后加载原官方的预训练模型到deepvac化后的网络，来进行重构正确性的检查。
config.train.model_reinterpret_cast = False
```
### Dataloader (适用于train.py和test.py)
```python
#Dataloader的线程数
config.train.num_workers = 3
#dataloader的collate_fn参数
config.train.collate_fn = None
#MyTrainDataset为Dataset的子类
config.train.train_dataset = MyTrainDataset(config.train)
config.train.train_loader = torch.utils.data.DataLoader(
    config.train.train_dataset,
    batch_size=config.train.batch_size,
    num_workers=config.train.num_workers,
    shuffle= True,
    collate_fn=config.train.collate_fn
)
#MyValDataset为Dataset的子类
config.train.val_dataset = MyValDataset(config.train)
config.train.val_loader = torch.utils.data.DataLoader(config.train.val_dataset, batch_size=1, pin_memory=False)

#MyTestDataset为Dataset的子类
config.train.test_dataset = MyTestDataset(config.train)
config.train.test_loader = torch.utils.data.DataLoader(config.train.test_dataset, batch_size=1, pin_memory=False)
```
### 优化器 (仅适用于train.py)
```python
config.train.optimizer = optim.SGD(config.train.net.parameters(),lr=0.01,momentum=0.9,weight_decay=None,nesterov=False)
config.train.scheduler = torch.optim.lr_scheduler.MultiStepLR(config.train.optimizer, [2,4,6,8,10], 0.27030)
```

### 训练 (仅适用于train.py)
```python
#网络定义
config.train.net = MyNet()
#损失函数
config.train.criterion = MyCriterion()

#训练的batch size
config.train.train.batch_size = 128
#训练多少个Epoch
config.train.epoch_num = 30
#一个Epoch中保存多少次模型和Checkpoint文件
config.train.save_num = 5

#checkpoint_suffix一旦配置，则启动train.py的时候将加载output/<git_branch>/checkpoint:<checkpoint_suffix>
#不配置或者配置为空字符串，表明从头开始训练。
#train.py下，该配置会覆盖config.model_path。
config.train.checkpoint_suffix = '2020-09-01-17-37_acc:0.9682857142857143_epoch:10_step:6146_lr:0.00011543040395151496.pth'
```

### 验证 (仅适用于train.py)
```python
#验证时所用的batch size
config.train.val.batch_size = None
```

### 测试 (仅适用于test.py)
```python
#使用jit加载模型，script、trace后的模型如果在python中加载，必须使用这个开关。
#test.py下，开启此开关后将会忽略config.model_path
config.train.jit_model_path = '/root/.cache/torch/hub/checkpoints/resnet50-19c8e357.pt'

#测试时所用的batch size
config.train.test.batch_size = None
```

### DDP（分布式训练，仅适用于train.py）
要启用分布式训练，需要确保2点：
- config.py需要进行如下配置：
```python
#dist_url，单机多卡无需改动，多机训练一定要修改
config.train.dist_url = "tcp://localhost:27030"

#rank的数量，一定要修改
config.train.world_size = 3
```
- 命令行传递如下两个参数(不在config.py中配置)：
```bash
#从0开始
--rank <rank_idx>
#从0开始
--gpu <gpu_idx>
```
上述的配置表明我们将使用3个进程在3个CUDA设备上进行训练。配置完成后，我们在命令行手工启动3个进程：
```bash
python train.py --rank 0 --gpu 0
python train.py --rank 1 --gpu 1
python train.py --rank 2 --gpu 2
```
### 启用EMA (仅适用于train.py)
EMA: exponential moving average，指数滑动平均。滑动平均可以使模型更健壮。采用梯度下降算法训练神经网络时，使用滑动平均在很多应用中都可以在一定程度上提高最终模型的表现。

要开启EMA，需要设置如下配置：
```python
config.train.ema = True

#可选配置，默认为lambda x: 0.9999 * (1 - math.exp(-x / 2000))
config.train.ema_decay = <lambda function>
```
### 启用tensorboard服务 (仅适用于train.py)
Deepvac会自动在log/<git_branch>/下写入tensorboard数据，如果需要在线可视化，则还需要如下配置：
```python
# 如果不配置，则不启用tensorboard服务
config.train.tensorboard_port = "6007"
# 不配置的话为0.0.0.0，如非必要则无需改变
config.train.tensorboard_ip = None
```

### 输出TorchScript（适用于train.py和test.py）
如果要转换PyTorch模型到TorchScript，你需要设置如下的配置：
```python
#通过script的方式将pytorch训练的模型编译为TorchScript模型
config.train.script_model_dir = <your_script_model_dir_only4smoketest>

#通过trace的方式将pytorch训练的模型转换为TorchScript模型
config.train.trace_model_dir = <your_trace_model_dir_only4smoketest>
```
注意：
- 在train.py下，配置上面的参数后，Deepvac会在第一次迭代的时候，进行冒烟测试。也就是测试网络是否能够成功转换为TorchScript。之后，在每次保存PyTorch模型的时候，会同时保存TorchScript；
- 在train.py下，<your_trace_model_dir_only4smoketest> 仅用于冒烟测试，真正的存储目录为PyTorch模型所在的目录，无需用户额外指定。
- 在test.py下，<your_trace_model_dir_only4smoketest> 为TorchScript模型输出路径。

### 输出ONNX模型（适用于train.py和test.py）
如果要转换PyTorch模型到ONNX，你需要设置如下的配置：
```python
#输出config.onnx_model_dir
config.train.onnx_model_dir = <your_onnx_model_dir_only4smoketest>
#默认onnx版本，默认是9。当模型使用了上采样等操作时，建议将它设置为11或以上
config.train.onnx_version = 9
config.train.onnx_input_names = ["input"]
config.train.onnx_output_names = ["output"]
#当模型的支持动态输入的时候，需要设置，input和output需要和上面2行设置的name对应。
config.train.onnx_dynamic_ax = {
            'input': {
                2: 'image_height',
                3: 'image_width'
                },
            'output':{
                2: 'image_height',
                3: 'image_width'
            }
        }
```
注意：
- 在train.py下，配置上面的参数后，Deepvac会在第一次迭代的时候，进行冒烟测试。也就是测试网络是否能够成功转换为ONNX。之后，在每次保存PyTorch模型的时候，会同时保存ONNX。
- 在train.py下，<your_onnx_model_dir_only4smoketest> 仅用于冒烟测试，真正的存储目录为PyTorch模型所在的目录，无需用户额外指定。
- 在test.py下，<your_onnx_model_dir_only4smoketest> 为ONNX模型输出路径。

### 输出NCNN模型（适用于train.py和test.py）
如果要转换PyTorch模型到NCNN，你需要设置如下的配置：
```python
# NCNN的文件路径, ncnn.arch ncnn.bin
config.train.ncnn_model_dir = <your_ncnn_model_dir_only4smoketest>
# onnx2ncnn可执行文件的路径，https://github.com/Tencent/ncnn/wiki/how-to-build#build-for-linux-x86
config.train.onnx2ncnn = <your_onnx2ncnn_executable_file>
```
注意：
- 在train.py下，配置上面的参数后，Deepvac会在第一次迭代的时候，进行冒烟测试。也就是测试网络是否能够成功转换为NCNN。之后，在每次保存PyTorch模型的时候，会同时保存NCNN。
- 在train.py下，<your_ncnn_model_dir_only4smoketest> 仅用于冒烟测试，真正的存储目录为PyTorch模型所在的目录，无需用户额外指定。
- 在test.py下，<your_ncnn_model_dir_only4smoketest> 为NCNN模型输出路径。

### 输出CoreML（适用于train.py和test.py）
如果要转换PyTorch模型到CoreML，你需要设置如下的配置：
```python
config.train.coreml_model_dir = <your_coreml_model_dir_only4smoketest>
#trace_model_dir和script_model_dir二选一，必须打开其中之一
config.train.trace_model_dir = trace.pt
config.train.script_model_dir = script.pt

#该配置要么设置为'image'或'tensor',要么不设置，此时相当于'tensor'
config.train.coreml_input_type = None

#以下配置只有当coreml_input_type = 'image'时才需要配置
config.train.coreml_scale = 1.0 / (0.226 * 255.0)
config.train.coreml_color_layout = 'BGR'
config.train.coreml_blue_bias = -0.406 / 0.226
config.train.coreml_green_bias = -0.456 / 0.226
config.train.coreml_red_bias = -0.485 / 0.226

#可以不设置
config.train.coreml_minimum_deployment_target = coremltools.target.iOS13
#如果类别多，使用代码初始化这个值
config.train.coreml_classfier_config = ["cls1","cls2","cls3","cls4","cls5","cls6"]
```
注意：
- 在train.py下，配置上面的参数后，Deepvac会在第一次迭代的时候，进行冒烟测试，也就是测试网络是否能够成功转换为CoreML。之后，在每次保存PyTorch模型的时候，会同时保存CoreML。
- 在train.py下，<your_coreml_model_dir_only4smoketest> 仅用于冒烟测试，真正的存储目录为PyTorch模型所在的目录，无需用户额外指定。
- 在test.py下，<your_coreml_model_dir_only4smoketest> 为CoreML模型输出路径。

### 输出TensorRT（适用于train.py和test.py）
如果要转换PyTorch模型到TensorRT，你需要设置如下的配置：
```python
config.train.onnx_model_dir = <your_onnx_model_dir_only4smoketest>
config.train.trt_model_dir = <your_trt_model_dir_only4smoketest>

# 动态输入下的onnx配置和TensorRT配置
# 需要配置onnx需要支持的动态输入/动态输出的数据维度, 可以参考上面的 输出ONNX模型
config.train.onnx_input_names = ["input"]
config.train.onnx_output_names = ["output"]
config.train.onnx_dynamic_ax = {
            'input': {
                0: 'batch_size',
                1: 'image_channel',
                2: 'image_height',
                3: 'image_width'
                },
            'output':{
                0: 'batch_size',
                1: 'output_channel',
                2: 'output_height',
                3: 'output_width'
        }
    }
# 需要配置图片的最小输入尺寸，最大输入尺寸和最优尺寸
config.train.trt_input_min_dims = (1, 3, 1, 1)
config.train.trt_input_opt_dims = (1, 3, 640, 640)
config.train.trt_input_max_dims = (1, 3, 2000, 2000)

```
注意：
- TensorRT模型的转换依赖于onnx，因此需要首先将模型转换为onnx。
- 在train.py下，配置上面的参数后，Deepvac会在第一次迭代的时候，进行冒烟测试，也就是测试网络是否能够成功转换为TensorRT。之后，在每次保存PyTorch模型的时候，会同时保存TensorRT。
- 在train.py下，<your_trt_model_dir_only4smoketest> 仅用于冒烟测试，真正的存储目录为PyTorch模型所在的目录，无需用户额外指定。
- 在test.py下，<your_trt_model_dir_only4smoketest> 为TensorRT模型输出路径。


### 启用自动混合精度训练（仅适用于train.py）
如果要开启自动混合精度训练（AMP），你只需要设置如下配置即可：
```python
config.train.amp = True
```
详情参考[PyTorch的自动混合精度](https://zhuanlan.zhihu.com/p/165152789)。

### 启用量化
目前PyTorch有三种量化方式，详情参考[PyTorch的量化](https://zhuanlan.zhihu.com/p/299108528):
- 动态量化
- 静态量化
- 量化感知训练

一次训练任务中只能开启一种。

#### 动态量化（适用于train.py和test.py）
要开启动态量化，你需要设置如下的配置：
```python
config.train.dynamic_quantize_dir = <your_quantize_model_output_dir_only4smoketest>
```
注意：开启动态量化需要首先开启trace_model_dir或者script_model_dir或者都开启。

#### 静态量化（适用于train.py和test.py）
要开启静态量化，你需要设置如下配置：
```python
config.train.static_quantize_dir = <your_quantize_model_output_dir_only4smoketest>

# backend 为可选，默认为fbgemm
config.train.quantize_backend = <'fbgemm' | 'qnnpack'>
```
注意：开启静态量化需要首先开启trace_model_dir或者script_model_dir或者都开启。

#### 量化感知训练(QAT，仅适用于train.py)
开启QAT后，整个训练任务的self.net就会转变为量化模型。也即所有trace、script、onnx、ncnn、coreml、amp等作用的对象已经变为量化感知模型。
要开启QAT，你需要设置如下配置：
```python
config.train.qat_dir = <your_quantize_model_output_dir_only4smoketest>

# backend 为可选，默认为fbgemm
config.train.quantize_backend = <'fbgemm' | 'qnnpack'>
```

注意：
- **由于上游PyTorch相关功能的缺失，该功能还不完善。Deepvac已经删除了此开关，将在之后的版本中择机加回来。**
- 在train.py下，配置上面的参数后，Deepvac会在第一次迭代的时候，进行冒烟测试。也就是测试网络是否能够量化成功。之后，在每次保存PyTorch模型的时候，会同时保存量化模型（QAT有点特殊，直接替换了之前的模型）。
- 在train.py下，<your_quantize_model_output_dir_only4smoketest> 仅用于冒烟测试，真正的存储目录为PyTorch模型所在的目录，无需用户额外指定。
- 在test.py下（如果支持的话），<your_quantize_model_output_dir_only4smoketest> 为量化模型输出路径。
