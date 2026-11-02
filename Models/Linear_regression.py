from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from Models.preprocessor import build_pipeline


def run_linear_regression(x_train, x_test, y_train, y_test):
    # Sử dụng Ridge (Linear Regression có điều chuẩn L2) trong Pipeline để tránh Overfitting với OneHotEncoder
    pipeline = build_pipeline(Ridge(alpha=15.0, random_state=42), x_train)
    pipeline.fit(x_train, y_train)
    y_predict = pipeline.predict(x_test)
    mse = mean_squared_error(y_test, y_predict)
    r2 = r2_score(y_test, y_predict)
    print("Linear Regression Model (Pipeline):")
    print("Mean Squared Error:", round(mse, 2))
    print("R2 Score:", round(r2, 2))
    return pipeline
