"""
Module huấn luyện LSTM dự báo giá sản phẩm theo từng product_id + platform.
Có thể import để tái sử dụng hoặc chạy trực tiếp để thử nghiệm nhanh.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, Dataset


class PriceLSTM(nn.Module):
    """Mạng LSTM đơn giản dự báo giá dựa trên chuỗi thời gian."""

    def __init__(self, num_features: int, hidden_size: int = 64, num_layers: int = 1) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=num_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return out


def create_windows(data_scaled: np.ndarray, seq_len: int) -> Tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for idx in range(len(data_scaled) - seq_len):
        window = data_scaled[idx : idx + seq_len]
        target_price = data_scaled[idx + seq_len][0]
        X.append(window)
        y.append(target_price)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


class PriceDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray) -> None:
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


def build_dataloaders(
    data_scaled: np.ndarray,
    seq_len: int,
    batch_size: int,
) -> Tuple[DataLoader, DataLoader]:
    X, y = create_windows(data_scaled, seq_len)
    if len(X) < 2:
        raise ValueError("Không đủ dữ liệu để tạo tập train/test. Hãy giảm seq_len hoặc thu thập thêm dữ liệu.")

    train_size = max(1, int(len(X) * 0.8))
    if train_size == len(X):
        train_size -= 1
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    train_ds = PriceDataset(X_train, y_train)
    test_ds = PriceDataset(X_test, y_test)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    return train_loader, test_loader


@dataclass
class ForecastConfig:
    csv_path: str
    product_id: str
    platform: str
    seq_len: int = 365
    batch_size: int = 32
    epochs: int = 30
    lr: float = 1e-3
    feature_cols: Sequence[str] = ("price", "original_price", "is_promo", "stock")
    hidden_size: int = 64
    num_layers: int = 1


@dataclass
class ForecastResult:
    predictions: np.ndarray
    train_loss: float
    test_loss: float
    subset: pd.DataFrame


def _prepare_dataframe(config: ForecastConfig, df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None:
        df = pd.read_csv(config.csv_path)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


def _prepare_series(
    df: pd.DataFrame,
    config: ForecastConfig,
) -> Tuple[pd.DataFrame, np.ndarray, MinMaxScaler]:
    subset = df[(df["product_id"] == config.product_id) & (df["platform"] == config.platform)].copy()
    subset = subset.sort_values("date")
    if len(subset) < config.seq_len + 5:
        raise ValueError("Dữ liệu hơi ít cho sản phẩm/sàn này. Hãy chọn sản phẩm khác hoặc giảm seq_len.")

    feature_df = subset.reindex(columns=config.feature_cols, fill_value=0.0).copy()

    feature_df["stock"] = feature_df["stock"].fillna(0)
    feature_df["original_price"] = feature_df["original_price"].fillna(feature_df["price"])
    feature_df["is_promo"] = feature_df["is_promo"].fillna(0)

    data = feature_df.values.astype(np.float32)
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)
    return subset, data_scaled, scaler


def _fit_model(
    train_loader: DataLoader,
    test_loader: DataLoader,
    num_features: int,
    config: ForecastConfig,
    device: str,
) -> Tuple[PriceLSTM, float, float]:
    model = PriceLSTM(num_features=num_features, hidden_size=config.hidden_size, num_layers=config.num_layers).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)

    last_train_loss, last_test_loss = 0.0, 0.0
    for _ in range(config.epochs):
        model.train()
        running_train_loss = 0.0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device).unsqueeze(1)

            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()

            running_train_loss += loss.item() * xb.size(0)

        last_train_loss = running_train_loss / len(train_loader.dataset)

        model.eval()
        running_test_loss = 0.0
        with torch.no_grad():
            for xb, yb in test_loader:
                xb = xb.to(device)
                yb = yb.to(device).unsqueeze(1)
                pred = model(xb)
                loss = criterion(pred, yb)
                running_test_loss += loss.item() * xb.size(0)
        last_test_loss = running_test_loss / len(test_loader.dataset)

    return model, last_train_loss, last_test_loss


def forecast_future_prices(
    model: PriceLSTM,
    scaler: MinMaxScaler,
    data_scaled: np.ndarray,
    seq_len: int,
    future_days: int,
    device: str,
) -> np.ndarray:
    model.eval()
    last_window = data_scaled[-seq_len:].copy()
    predictions_scaled = []

    with torch.no_grad():
        current_window = last_window
        for _ in range(future_days):
            inp = torch.tensor(current_window, dtype=torch.float32, device=device).unsqueeze(0)
            pred_scaled = model(inp).cpu().numpy()[0, 0]
            predictions_scaled.append(pred_scaled)

            next_row = current_window[-1].copy()
            next_row[0] = pred_scaled
            current_window = np.vstack([current_window[1:], next_row])

    predictions_full = []
    for pred in predictions_scaled:
        row = data_scaled[-1].copy()
        row[0] = pred
        predictions_full.append(row)
    predictions_full = np.array(predictions_full)
    predictions_inversed = scaler.inverse_transform(predictions_full)[:, 0]
    return predictions_inversed


def train_and_predict(
    config: ForecastConfig,
    future_days: int = 30,
    df: Optional[pd.DataFrame] = None,
    device: Optional[str] = None,
) -> ForecastResult:
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    df_prepared = _prepare_dataframe(config, df)
    subset, data_scaled, scaler = _prepare_series(df_prepared, config)
    train_loader, test_loader = build_dataloaders(data_scaled, config.seq_len, config.batch_size)

    model, train_loss, test_loss = _fit_model(
        train_loader,
        test_loader,
        num_features=data_scaled.shape[1],
        config=config,
        device=device,
    )

    predictions = forecast_future_prices(model, scaler, data_scaled, config.seq_len, future_days, device)
    return ForecastResult(predictions=predictions, train_loss=train_loss, test_loss=test_loss, subset=subset)


if __name__ == "__main__":
    DEFAULT_CONFIG = ForecastConfig(
        csv_path=Path(__file__).resolve().parents[1] / "dataset" / "dataset_sense.csv",
        product_id="anker_acc036",
        platform="shopee",
        seq_len=365,
        batch_size=32,
        epochs=30,
    )

    result = train_and_predict(DEFAULT_CONFIG, future_days=30)
    print("Dự báo 30 ngày tới:", result.predictions)
