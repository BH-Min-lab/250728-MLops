# metric.py
# 원하는 metric 함수를 추가하면 됨. 단, mae는 반드시 남겨둘 것

import torch
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# -------------------------
# 회귀용 metric 
# -------------------------

def rmse(output, target):
    with torch.no_grad():
        return torch.sqrt(torch.mean((output - target) ** 2)).item()

def mae(output, target):
    with torch.no_grad():
        return torch.mean(torch.abs(output - target)).item()

def mape(output, target):
    with torch.no_grad():
        return torch.mean(torch.abs((output - target) / target)).item()

# -------------------------
# 분류용 metric (새롭게 추가)
# -------------------------

def accuracy(output, target):
    y_pred = output.detach().cpu().numpy()
    y_true = target.detach().cpu().numpy()
    return accuracy_score(y_true, y_pred)

def precision(output, target, average='macro'):
    y_pred = output.detach().cpu().numpy()
    y_true = target.detach().cpu().numpy()
    return precision_score(y_true, y_pred, average=average, zero_division=0)

def recall(output, target, average='macro'):
    y_pred = output.detach().cpu().numpy()
    y_true = target.detach().cpu().numpy()
    return recall_score(y_true, y_pred, average=average, zero_division=0)

def f1(output, target, average='macro'):
    y_pred = output.detach().cpu().numpy()
    y_true = target.detach().cpu().numpy()
    return f1_score(y_true, y_pred, average=average, zero_division=0)

# -------------------------
# 테스트 코드
# -------------------------
if __name__ == '__main__':
    # 회귀 예제
    output_reg = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float32)
    target_reg = torch.tensor([2, 2, 3, 4, 7], dtype=torch.float32)

    print(f'RMSE : {rmse(output_reg, target_reg):.4f}')
    print(f'MAE  : {mae(output_reg, target_reg):.4f}')
    print(f'MAPE : {mape(output_reg, target_reg) * 100:.2f} %')

    # 분류 예제
    output_cls = torch.tensor([0, 2, 1, 3, 4])  # 예측값
    target_cls = torch.tensor([0, 1, 1, 3, 4])  # 실제값

    print(f'Accuracy  : {accuracy(output_cls, target_cls):.4f}')
    print(f'Precision : {precision(output_cls, target_cls):.4f}')
    print(f'Recall    : {recall(output_cls, target_cls):.4f}')
    print(f'F1 Score  : {f1(output_cls, target_cls):.4f}')
