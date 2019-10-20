from py_garch.vol_estimator import AllDatesVolModelRunParams, RVMSingleResultCache, RVolModelSingleResult, \
    RVolModelMultiDateResult
from py_garch.result_viz import *
from r_garch.r_utilities import r_connection_initialized
from r_garch.r_model_run import initialized_single_run


from .default_inputs import DATA_COLUMNS, TEST_DISTS, MODEL_TYPES, LOOK_BACKS, \
    START_DATE, N_FORECAST, N_SIM, DATA_FILE, R_CONN_INITIALIZATION_STRING


def populate_result_holders(look_backs, test_dists, model_types, n_forecast, n_simulations):
    model_results = []
    for window in look_backs:
        for test_dist in test_dists:
            for model_type in model_types:
                params = AllDatesVolModelRunParams(model_type, test_dist, n_forecast, n_simulations, window)
                cross_date_holder = RVolModelMultiDateResult(params)
                model_results.append(cross_date_holder)
    return model_results


def populate_single_run_results(r_conn, start_point, result_holder, data_set_test, data_set_full):
    input_start_date, input_end_date = result_holder.params.get_start_end_dates(
        start_point,
        data_set_test,
        data_set_full)

    result = RVMSingleResultCache.check_exists(input_start_date, input_end_date, result_holder.params)

    if result is None:
        result_dict = initialized_single_run(r_conn,
                                             data_set_full,
                                             input_start_date,
                                             input_end_date,
                                             result_holder.params.n_forecast,
                                             result_holder.params.model_type,
                                             result_holder.params.test_dist,
                                             result_holder.params.n_sims)
        result = RVolModelSingleResult(input_start_date, input_end_date, result_holder.params)
        result.set_from(result_dict)
        RVMSingleResultCache.cache_local(result)

    result_holder.add_result(result)


def run_all_params():
    full_data_set = pd.read_table(DATA_FILE, sep='\t')
    full_data_set.date=pd.to_datetime(full_data_set.date)
    full_data_set.columns = DATA_COLUMNS
    look_backs = LOOK_BACKS
    test_dists = TEST_DISTS
    model_types = MODEL_TYPES
    start_date_full_set = START_DATE
    data_set_fit_from = full_data_set[full_data_set.Date >= start_date_full_set]
    n_forecast = N_FORECAST
    start_offset = 0
    n_total = data_set_fit_from.shape[0]
    start_points = np.arange(start_offset, n_total - n_forecast - 1, n_forecast)
    n_dates_run = start_points.shape[0]
    n_simulations = N_SIM

    model_results = populate_result_holders(look_backs, test_dists, model_types, n_forecast, n_simulations)

    with r_connection_initialized(R_CONN_INITIALIZATION_STRING) as r_conn:
        for i, start_point in enumerate(start_points):
            for result_holder in model_results:
                populate_single_run_results(r_conn, start_point, result_holder, data_set_fit_from, full_data_set)
            print('completed across models, windows, test_dists {!s} of {!s}'.format(i, n_dates_run))

    summary = SummaryResults(model_results)
    summary_frame = summary.summary_error_frame() 
    
    summary_frame_metric_plots('mse', summary_frame, -1, True)
    summary_frame_metric_plots('mae', summary_frame, -1, True)
    summary_frame_metric_plots('q3_abs', summary_frame, -1, True)
    sim_frame = summary.sim_frame
    realized_series = summary.realized_series
    error_frame = summary.forecast_error_frame
    plot_sim_realized_timeseries_group(sim_frame, realized_series, 'gjrGARCH', 'std')
    plot_sim_realized_timeseries_group(sim_frame, realized_series, 'eGARCH', 'std')
    
    plot_resid_realized_timeseries_group(error_frame, realized_series, 'gjrGARCH', 'std')
    plot_resid_realized_timeseries_group(error_frame, realized_series, 'eGARCH', 'std')
    
    plot_resid_rolling_realized_timeseries_group(error_frame, realized_series, 'gjrGARCH', 'std')
    plot_resid_rolling_realized_timeseries_group(error_frame, realized_series, 'eGARCH', 'std')
    
    plot_sim_realized_timeseries_window_group(sim_frame, realized_series, '504', 'std')
    plot_resid_realized_timeseries_window_group(error_frame, realized_series, '504', 'std')
    plot_resid_rolling_realized_timeseries_window_group(error_frame, realized_series, '504', 'std')
    
    splits = summary.sim_frame.shape[0] // 3
    split_0 = (0, splits)
    split_1 = (splits, splits*2)
    split_2 = (splits*2, -1)
    summary_frame_split_0 = summary.summary_error_frame(*split_0)
    summary_frame_split_1 = summary.summary_error_frame(*split_1)
    summary_frame_split_2 = summary.summary_error_frame(*split_2)
    
    summary_frame_metric_plots('mse', summary_frame_split_0, 0, False)
    summary_frame_metric_plots('mse', summary_frame_split_1, 1, False)
    summary_frame_metric_plots('mse', summary_frame_split_2, 2, False)


if __name__ == '__main__':
    run_all_params()