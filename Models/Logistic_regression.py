import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from Models.preprocessor import build_pipeline


def run_logistic_regression(x_train_log, x_test_log, y_train_log, y_test_log):
    # Đóng gói Preprocessor (OneHotEncoder + StandardScaler) + LogisticRegression vào Pipeline
    pipeline = build_pipeline(
        LogisticRegression(max_iter=1000, C=0.5, random_state=42),
        x_train_log,
    )
    pipeline.fit(x_train_log, y_train_log)

    y_predict_log = pipeline.predict(x_test_log)
    accuracy = accuracy_score(y_test_log, y_predict_log)

    print("Logistic Regression Model (Pipeline):")
    print("Tỉ lệ phân phối các lớp trong tập Train:")
    print(pd.Series(y_train_log).value_counts(normalize=True).round(3))
    print(f"Accuracy: {accuracy:.2f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test_log, y_predict_log))
    print("Classification Report:\n")
    print(classification_report(y_test_log, y_predict_log, zero_division=0))

    return pipeline
