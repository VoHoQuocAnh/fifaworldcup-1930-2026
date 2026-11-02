from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from Models.preprocessor import build_pipeline


def run_knn(x_train, x_test, y_train, y_test):
    # Đóng gói Preprocessor (OneHotEncoder + StandardScaler) + KNN vào 1 Pipeline
    pipeline = build_pipeline(KNeighborsClassifier(n_neighbors=9), x_train)

    pipeline.fit(x_train, y_train)
    pre_knn = pipeline.predict(x_test)
    acc = accuracy_score(y_test, pre_knn)

    print("KNN Model (Pipeline):")
    print("Accuracy:", round(acc, 2))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, pre_knn))
    print("Classification Report:\n", classification_report(y_test, pre_knn, zero_division=0))

    return pipeline
