from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from Models.preprocessor import build_pipeline


def run_random_forest(x_train, x_test, y_train, y_test):
    pipeline = build_pipeline(
        RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=2, random_state=42
        ),
        x_train,
    )
    pipeline.fit(x_train, y_train)

    pre_rf = pipeline.predict(x_test)
    print("Random Forest Classifier Model (Pipeline):")
    print("Accuracy:", round(accuracy_score(y_test, pre_rf), 2))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, pre_rf))
    print("Classification Report:\n", classification_report(y_test, pre_rf, zero_division=0))

    return pipeline
