import seaborn as sns
from config import PLOT_PATH
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class SummaryResults(object):
    def __init__(self, model_results):
        self.model_results = model_results
        self.forecast_error_frame = None
        self.realized_series = None
        self.sim_frame = None
        self.set_timeseries_frames()

    def set_timeseries_frames(self):
        forecast_error_list = []
        for result_holder in self.model_results:
            r_frame = result_holder.get_result_frame()
            name = '{!s}_{!s}_{!s}'.format(
                result_holder.params.model_type, result_holder.params.test_dist, result_holder.params.window)
            forecast_error_series = r_frame.set_index('data_end_date').forecast_error.copy()
            forecast_error_series.name = name
            forecast_error_list.append(forecast_error_series)

        self.forecast_error_frame = pd.DataFrame(forecast_error_list).T

        result_holder = self.model_results[0]
        r_frame = result_holder.get_result_frame()
        self.realized_series = r_frame.set_index('data_end_date').vol_realized_ann.copy()
        self.realized_series.name = 'Realized'

        self.sim_frame = self.forecast_error_frame.apply(lambda error_col: self.realized_series - error_col)

    def summary_error_frame(self, sub_start=0, sub_end=-1):
        error_frame_sub = self.forecast_error_frame.iloc[sub_start:sub_end]
        mses = (error_frame_sub**2).mean()
        maes = (error_frame_sub.abs()).mean()
        q3abs = error_frame_sub.abs().quantile(.75)

        model_types = list(map(lambda x: x.split('_')[0], mses.index))
        dist_types = list(map(lambda x: x.split('_')[1], mses.index))
        windows = list(map(lambda x: x.split('_')[2], mses.index))
        mse_values = mses.tolist()
        mae_values = maes.tolist()
        q3_values = q3abs.tolist()
        summary_frame = pd.DataFrame([mse_values, mae_values, q3_values, model_types, dist_types, windows],
            index=['mse','mae','q3_abs', 'model_type','dist_type','window']).T

        summary_frame['window'] = summary_frame.window.astype('int')
        summary_frame['mse'] = summary_frame.mse.astype('float')
        summary_frame['mae'] = summary_frame.mae.astype('float')
        summary_frame['q3_abs'] = summary_frame.q3_abs.astype('float')
        summary_frame['window_name'] = summary_frame['window'].apply(
            lambda w: '{!s} Days'.format(w) if int(w) != -1 else 'Full History')
        summary_frame.loc[summary_frame[summary_frame.window==-1].index,'window'] = 10000
        summary_frame.sort_values(by=['window','model_type','dist_type'],inplace=True)
        return summary_frame


def summary_frame_metric_plots(metric, summary_frame, split=-1, save_fig=True):
    if split == -1:
        split_post_fix = '_all'
        split_title = 'Full Period'
    else:
        split_post_fix = '_split_{!s}'.format(split)
        split_title = 'Split {!s}'.format(split)
    g = sns.catplot(kind='bar',x='window_name', y=metric, hue='model_type',col='dist_type',data=summary_frame)
    g.despine(left=True).set_ylabels(metric).\
        set(ylim=(summary_frame[metric].min()*.97, summary_frame[metric].max()*1.03)).fig.suptitle(split_title)
    if save_fig:
        g.savefig(os.path.join(PLOT_PATH, '{!s}_win_model_dist{!s}.png'.format(metric, split_post_fix)))
    g = sns.catplot(kind='bar',x='model_type', y=metric, hue='window_name',col='dist_type',data=summary_frame)
    g.despine(left=True).set_ylabels(metric).\
        set(ylim=(summary_frame[metric].min()*.97, summary_frame[metric].max()*1.03)).fig.suptitle(split_title)
    if save_fig:
        g.savefig(os.path.join(PLOT_PATH, '{!s}_model_win_dist{!s}.png'.format(metric, split_post_fix)))
    g = sns.catplot(kind='bar',x='model_type', y=metric, hue='dist_type',col='window_name',data=summary_frame)
    g.despine(left=True).set_ylabels(metric).\
        set(ylim=(summary_frame[metric].min()*.97, summary_frame[metric].max()*1.03)).fig.suptitle(split_title)
    if save_fig:
        g.savefig(os.path.join(PLOT_PATH, '{!s}_model_dist_win{!s}.png'.format(metric, split_post_fix)))
        plt.close('all')


def plot_sim_realized_timeseries_group(sim_frame, realized_series, model_type, dist_type, save_fig=True):
    subset = list(filter(lambda c: c.split('_')[0]==model_type, sim_frame.columns))
    subset = list(filter(lambda c: c.split('_')[1]==dist_type, subset))
    tmp = sim_frame[subset].copy()
    windows = list(map(lambda c: c.split('_')[2], subset))
    windows_names = list(map(lambda w: w + ' Days' if int(w)!=-1 else 'Full History', windows))
    tmp.columns = windows_names
    axs = tmp.plot(subplots=True,sharey=True)
    _ = list(map(lambda a: realized_series.plot(ax=a,style='k--',label=realized_series.name), axs))
    _ = list(map(lambda a: a.legend(), axs))
    axs[-1].set_xlabel('')
    title = 'Sim Forecast Comparison | Model: {!s} | Dist: {!s}'.format(model_type, dist_type)
    axs[0].set_title(title)
    axs[0].figure.set_size_inches(9,7.5)
    plt.tight_layout()
    if save_fig:
        axs[0].figure.savefig(os.path.join(PLOT_PATH, 'sim_forecast_comp_{!s}_{!s}.png'.format(model_type, dist_type)))
        plt.close('all')


def plot_sim_realized_timeseries_window_group(sim_frame, realized_series, window, dist_type, save_fig=True):
    subset = list(filter(lambda c: int(c.split('_')[2])==int(window), sim_frame.columns))
    subset = list(filter(lambda c: c.split('_')[1]==dist_type, subset))
    tmp = sim_frame[subset].copy()
    models = list(map(lambda c: c.split('_')[0], subset))
    window_name = window + ' Days' if int(window) != -1 else 'Full History'
    tmp.columns = models
    axs = tmp.plot(subplots=True,sharey=True)
    _ = list(map(lambda a: realized_series.plot(ax=a,style='k--',label=realized_series.name), axs))
    _ = list(map(lambda a: a.legend(), axs))
    axs[-1].set_xlabel('')
    title = 'Sim Forecast Comparison | Window: {!s} | Dist: {!s}'.format(window_name, dist_type)
    axs[0].set_title(title)
    axs[0].figure.set_size_inches(9,7.5)
    plt.tight_layout()
    if save_fig:
        axs[0].figure.savefig(os.path.join(PLOT_PATH, 'sim_forecast_comp_{!s}_{!s}.png'.format(window_name, dist_type)))
        plt.close('all')

def plot_resid_realized_timeseries_group(resid_frame, realized_series, model_type, dist_type, save_fig=True):
    subset = list(filter(lambda c: c.split('_')[0]==model_type, resid_frame.columns))
    subset = list(filter(lambda c: c.split('_')[1]==dist_type, subset))
    tmp = resid_frame[subset].copy()
    windows = list(map(lambda c: c.split('_')[2], subset))
    windows_names = list(map(lambda w: w + ' Days' if int(w)!=-1 else 'Full History', windows))
    tmp.columns = windows_names
    axs = tmp.plot(subplots=True,sharey=True)
    _ = list(map(lambda a: realized_series.plot(ax=a,style='k--',secondary_y=True,label=realized_series.name), axs))
    _ = list(map(lambda a: a.legend(), axs))
    axs[-1].set_xlabel('')
    title = 'Sim Error Comparison | Model: {!s} | Dist: {!s}'.format(model_type, dist_type)
    axs[0].set_title(title)
    axs[0].figure.set_size_inches(9,7.5)
    plt.tight_layout()
    if save_fig:
        axs[0].figure.savefig(os.path.join(PLOT_PATH, 'sim_residual_comp_{!s}_{!s}.png'.format(model_type, dist_type)))
        plt.close('all')

def plot_resid_realized_timeseries_window_group(resid_frame, realized_series, window, dist_type, save_fig=True):
    subset = list(filter(lambda c: int(c.split('_')[2])==int(window), resid_frame.columns))
    subset = list(filter(lambda c: c.split('_')[1]==dist_type, subset))
    tmp = resid_frame[subset].copy()
    models = list(map(lambda c: c.split('_')[0], subset))
    window_name = window + ' Days' if int(window) != -1 else 'Full History'
    tmp.columns = models
    axs = tmp.plot(subplots=True,sharey=True)
    _ = list(map(lambda a: realized_series.plot(ax=a,style='k--',secondary_y=True,label=realized_series.name), axs))
    _ = list(map(lambda a: a.legend(), axs))
    axs[-1].set_xlabel('')
    title = 'Sim Resididual Comparison | Window: {!s} | Dist: {!s}'.format(window_name, dist_type)
    axs[0].set_title(title)
    axs[0].figure.set_size_inches(9,7.5)
    plt.tight_layout()
    if save_fig:
        axs[0].figure.savefig(os.path.join(PLOT_PATH, 'sim_residual_comp_{!s}_{!s}.png'.format(window_name, dist_type)))
        plt.close('all')

def plot_resid_rolling_realized_timeseries_group(resid_frame, realized_series, model_type, dist_type, save_fig=True):
    subset = list(filter(lambda c: c.split('_')[0]==model_type, resid_frame.columns))
    subset = list(filter(lambda c: c.split('_')[1]==dist_type, subset))
    tmp = resid_frame[subset].copy()
    windows = list(map(lambda c: c.split('_')[2], subset))
    windows_names = list(map(lambda w: w + ' Days' if int(w)!=-1 else 'Full History', windows))
    tmp.columns = windows_names
    tmp_rolling = tmp.rolling(12,min_periods=1).apply(lambda rg: np.sum(np.abs(rg)),raw=True)
    f, axs= plt.subplots(2,1,sharex=True)
    tmp_rolling.plot(ax=axs[0])
    realized_series.plot(ax=axs[1],style='k--',label=realized_series.name)
    axs[1].legend()
    axs[-1].set_xlabel('')
    title = 'Sim Rolling Cumulative Abs Error Comparison | Model: {!s} | Dist: {!s}'.format(model_type, dist_type)
    axs[0].set_title(title)
    axs[0].figure.set_size_inches(9,5)
    plt.tight_layout()
    if save_fig:
        axs[0].figure.savefig(os.path.join(PLOT_PATH, 'sim_rolling_comp_{!s}_{!s}.png'.format(model_type, dist_type)))
        plt.close('all')

def plot_resid_rolling_realized_timeseries_window_group(resid_frame, realized_series, window, dist_type, save_fig=True):
    subset = list(filter(lambda c: int(c.split('_')[2])==int(window), resid_frame.columns))
    subset = list(filter(lambda c: c.split('_')[1]==dist_type, subset))
    tmp = resid_frame[subset].copy()
    models = list(map(lambda c: c.split('_')[0], subset))
    window_name = window + ' Days' if int(window) != -1 else 'Full History'
    tmp.columns = models
    tmp_rolling = tmp.rolling(12,min_periods=1).apply(lambda rg: np.sum(np.abs(rg)),raw=True)
    f, axs= plt.subplots(2,1,sharex=True)
    tmp_rolling.plot(ax=axs[0])
    realized_series.plot(ax=axs[1],style='k--',label=realized_series.name)
    axs[1].legend()
    axs[-1].set_xlabel('')
    title = 'Sim Rolling Cumulative Abs Error Comparison | Window: {!s} | Dist: {!s}'.format(window_name, dist_type)
    axs[0].set_title(title)
    axs[0].figure.set_size_inches(9,5)
    plt.tight_layout()
    if save_fig:
        axs[0].figure.savefig(os.path.join(PLOT_PATH, 'sim_rolling_comp_{!s}_{!s}.png'.format(window_name, dist_type)))
        plt.close('all')