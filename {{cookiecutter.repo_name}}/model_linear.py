"""Linear Model"""
from sklearn.linear_model import Ridge
import joblib
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error
from dask_ml.model_selection import RandomizedSearchCV
import numpy as np
import scipy.stats

from runner import get_runner
import fire


def predict(run):
    cfg = run.cfg
    # Prediction task
    X = np.random.rand(100).reshape(-1, 1)
    linear_model = joblib.load(cfg.linear__model_fn)
    y_predict = linear_model.predict(X)
    np.save(cfg.linear__prediction_fn, y_predict)
    run.log.info(f"Finished prediction: {run.model_id}")


def train_hp(run):
    X = np.random.rand(300).reshape(-1, 1)
    y = 4 * X + np.random.randn(300, 1) * 0.5

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    params = {"alpha": scipy.stats.uniform(0, 2)}
    rs = RandomizedSearchCV(
        Ridge(), params, n_iter=20, scoring='neg_mean_squared_error')
    rs.fit(X_train, y_train)

    train_score = mean_squared_error(y_train, rs.predict(X_train))
    test_score = mean_squared_error(y_test, rs.predict(X_test))

    run.log.info(
        f"Finished hyperparameter search on {run.model_id} test_score: "
        f"{test_score:0.6}, train_score: {train_score:0.6}, "
        f"params: {rs.best_params_}")

    return {"valid": test_score, "train": train_score}


def train(run):
    cfg = run.cfg

    X = np.random.rand(300).reshape(-1, 1)
    y = 4 * X + np.random.randn(300, 1) * 0.5

    linear_model = Ridge(cfg.linear__alpha)
    valid_scores = cross_val_score(
        linear_model, X, y, scoring='neg_mean_squared_error', cv=5)
    valid_score = -np.mean(valid_scores)
    valid_score_std = np.std(valid_scores)

    linear_model.fit(X, y)
    train_score = mean_squared_error(y, linear_model.predict(X))

    joblib.dump(linear_model, cfg.linear__model_fn)

    run.log.info(f"Finished training {run.model_id} val_score: "
                 f"{valid_score:0.6}+/-{valid_score_std:0.6}, "
                 f"train_score: {train_score:0.6}")
    return {"valid": valid_score, "train": train_score}


if __name__ == '__main__':
    r = get_runner("linear", [train, train_hp, predict])
    fire.Fire(r)
