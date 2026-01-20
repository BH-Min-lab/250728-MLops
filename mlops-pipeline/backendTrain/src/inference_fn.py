import os
import torch
import joblib
import pandas as pd
import dataset as module_data
import model as module_arch

def inference(config, checkpoint_path, output_path="inference_result.csv"):
    dataset = getattr(module_data, config.dataset.type)(
        is_training=False, **config.dataset.args
    )
    (x_wide, x_deep), y = dataset[:][0], dataset[:][1]
    wide_input_dim, deep_input_dim = x_wide.shape[1], x_deep.shape[1]

    encoder = joblib.load(os.path.join(config.dataset.args.data_dir, 'label_encoder.pkl'))
    num_classes = len(encoder.classes_)
    print(f"num_classes from LabelEncoder: {num_classes}")

    model_args = dict(config.wideanddeep_args)
    model_args.update({
        "wide_input_dim": wide_input_dim,
        "deep_input_dim": deep_input_dim,
        "num_classes": num_classes
    })
    model = module_arch.WideAndDeep(**model_args)

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"체크포인트 파일이 존재하지 않습니다: {checkpoint_path}")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model = model.to(device)
    model.eval()

    with torch.no_grad():
        x_wide, x_deep = x_wide.to(device), x_deep.to(device)
        output = model(x_wide, x_deep)
        pred = output.argmax(dim=1).cpu().numpy()
        y_true = y.numpy()

    result_df = pd.DataFrame({
        "SampleID": list(range(len(pred))),
        "Prediction": pred,
        "Prediction_Label": encoder.inverse_transform(pred.astype(int)),
        "GroundTruth": y_true,
        "GroundTruth_Label": encoder.inverse_transform(y_true.astype(int))
    })
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Inference 완료! 결과 저장: {output_path}")