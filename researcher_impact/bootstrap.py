from collections import defaultdict
import numpy as np


def bootstrap_wrapper(func, data, rng, bootstrap_size=1000, mock=False):
    """
    Returns a bootstrap sample of the result of `func` on `data`.
    """
    if mock:
        return [func(data)]
    
    data_size = len(data)
    bootstrap_sample = []

    for _ in range(bootstrap_size):
        # Resample the data
        resampled_idxs = rng.choice(np.arange(data_size), size=data_size, replace=True)
        resampled_data = data[resampled_idxs]
        # Compute result for resampled data
        result = func(resampled_data)
        bootstrap_sample.append(result)

    return bootstrap_sample


def propagate_bootstrap_list(func, bootstrap_sample):
    """
    Propagates the bootstrap sample through `func`.
    """
    propagated_bootstrap_sample = []

    for sample in bootstrap_sample:
        propagated_sample = func(sample)
        propagated_bootstrap_sample.append(propagated_sample)

    return propagated_bootstrap_sample


def propagate_bootstrap_dict(func, bootstrap_sample):
    outputs = [{} for _ in range(len(bootstrap_sample))]
    for i in range(len(bootstrap_sample)):
        for ins, data in bootstrap_sample[i].items():
            outputs[i][ins] = func(data)
    return outputs


def bootstrap_stats(bootstrap_sample, ci=90):
    """
    Returns the mean, median, standard deviation, and confidence interval 
    of the bootstrap sample.

    Assumes the bootstrap sample is a list of dicts mapping keys to an array.
    The reduction is performed at the list level.
    Output: dict mapping keys to a reduced array of values, for each statistic.
    """
    stats = defaultdict(dict)
    for ins in bootstrap_sample[0].keys():
        ins_sample = [bootstrap_sample[i][ins] for i in range(len(bootstrap_sample))]
        stats[ins]['mean'] = np.mean(ins_sample, axis=0)
        stats[ins]['median'] = np.median(ins_sample, axis=0)
        stats[ins]['std'] = np.std(ins_sample, axis=0)
        stats[ins]['ci'] = np.percentile(ins_sample, [50 - ci/2, 50 + ci/2], axis=0)
    return stats


def impute_missing_years(data, all_years):
    """
    Imputes missing years with the mean of the original data.
    """
    mean = data.mean()
    # Reindex the original DataArray to new range of years
    # and fill NaN values with the mean of the original array
    data_imputed = data.reindex(year=all_years, fill_value=mean)
    return data_imputed
