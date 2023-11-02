import numpy as np
import xarray as xr

def printe(x, digits=None):
    if digits is None:
        print(f"{x:e}")
    else:
        print(f"{x:.{digits}e}")

def dict_to_dataarray(d:dict, dim:str, val_fn=lambda x: x):
    arr = xr.DataArray(np.zeros(len(d)), coords={dim: sorted(d.keys())})
    for key, val in d.items():
        arr.loc[key] = val_fn(val)
    return arr

def dicts_to_dataarrays(d:dict, dim:str, val_fn=lambda x: x):
    return {key: dict_to_dataarray(val, dim, val_fn) for key, val in d.items()}
