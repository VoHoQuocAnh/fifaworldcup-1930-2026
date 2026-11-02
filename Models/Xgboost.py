import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from Models.preprocessor import build_pipeline


def run_xgboost(x_train, x_test, y_train, y_test):
    pipeline = build_pipeline(
        xgb.XGBClassifier(
            n_estimators=70,
            learning_rate=0.04,
            max_depth=2,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=2.5,
            random_state=42,
            eval_metric="mlogloss",
        ),
        x_train,
    )
    pipeline.fit(x_train, y_train)
    pre_xgb = pipeline.predict(x_test)
    print("XGBoost Classifier Model (Pipeline):")
    print("Accuracy:", round(accuracy_score(y_test, pre_xgb), 2))
    print("Confusion Matrix:\n", confusion_matrix(y_test, pre_xgb))
    print("Classification Report:\n", classification_report(y_test, pre_xgb, zero_division=0))
    return pipeline
