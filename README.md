# demo_vol_tuning
Understanding how the amount of data fed to a GARCH model influences its results

To run the exercise detailed in the accompanying post, navigate to the project directory and execute:
$ python -m exercise.comparison

Notes:
If using python3, may have to edit pyper.py line 233 to the following:
        tps = isinstance(obj0, basestring) and [str] or isinstance(obj0, bool) and [bool] or num_types
