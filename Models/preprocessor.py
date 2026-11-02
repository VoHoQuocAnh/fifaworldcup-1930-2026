import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def clean_fifa_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Làm sạch dữ liệu FIFA World Cup:
    - Khôi phục total_goals_team1 & total_goals_team2 từ fulltime_score / extra_time_score
      đối với các dòng bị ghi nhận thiếu (0-0 trong khi fulltime_score > 0).
    - Điền giá trị mặc định cho cột 'group' ở các vòng loại trực tiếp (Knockout).
    """
    df = df.copy()
    if "fulltime_score_team1" in df.columns and "total_goals_team1" in df.columns:
        mask_corrupt = (
            (df["total_goals_team1"] == 0)
            & (df["total_goals_team2"] == 0)
            & (
                (df["fulltime_score_team1"].fillna(0) > 0)
                | (df["fulltime_score_team2"].fillna(0) > 0)
            )
        )
        if "extra_time_score_team1" in df.columns:
            df.loc[mask_corrupt, "total_goals_team1"] = df.loc[
                mask_corrupt, "extra_time_score_team1"
            ].fillna(df.loc[mask_corrupt, "fulltime_score_team1"])
            df.loc[mask_corrupt, "total_goals_team2"] = df.loc[
                mask_corrupt, "extra_time_score_team2"
            ].fillna(df.loc[mask_corrupt, "fulltime_score_team2"])
        else:
            df.loc[mask_corrupt, "total_goals_team1"] = df.loc[
                mask_corrupt, "fulltime_score_team1"
            ]
            df.loc[mask_corrupt, "total_goals_team2"] = df.loc[
                mask_corrupt, "fulltime_score_team2"
            ]

    df = df.dropna(subset=["total_goals_team1", "total_goals_team2"])
    if "group" in df.columns:
        df["group"] = df["group"].fillna("Knockout")
    return df


class FootballFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Transformer trích xuất đặc trưng sức mạnh lịch sử của 2 đội bóng (tỉ lệ thắng, tỉ lệ thua,
    kinh nghiệm thi đấu World Cup, lợi thế sân nhà) chỉ tính trên tập Train (tránh Data Leakage).
    """

    def fit(self, X, y=None):
        self.team_win_rate_ = {}
        self.team_loss_rate_ = {}
        self.team_matches_ = {}
        self.has_raw_cols_ = isinstance(X, pd.DataFrame) and {
            "team1",
            "team2",
        }.issubset(X.columns)

        if self.has_raw_cols_ and y is not None:
            y_arr = np.asarray(y)
            teams = set(X["team1"].dropna()).union(set(X["team2"].dropna()))
            is_clf = set(np.unique(y_arr)).issubset({0, 1, 2})

            for t in teams:
                m1 = (X["team1"] == t).values
                m2 = (X["team2"] == t).values
                total = int(m1.sum() + m2.sum())
                if is_clf:
                    wins = int((m1 & (y_arr == 2)).sum() + (m2 & (y_arr == 0)).sum())
                    losses = int((m1 & (y_arr == 0)).sum() + (m2 & (y_arr == 2)).sum())
                    self.team_win_rate_[t] = (wins + 2.0) / (total + 6.0)
                    self.team_loss_rate_[t] = (losses + 2.0) / (total + 6.0)
                else:
                    # Với bài toán Regression (y là số bàn thắng của team1):
                    # Tính trung bình bàn thắng ghi được khi là team1 và bàn thua khi là team2
                    g_scored = float(y_arr[m1].sum()) if m1.sum() > 0 else 1.2
                    g_conceded = float(y_arr[m2].sum()) if m2.sum() > 0 else 1.2
                    self.team_win_rate_[t] = (g_scored + 3.6) / (int(m1.sum()) + 3.0)
                    self.team_loss_rate_[t] = (g_conceded + 3.6) / (int(m2.sum()) + 3.0)

                self.team_matches_[t] = total
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame) or not getattr(self, "has_raw_cols_", False):
            return X

        X_out = X.copy()
        if "group" in X_out.columns:
            X_out["group"] = X_out["group"].fillna("Knockout").astype(str)

        w1 = X_out["team1"].map(self.team_win_rate_).fillna(0.30)
        w2 = X_out["team2"].map(self.team_win_rate_).fillna(0.30)
        l1 = X_out["team1"].map(self.team_loss_rate_).fillna(0.45)
        l2 = X_out["team2"].map(self.team_loss_rate_).fillna(0.45)
        m1 = X_out["team1"].map(self.team_matches_).fillna(0)
        m2 = X_out["team2"].map(self.team_matches_).fillna(0)

        X_out["team1_win_rate"] = w1
        X_out["team2_win_rate"] = w2
        X_out["team1_loss_rate"] = l1
        X_out["team2_loss_rate"] = l2
        X_out["win_rate_diff"] = w1 - w2
        X_out["loss_rate_diff"] = l1 - l2
        X_out["exp_diff"] = np.log1p(m1) - np.log1p(m2)

        if "host_country" in X_out.columns:
            X_out["is_team1_host"] = [
                1 if str(t) in str(h) else 0
                for t, h in zip(X_out["team1"], X_out["host_country"])
            ]
            X_out["is_team2_host"] = [
                1 if str(t) in str(h) else 0
                for t, h in zip(X_out["team2"], X_out["host_country"])
            ]
        return X_out


def build_pipeline(estimator, x_sample: pd.DataFrame) -> Pipeline:
    """
    Đóng gói Pipeline hoàn chỉnh gồm:
      1. FootballFeatureEngineer (trích xuất đặc trưng thống kê đội bóng)
      2. ColumnTransformer (StandardScaler cho cột số + OneHotEncoder cho cột phân loại)
      3. Estimator (Mô hình học máy)
    """
    has_raw = isinstance(x_sample, pd.DataFrame) and {"team1", "team2"}.issubset(
        x_sample.columns
    )

    if has_raw:
        num_cols = [
            "world_cup_year",
            "team1_win_rate",
            "team2_win_rate",
            "team1_loss_rate",
            "team2_loss_rate",
            "win_rate_diff",
            "loss_rate_diff",
            "exp_diff",
            "is_team1_host",
            "is_team2_host",
        ]
        cat_cols = ["team1", "team2", "stage", "group", "host_country", "stadium"]

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "num",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    num_cols,
                ),
                (
                    "cat",
                    Pipeline(
                        [
                            (
                                "imputer",
                                SimpleImputer(strategy="constant", fill_value="Unknown"),
                            ),
                            (
                                "ohe",
                                OneHotEncoder(
                                    handle_unknown="ignore", sparse_output=False
                                ),
                            ),
                        ]
                    ),
                    cat_cols,
                ),
            ],
            remainder="drop",
        )
        return Pipeline(
            [
                ("feature_engineer", FootballFeatureEngineer()),
                ("preprocessor", preprocessor),
                ("model", estimator),
            ]
        )
    else:
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", estimator),
            ]
        )
