from .Linear_regression import run_linear_regression
from .Logistic_regression import run_logistic_regression
from .knn import run_knn
from .Random_forest import run_random_forest
from .Decision_tree import run_decision_tree
from .Xgboost import run_xgboost

__all__ = [
    "run_linear_regression",
    "run_logistic_regression",
    "run_knn",
    "run_random_forest",
    "run_decision_tree",
    "run_xgboost",
]
