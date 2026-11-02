import os
import sys
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from Models.Decision_tree import run_decision_tree
from Models.knn import run_knn
from Models.Linear_regression import run_linear_regression
from Models.Logistic_regression import run_logistic_regression
from Models.preprocessor import clean_fifa_dataframe
from Models.Random_forest import run_random_forest
from Models.Xgboost import run_xgboost

# Đảm bảo hiển thị tiếng Việt có dấu trên Terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "fifa.csv")
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "saved_models")


def main():
    # 1. Đọc và làm sạch dữ liệu (Sửa đường dẫn chuẩn hoa/thường: Data/fifa.csv)
    raw_df = pd.read_csv(DATA_PATH)
    df = clean_fifa_dataframe(raw_df)

    features = [
        "world_cup_year",
        "team1",
        "team2",
        "stage",
        "group",
        "host_country",
        "stadium",
    ]
    x = df[features].copy()

    # 2. BÀI TOÁN HỒI QUY: LINEAR REGRESSION (Dự đoán số bàn thắng của Team 1 & Team 2)
    print("=" * 60)
    print("1. LINEAR REGRESSION (PIPELINE)")
    print("=" * 60)

    y_linear_t1 = df["total_goals_team1"]
    x_train_reg, x_test_reg, y_train_reg, y_test_reg = train_test_split(
        x, y_linear_t1, test_size=0.2, random_state=42
    )
    goal_model_t1 = run_linear_regression(
        x_train_reg, x_test_reg, y_train_reg, y_test_reg
    )

    # Huấn luyện thêm bộ dự đoán bàn thắng cho Team 2 để phục vụ dự đoán tỉ số
    y_linear_t2 = df["total_goals_team2"]
    _, _, y_train_reg2, y_test_reg2 = train_test_split(
        x, y_linear_t2, test_size=0.2, random_state=42
    )
    print("\n--- Dự đoán bàn thắng Đội 2 ---")
    goal_model_t2 = run_linear_regression(
        x_train_reg, x_test_reg, y_train_reg2, y_test_reg2
    )

    # 3. BÀI TOÁN PHÂN LOẠI (CLASSIFICATION: 2 = Thắng, 1 = Hòa, 0 = Thua)
    y_clf = np.select(
        [
            df["total_goals_team1"] > df["total_goals_team2"],  # Thắng
            df["total_goals_team1"] == df["total_goals_team2"],  # Hòa
        ],
        [2, 1],
        default=0,  # Thua
    )

    # Chia tập Train/Test TRƯỚC khi đưa vào Pipeline (OneHotEncoder + StandardScaler) để tránh Data Leakage
    x_train_c, x_test_c, y_train_c, y_test_c = train_test_split(
        x, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )

    trained_models = {}
    model_accuracies = {}
    model_metrics = {}

    model_runners = [
        ("2. LOGISTIC REGRESSION", "Logistic Regression", run_logistic_regression),
        ("3. KNN", "KNN", run_knn),
        ("4. RANDOM FOREST", "Random Forest", run_random_forest),
        ("5. DECISION TREE", "Decision Tree", run_decision_tree),
        ("6. XGBOOST", "XGBoost", run_xgboost),
    ]

    for header, name, runner in model_runners:
        print("\n" + "=" * 60)
        print(header)
        print("=" * 60)
        model_pipe = runner(x_train_c, x_test_c, y_train_c, y_test_c)
        if model_pipe is not None:
            preds = model_pipe.predict(x_test_c)
            acc = float(accuracy_score(y_test_c, preds))
            trained_models[name] = model_pipe
            model_accuracies[name] = acc
            model_metrics[name] = {
                "accuracy": round(acc * 100, 2),
                "precision": round(
                    float(
                        precision_score(
                            y_test_c, preds, average="weighted", zero_division=0
                        )
                    )
                    * 100,
                    2,
                ),
                "recall": round(
                    float(
                        recall_score(
                            y_test_c, preds, average="weighted", zero_division=0
                        )
                    )
                    * 100,
                    2,
                ),
                "f1_score": round(
                    float(
                        f1_score(y_test_c, preds, average="weighted", zero_division=0)
                    )
                    * 100,
                    2,
                ),
            }

    # 4. TỔNG KẾT VÀ TỰ ĐỘNG CHỌN MÔ HÌNH TỐT NHẤT ĐỂ LƯU
    if model_accuracies:
        print("\n" + "=" * 60)
        print("BẢNG TỔNG KẾT ĐỘ CHÍNH XÁC (ACCURACY):")
        print("=" * 60)
        for model_name, acc in sorted(
            model_accuracies.items(), key=lambda item: item[1], reverse=True
        ):
            print(f"- {model_name:22s}: {acc * 100:.2f}%")

        best_model_name = max(model_accuracies, key=model_accuracies.get)
        best_model = trained_models[best_model_name]
        best_acc = model_accuracies[best_model_name] * 100

        os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
        best_model_path = os.path.join(SAVED_MODELS_DIR, "best_model.pkl")
        bundle_path = os.path.join(SAVED_MODELS_DIR, "model_bundle.pkl")

        # Lưu Pipeline mô hình phân loại tốt nhất vào best_model.pkl
        joblib.dump(best_model, best_model_path)

        # Lưu thêm gói bundle đầy đủ (tất cả model + dự đoán bàn thắng + metrics) cho predict.py & UI
        joblib.dump(
            {
                "best_model_name": best_model_name,
                "best_accuracy": round(best_acc, 2),
                "best_model": best_model,
                "all_models": trained_models,
                "goal_model_team1": goal_model_t1,
                "goal_model_team2": goal_model_t2,
                "model_metrics": model_metrics,
                "features": features,
            },
            bundle_path,
        )

        print(
            f"\n🏆 Mô hình tốt nhất được chọn tự động: {best_model_name} ({best_acc:.2f}%)"
        )
        print(f"-> Đã lưu Pipeline mô hình tốt nhất vào: {best_model_path}")
        print(f"-> Đã lưu gói mô hình đầy đủ vào: {bundle_path}")

        # Vẽ biểu đồ so sánh
        plt.figure(figsize=(10, 5.5))
        names = list(model_accuracies.keys())
        accs = [acc * 100 for acc in model_accuracies.values()]
        ax = sns.barplot(
            x=names,
            y=accs,
            hue=names,
            palette="viridis",
            legend=False,
        )
        for idx, val in enumerate(accs):
            ax.text(
                idx,
                val + 1.5,
                f"{val:.2f}%",
                ha="center",
                va="bottom",
                fontweight="bold",
            )
        plt.title(
            f"So sánh độ chính xác giữa các mô hình (Best: {best_model_name})",
            fontsize=13,
            fontweight="bold",
        )
        plt.ylabel("Accuracy (%)")
        plt.ylim(0, 100)

        chart_path = os.path.join(BASE_DIR, "model_comparison.png")
        plt.savefig(chart_path, bbox_inches="tight", dpi=150)
        plt.close()
        print(f"-> Đã xuất biểu đồ so sánh thành công: {chart_path}")


if __name__ == "__main__":
    main()
