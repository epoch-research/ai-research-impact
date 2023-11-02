import numpy as np
import pandas as pd
import squigglepy as sq
import statsmodels.api as sm

def fit_linear_regression(x, y):
    """
    Fit an Ordinary Least Squares regression model to the data (x, y).

    Returns the fitted regression model.

    Arguments:
    x -- the independent variable. 2-D array with shape (observations, features).
    y -- the dependent variable. 1-D array with shape (observations,).
    """
    X = sm.add_constant(x)
    ols_model = sm.OLS(y, X)
    est = ols_model.fit()
    return est

def stochastic_regression(x, y, dist):
    """
    Returns a sample of log-linear regression models, accounting for uncertainty 
    in the y-values.
    The relative uncertainty in the y-values is expressed by the distribution 
    `dist`.

    For some number of samples, the y-values are multiplied element-wise by an 
    equal-length vector of values sampled from `dist`.
    Then, a log-linear regression is fitted to the resulting (x, y) values.

    Returns a list of regression models.
    """
    bootstrap_size = 1000
    regression_size = len(y)
    models = list()

    logy = np.log10(y)

    for _ in range(bootstrap_size):
        # Multiply by a random factor to account for uncertainty
        random_multiplier = sq.sample(dist, n=regression_size, lclip=1e-3)    # lclip to avoid non-positive multipliers
        noisy_logy = logy + np.log10(random_multiplier)
        # Fit log-linear regression
        reg_result = fit_linear_regression(x, noisy_logy)
        models.append(reg_result)

    return models

def regression_bootstrap(x, y, rng, data_ci_ratio):
    """
    Performs a bootstrap of the log-linear regression, while accounting for 
    uncertainty in the y-values.

    `data_ci` represents a relative, uniform uncertainty about each data point.
    Each y value is multiplied by a random factor sampled uniformly from this
    range.
    The CI is expressed in log10 space.
    For example, if `data_ci == [-1, 1]`, then in each bootstrap sample, each y
    value is multiplied by a number between 0.1 and 10.
    """
    bootstrap_size = 1000
    regression_size = len(y)
    models = list()

    for i in range(bootstrap_size):
        # Resample the data
        resampled_idxs = rng.choice(np.arange(regression_size), size=regression_size, replace=True)
        x_resample = x[resampled_idxs]
        # Check if the sample is uniform - can't do linear regression, so reject it
        while np.sum(x_resample / x_resample[0]) == len(x_resample):
            resampled_idxs = rng.choice(np.arange(regression_size), size=regression_size, replace=True)
            x_resample = x[resampled_idxs]
        y_resample = y[resampled_idxs]
        # Multiply by a random factor to account for uncertainty in compute
        random_multiplier = 10 ** rng.uniform(data_ci_ratio[0], data_ci_ratio[1], size=regression_size)
        y_resample *= random_multiplier
        # Fit log-linear regression
        reg_result = fit_linear_regression(x_resample, np.log10(y_resample))
        if len(reg_result.params) < 2:
            print(i)
            print(x_resample, y_resample)
        models.append(reg_result)

    return models

def regression_results_bootstrap(models):
    slopes = np.zeros(len(models))
    for i, model in enumerate(models):
        slopes[i] = model.params[1]  # * SECONDS_PER_YEAR
    mean = np.mean(slopes)
    median = np.median(slopes)
    ci = np.percentile(slopes, [5,95])  # 90% CI
    print(f"""Bootstrapped regression result for slope:
        Mean: {mean:.2f}
        Median: {median:.2f}
        90% CI: {ci[0]:.2f} to {ci[1]:.2f}"""
    )
    return dict(mean=mean, median=median, ci=ci)

def predict(model, inputs):
    X = sm.add_constant(inputs)
    log_preds = model.get_prediction(X).summary_frame()
    # log_preds = pd.concat([inputs, log_preds], axis=1)
    return log_preds

def predict_bootstrap(models, x_start, x_end, num_predictions=100):
    log_pred_means = np.zeros((len(models), num_predictions))
    for i, model in enumerate(models):
        log_preds = predict(model, x_start, x_end, num_predictions)
        log_pred_means[i] = log_preds['mean']

    bootstrapped_log_pred_mean = np.mean(log_pred_means, axis=0)
    bootstrapped_log_pred_median = np.median(log_pred_means, axis=0)
    bootstrapped_log_pred_ci = np.percentile(log_pred_means, [5, 95], axis=0)

    return dict(
        mean=bootstrapped_log_pred_mean,
        median=bootstrapped_log_pred_median,
        ci=bootstrapped_log_pred_ci,
    )

def end_date_predictions(preds_bootstrapped):
    print(f"""End date predictions:
        mean: {10**preds_bootstrapped['mean'][-1]:.0e}
        median: {10**preds_bootstrapped['median'][-1]:.0e}
        90% CI: [{10**preds_bootstrapped['ci'][0][-1]:.0e}, {10**preds_bootstrapped['ci'][1][-1]:.0e}]"""
    )

def scale_range_of_predictions(preds_bootstrapped):
    print(f"Scale range of predictions: {10**preds_bootstrapped['mean'][0]:.0e} to {10**preds_bootstrapped['mean'][-1]:.0e}")
