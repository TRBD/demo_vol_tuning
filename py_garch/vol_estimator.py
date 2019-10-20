import pandas as pd
from config import TMP_PATH
import os


class AllDatesVolModelRunParams(object):
    """
    Parameters for running a set of simulations across dates
    model_type: eGARCH, gjrGARCH, csGARCH
    test_dist: std, norm
    n_forecast: a positive integer
    n_sims: a positive integer
    window: a positive integer or -1 for full history
    """
    def __init__(self, model_type, test_dist, n_forecast, n_sims, window):
        self.model_type = model_type
        self.n_forecast = n_forecast
        self.test_dist = test_dist
        self.n_sims = n_sims
        self.window = window

    @classmethod
    def from_series(cls, series):
        """
        Instance an new object from the series data used in caching
        :param series: stored data stored by RVMSingleResultCache.cache_local, retrieved by
            RVMSingleResultCache.check_exists
        :return: new AllDatesVolModelRunParams object
        """
        prefix = series.pop('prefix')
        model_type, test_dist, n_sims, n_forecast, _, _ = prefix.split('_')
        window = series.pop('window')
        return cls(model_type, test_dist, int(n_forecast), int(n_sims), int(window))

    def get_start_end_dates(self, start_point, test_data_set, full_data_set):
        """
        Returns the start and end dates for an input dataset to go into the R script method
        :param start_point: non-negative integer
        :param test_data_set: truncated dataset of price history
        :param full_data_set: full dataset of price history
        :return: input_start_date (Timestamp), input_end_date (Timestamp)
        """
        input_end_date = test_data_set.iloc[start_point].Date
        data_set_preceding = full_data_set.set_index('Date').loc[:input_end_date]
        if self.window > 0:
            input_start_date = data_set_preceding.tail(self.window).index[0]
        else:
            input_start_date = data_set_preceding.index[0]
        return input_start_date, input_end_date

    def __eq__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        is_equal = self.model_type == other.model_type and \
            self.n_forecast == other.n_forecast and \
            self.test_dist == other.test_dist and \
            self.n_sims == other.n_sims and \
            self.window == other.window
        if not is_equal:
            return False
        return True

    def __hash__(self):
        h0 = hash(self.model_type)
        h0 += hash(self.n_forecast)
        h0 += hash(self.test_dist)
        h0 += hash(self.n_sims)
        h0 += hash(self.window)
        return h0


class RVolModelSingleResult(object):
    """
    Holds a single date's result for a given AllDatesVolModelRunParams model run input
    data_start_date: Timestamp
    data_end_date: Timestamp
    params: AllDatesVolModelRunParams

    Attributes:
        quantile0_pct: (float) min simulated value
        quantile25_pct: (float) 25th percentile simulated value
        quantile50_pct: (float) median simulated value
        quantile75_pct: (float) 75th percentile simulated value
        quantile100_pct: (float) max simulated value
        mean_sim_ann: (float) mean simulated value
        vol_realized_ann: (float) relaized n_forecast period vol
        forecast_error: (float) realized less mean_sim_ann
    """
    def __init__(self, data_start_date, data_end_date, params):
        self.data_start_date = data_start_date
        self.data_end_date = data_end_date
        self.params = params
        self.quantile0_pct = None
        self.quantile25_pct = None
        self.quantile50_pct = None
        self.quantile75_pct = None
        self.quantile100_pct = None
        self.mean_sim_ann = None
        self.vol_realized_ann = None
        self.forecast_error = None

    @classmethod
    def from_series(cls, series):
        """
        Instance an new object from the series data used in caching
        :param series: stored data stored by RVMSingleResultCache.cache_local, retrieved by
            RVMSingleResultCache.check_exists
        :return: new RVolModelSingleResult object
        """
        params = AllDatesVolModelRunParams.from_series(series)
        data_start_date = pd.Timestamp(series.pop('data_start_date'))
        data_end_date = pd.Timestamp(series.pop('data_end_date'))
        result = cls(data_start_date, data_end_date, params)
        for attr_name, attr_value in series.iteritems():
            try:
                setattr(result, attr_name, float(attr_value))
            except ValueError:
                setattr(result, attr_name, attr_value)
        return result

    def to_full_series(self):
        """
        Generate cache-able version of data in pd.Series
        :return: Series
        """
        series = self.to_series()
        series['prefix'] = self.prefix
        series['window'] = self.params.window
        return series

    def to_series(self):
        """
        Generate data-only version of data in pd.Series
        :return: Series
        """
        return pd.Series([self.data_start_date,
                          self.data_end_date,
                          self.quantile0_pct,
                          self.quantile25_pct,
                          self.quantile50_pct,
                          self.quantile75_pct,
                          self.quantile100_pct,
                          self.mean_sim_ann,
                          self.vol_realized_ann,
                          self.forecast_error],
                         index=['data_start_date','data_end_date',
                                'quantile0_pct','quantile25_pct',
                                'quantile50_pct','quantile75_pct',
                                'quantile100_pct','mean_sim_ann',
                                'vol_realized_ann', 'forecast_error'])

    @property
    def prefix(self):
        """
        File string prefix method
        :return: str
        """
        return '{!s}_{!s}_{!s}_{!s}_{!s}_{!s}'.format(
            self.params.model_type,
            self.params.test_dist,
            self.params.n_sims,
            self.params.n_forecast,
            self.data_start_date.strftime('%Y%m%d'),
            self.data_end_date.strftime('%Y%m%d')
        )

    def set_from(self, result_dict):
        """
        Set float value attributes using R script return dictionary
        :return: None
        """
        prefix_result = self.prefix
        self.quantile0_pct = result_dict["{!s}_quantile0".format(prefix_result)]
        self.quantile25_pct = result_dict["{!s}_quantile25".format(prefix_result)]
        self.quantile50_pct = result_dict["{!s}_quantile50".format(prefix_result)]
        self.quantile75_pct = result_dict["{!s}_quantile75".format(prefix_result)]
        self.quantile100_pct = result_dict["{!s}_quantile100".format(prefix_result)]
        self.mean_sim_ann = result_dict["{!s}_mean.sim.ann".format(prefix_result)]
        self.vol_realized_ann = result_dict["{!s}_vol.realized.ann".format(prefix_result)]
        self.forecast_error = result_dict["{!s}_forecast.error".format(prefix_result)]

    def __eq__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        is_equal = self.data_start_date == other.data_start_date and \
            self.data_end_date == other.data_end_date and \
            self.params == other.params
        return is_equal

    def __hash__(self):
        h0 = hash(self.params)
        h0 += hash(self.data_start_date)
        h0 += hash(self.data_end_date)
        return h0


class RVolModelMultiDateResult(object):
    """
    Holds the RVolModelSingleResult, for a range of dates, for a given AllDatesVolModelRunParams
    Provides access methods for accumulating RVolModelSingleResult data

    attributes:
        params: AllDatesVolModelRunParams
        results: dict<Timestamp: RVolModelSingleResult>
    """
    def __init__(self, params):
        self.params = params
        self.results = {}

    def add_result(self, single_result):
        """
        Add a RVolModelSingleResult to held results
        :param single_result: RVolModelSingleResult
        :return: None
        """
        if self.params == single_result.params:
            self.results[single_result.data_end_date] = single_result

    def get_result_field(self, field_name):
        """
        Return a list of values across held RVolModelSingleResult for attribute field_name
        :param field_name: str
        :return: list<values>
        """
        return map(
            lambda result_end_date: getattr(self.results[result_end_date], field_name),
            sorted(self.results.keys()))

    def get_result_frame(self):
        """
        Return a frame of series across held RVolModelSingleResult
        :return: DataFrame<RVolModelSingleResult.to_series()>
        """
        list_results = map(
            lambda result_end_date: self.results[result_end_date].to_series(),
            sorted(self.results.keys())
        )
        return pd.DataFrame(list_results)


class RVMSingleResultCache(object):
    @classmethod
    def filename(cls, data_start_date, data_end_date, params):
        fn = '{!s}_{!s}_{!s}_{!s}_{!s}_{!s}.txt'.format(
            params.model_type,
            params.test_dist,
            params.n_sims,
            params.n_forecast,
            data_start_date.strftime('%Y%m%d'),
            data_end_date.strftime('%Y%m%d')
        )
        fn = os.path.join(TMP_PATH, fn)
        return fn

    @classmethod
    def check_exists(cls, data_start_date, data_end_date, params):
        file_check = cls.filename(data_start_date, data_end_date, params)
        if os.path.exists(file_check):
            result_series = pd.read_csv(file_check,sep='\t',header=None,index_col=0)[1]
            result_series.index.name = ''
            return RVolModelSingleResult.from_series(result_series)
        return None

    @classmethod
    def cache_local(cls, result, overwrite=True):
        series_save = result.to_full_series()
        file_name_save = cls.filename(result.data_start_date, result.data_end_date, result.params)
        if not overwrite:
            if os.path.exists(file_name_save):
                raise Exception('Result already stored and set no-overwrite')
        series_save.to_csv(file_name_save, sep='\t', header=False)


