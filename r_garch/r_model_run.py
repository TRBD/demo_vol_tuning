from .r_utilities import RUtilities


def initialized_single_run(r_conn, x_frame, start_date, end_date, n_forecast, model_type, test_dist, n_simulations):
    r_conn['nForecastDays'] = n_forecast
    RUtilities.create_time_series_frame(r_conn, x_frame, 'Date', 'data')
    r_conn['vModel'] = model_type
    r_conn['dist'] = test_dist
    r_conn['nSimulations'] = n_simulations
    r_conn['dt.test.start'] = start_date.strftime('%Y-%m-%d')
    r_conn['dt.test.end'] = end_date.strftime('%Y-%m-%d')
    r_conn(
        'result <- rGARCH(data, dt.test.start, dt.test.end, vModel, ' +
        'nForecastDays=nForecastDays, nSimulations=nSimulations, dist=dist)'
    )
    result_dict = r_conn['result']
    return result_dict
