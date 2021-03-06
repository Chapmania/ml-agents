import torch
from enum import Enum


class Swish(torch.nn.Module):
    def forward(self, data: torch.Tensor) -> torch.Tensor:
        return torch.mul(data, torch.sigmoid(data))


class Initialization(Enum):
    Zero = 0
    XavierGlorotNormal = 1
    XavierGlorotUniform = 2
    KaimingHeNormal = 3  # also known as Variance scaling
    KaimingHeUniform = 4


_init_methods = {
    Initialization.Zero: torch.zero_,
    Initialization.XavierGlorotNormal: torch.nn.init.xavier_normal_,
    Initialization.XavierGlorotUniform: torch.nn.init.xavier_uniform_,
    Initialization.KaimingHeNormal: torch.nn.init.kaiming_normal_,
    Initialization.KaimingHeUniform: torch.nn.init.kaiming_uniform_,
}


def linear_layer(
    input_size: int,
    output_size: int,
    kernel_init: Initialization = Initialization.XavierGlorotUniform,
    kernel_gain: float = 1.0,
    bias_init: Initialization = Initialization.Zero,
) -> torch.nn.Module:
    """
    Creates a torch.nn.Linear module and initializes its weights.
    :param input_size: The size of the input tensor
    :param output_size: The size of the output tensor
    :param kernel_init: The Initialization to use for the weights of the layer
    :param kernel_gain: The multiplier for the weights of the kernel. Note that in
    TensorFlow, calling variance_scaling with scale 0.01 is equivalent to calling
    KaimingHeNormal with kernel_gain of 0.1
    :param bias_init: The Initialization to use for the weights of the bias layer
    """
    layer = torch.nn.Linear(input_size, output_size)
    _init_methods[kernel_init](layer.weight.data)
    layer.weight.data *= kernel_gain
    _init_methods[bias_init](layer.bias.data)
    return layer


def lstm_layer(
    input_size: int,
    hidden_size: int,
    num_layers: int = 1,
    batch_first: bool = True,
    forget_bias: float = 1.0,
    kernel_init: Initialization = Initialization.XavierGlorotUniform,
    bias_init: Initialization = Initialization.Zero,
) -> torch.nn.Module:
    """
    Creates a torch.nn.LSTM and initializes its weights and biases. Provides a
    forget_bias offset like is done in TensorFlow.
    """
    lstm = torch.nn.LSTM(input_size, hidden_size, num_layers, batch_first=batch_first)
    # Add forget_bias to forget gate bias
    for name, param in lstm.named_parameters():
        # Each weight and bias is a concatenation of 4 matrices
        if "weight" in name:
            for idx in range(4):
                block_size = param.shape[0] // 4
                _init_methods[kernel_init](
                    param.data[idx * block_size : (idx + 1) * block_size]
                )
        if "bias" in name:
            for idx in range(4):
                block_size = param.shape[0] // 4
                _init_methods[bias_init](
                    param.data[idx * block_size : (idx + 1) * block_size]
                )
                if idx == 1:
                    param.data[idx * block_size : (idx + 1) * block_size].add_(
                        forget_bias
                    )
    return lstm
