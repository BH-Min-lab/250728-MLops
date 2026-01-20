import os
import torch
from torch.utils.data import DataLoader
from utils import fix_seed, MetricTracker
import dataset as module_data
import model as module_arch
import metric as module_metric
import datetime
import mlflow
import mlflow.pytorch


def train(config, logger):
    fix_seed(config.seed)

    # MLflow 설정
    mlflow.set_tracking_uri(
        os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    mlflow.set_experiment("mlops_pipeline")

    # MLflow run 시작
    with mlflow.start_run(run_name=f"train_{datetime.datetime.now():%Y%m%d_%H%M%S}"):
        # 하이퍼파라미터 로깅
        mlflow.log_params({
            "model_type": config.model.type,
            "batch_size": config.dataloader.args.batch_size,
            "learning_rate": config.optimizer.args.lr,
            "epochs": config.train.epochs,
            "seed": config.seed,
            "deep_hidden_units": str(config.wideanddeep_args.deep_hidden_units),
            "dropout_p": config.wideanddeep_args.dropout_p,
        })

        train_dataset = getattr(module_data, config.dataset.type)(
            is_training=True, **config.dataset.args
        )
        train_dataloader = DataLoader(
            dataset=train_dataset,
            batch_size=config.dataloader.args.batch_size,
            shuffle=config.dataloader.args.shuffle,
            num_workers=config.dataloader.args.num_workers,
            drop_last=True
        )

        (x_wide, x_deep), _ = train_dataset[0]
        wide_input_dim, deep_input_dim = x_wide.shape[0], x_deep.shape[0]
        num_classes = int(train_dataset.y.max().item()) + 1

        # 데이터셋 정보 로깅
        mlflow.log_params({
            "wide_input_dim": wide_input_dim,
            "deep_input_dim": deep_input_dim,
            "num_classes": num_classes,
            "train_samples": len(train_dataset),
        })

        model_type = config.model.type
        if model_type == "WideAndDeep":
            model_args = dict(config.wideanddeep_args)
            model_args.update({
                "wide_input_dim": wide_input_dim,
                "deep_input_dim": deep_input_dim,
                "num_classes": num_classes
            })
            model = module_arch.WideAndDeep(**model_args)
        elif model_type == "MLP":
            model = module_arch.MLP(
                input_size=wide_input_dim + deep_input_dim,
                output_size=num_classes,
                **config.mlp_args
            )
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {model_type}")

        if config.train.resume:
            model.load_state_dict(torch.load(config.train.resume_path))

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)

        # 모델 아키텍처 로깅
        total_params = sum(p.numel()
                           for p in model.parameters() if p.requires_grad)
        mlflow.log_param("total_parameters", total_params)

        criterion = getattr(torch.nn, config.loss)().to(device)
        optimizer = getattr(torch.optim, config.optimizer.type)(
            model.parameters(), **config.optimizer.args)
        scheduler = getattr(torch.optim.lr_scheduler, config.lr_scheduler.type)(
            optimizer, **config.lr_scheduler.args)

        metrics = [getattr(module_metric, met) for met in config.metrics]
        tracker = MetricTracker('loss', *config.metrics)

        # 저장 디렉토리 미리 생성
        save_root = os.path.abspath(config.train.save_dir)
        ckpt_dir = os.path.join(save_root, "checkpoints")
        os.makedirs(ckpt_dir, exist_ok=True)
        logger.info(f"Checkpoint directory: {ckpt_dir}")

        best_loss = float('inf')
        best_accuracy = 0.0

        for epoch in range(1, config.train.epochs + 1):
            model.train()
            tracker.reset()

            for batch_idx, ((x_wide, x_deep), target) in enumerate(train_dataloader):
                x_wide, x_deep, target = x_wide.to(
                    device), x_deep.to(device), target.to(device)
                output = model(torch.cat(
                    [x_wide, x_deep], dim=1)) if model_type == "MLP" else model(x_wide, x_deep)
                loss = criterion(output, target.view(-1).long())

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                tracker.update('loss', loss.item())
                for met in metrics:
                    pred = output.argmax(dim=1)
                    tracker.update(met.__name__, met(
                        pred, target.view(-1).long()))

            scheduler.step()

            # Epoch 메트릭 계산
            epoch_metrics = tracker.result()

            # MLflow에 메트릭 로깅
            mlflow.log_metrics({
                "train_loss": epoch_metrics['loss'],
                "train_accuracy": epoch_metrics.get('accuracy', 0),
                "train_f1": epoch_metrics.get('f1', 0),
                "learning_rate": optimizer.param_groups[0]['lr'],
            }, step=epoch)

            # Best 메트릭 업데이트
            if epoch_metrics['loss'] < best_loss:
                best_loss = epoch_metrics['loss']
            if epoch_metrics.get('accuracy', 0) > best_accuracy:
                best_accuracy = epoch_metrics.get('accuracy', 0)

            # 로그 출력
            log_msg = f"[Epoch {epoch}/{config.train.epochs}] " + ", ".join(
                f"{k.upper()}: {v:.4f}" for k, v in epoch_metrics.items())
            logger.info(log_msg)

            # 체크포인트 저장
            if epoch % config.train.save_period == 0:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                ckpt_path = os.path.join(ckpt_dir, f"model-e{epoch}-{ts}.pt")

                try:
                    torch.save(model.state_dict(), ckpt_path)
                    logger.info(f"✅ Saved checkpoint: {ckpt_path}")

                    # 파일 존재 확인
                    if os.path.exists(ckpt_path):
                        file_size = os.path.getsize(
                            ckpt_path) / (1024*1024)  # MB
                        logger.info(f"   File size: {file_size:.2f} MB")

                        # MLflow에 체크포인트 아티팩트 로깅
                        mlflow.log_artifact(
                            ckpt_path, artifact_path="checkpoints")
                    else:
                        logger.error(
                            f"❌ Failed to save checkpoint - file not found")
                except Exception as e:
                    logger.error(f"❌ Error saving checkpoint: {e}")

        # 마지막 모델 저장
        final_path = os.path.join(
            ckpt_dir, f"model-final-{datetime.datetime.now():%Y%m%d_%H%M%S}.pt")
        try:
            torch.save(model.state_dict(), final_path)
            logger.info(f"✅ Saved final model: {final_path}")

            # MLflow에 최종 모델 저장
            mlflow.pytorch.log_model(model, "model")
            mlflow.log_artifact(final_path, artifact_path="final_model")

            # Best 메트릭 로깅
            mlflow.log_metrics({
                "best_loss": best_loss,
                "best_accuracy": best_accuracy,
            })

        except Exception as e:
            logger.error(f"❌ Error saving final model: {e}")
