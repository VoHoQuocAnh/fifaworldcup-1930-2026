from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from Models.preprocessor import build_pipeline


def run_decision_tree(x_train_K, x_test_K, y_train_K, y_test_K):
    pipeline = build_pipeline(
        DecisionTreeClassifier(max_depth=12, random_state=42),
        x_train_K,
    )
    pipeline.fit(x_train_K, y_train_K)
    pre_tree = pipeline.predict(x_test_K)
    print("Decision Tree Classifier Model (Pipeline):")
    print("Accuracy:", round(accuracy_score(y_test_K, pre_tree), 2))
    print("Confusion Matrix:\n", confusion_matrix(y_test_K, pre_tree))
    print("Classification Report:\n", classification_report(y_test_K, pre_tree, zero_division=0))
    return pipeline
