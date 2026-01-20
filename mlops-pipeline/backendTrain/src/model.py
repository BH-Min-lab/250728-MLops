import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from abc import abstractmethod


class BaseModel(nn.Module):
    """
    Base class for all models
    """
    @abstractmethod
    def forward(self):
        """
        Forward pass logic
        """
        raise NotImplementedError

    def __str__(self):
        """
        Model prints with number of trainable parameters
        """
        model_parameters = filter(lambda p: p.requires_grad, self.parameters())
        params = sum([np.prod(p.size()) for p in model_parameters])
        return super().__str__() + '\nTrainable parameters: {}'.format(params)


class WideAndDeep(BaseModel):
    def __init__(
        self,
        wide_input_dim,
        deep_input_dim,
        deep_hidden_units=[128, 64],
        num_classes=16,             # 분류 클래스 수
        dropout_p=0.0,
        batch_norm=False,
        use_softmax=True            # softmax 적용 여부
    ):
        super(WideAndDeep, self).__init__()

        self.use_softmax = use_softmax
        self.num_classes = num_classes

        # Wide part
        self.wide = nn.Linear(wide_input_dim, num_classes)

        # Deep part
        self.deep_layers = nn.ModuleList()
        self.bn_layers = nn.ModuleList() if batch_norm else None
        self.dropout_layers = nn.ModuleList() if dropout_p > 0 else None

        input_dim = deep_input_dim
        for hidden_dim in deep_hidden_units:
            self.deep_layers.append(nn.Linear(input_dim, hidden_dim))
            if batch_norm:
                self.bn_layers.append(nn.LayerNorm(hidden_dim))
            if dropout_p > 0:
                self.dropout_layers.append(nn.Dropout(dropout_p))
            input_dim = hidden_dim

        self.deep_out = nn.Linear(input_dim, num_classes)

    def forward(self, wide_x, deep_x):
        wide_out = self.wide(wide_x)  # (B, C)

        x = deep_x
        for i, layer in enumerate(self.deep_layers):
            x = layer(x)
            # print(f"[DEBUG] after layer {i}, x.shape: {x.shape}")
            x = F.relu(x)
            if self.bn_layers:
                if x.dim() == 1:
                    x = x.unsqueeze(0)  # (features) → (1, features)
                x = self.bn_layers[i](x)

            if self.dropout_layers:
                x = self.dropout_layers[i](x)

        # print(f"[DEBUG] before deep_out, x.shape: {x.shape}")
        deep_out = self.deep_out(x)  # (B, C)

        logits = wide_out + deep_out  # (B, C)

        if self.use_softmax:
            return F.softmax(logits, dim=1)  # 클래스 확률 반환
        else:
            return logits  # loss 계산용 (CrossEntropyLoss는 softmax 포함)


if __name__ == '__main__':
    import torch

    # === Test WideAndDeep ===
    batch_size = 32
    wide_input_dim = 20000
    deep_input_dim = 30000
    num_classes = 16

    model = WideAndDeep(
        wide_input_dim=wide_input_dim,
        deep_input_dim=deep_input_dim,
        deep_hidden_units=[128, 64],
        num_classes=num_classes,
        dropout_p=0.3,
        batch_norm=True,
        use_softmax=True
    )
    print(model)

    wide_x = torch.randn(batch_size, wide_input_dim)
    deep_x = torch.randn(batch_size, deep_input_dim)
    y = model(wide_x, deep_x)
    print(
        f'\n[WideAndDeep] wide_x: {wide_x.shape}, deep_x: {deep_x.shape} => y: {y.shape}')
