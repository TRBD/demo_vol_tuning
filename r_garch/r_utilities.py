import pandas as pd
from contextlib import contextmanager
from pyper import R, RError
from config import R_PATH
import os.path

cur_path = os.path.dirname(os.path.realpath(__file__))
script_path = os.path.join(cur_path, "../scripts")
SOURCE_FILE = os.path.join(script_path, 'rGarch.r')



@contextmanager
def r_connection():
    r = R(RCMD=R_PATH)
    yield r
    r.prog.terminate()


@contextmanager
def r_connection_initialized(initialization_string):
    r = R(RCMD=R_PATH)
    r(initialization_string)
    yield r
    r.prog.terminate()


class RUtilities(object):

    @classmethod
    def create_date_series(cls, r_conn, date_list, date_list_var_name):
        if len(date_list) > 0:
            date_list_str = map(lambda d: d.strftime('%Y-%m-%d'), date_list)
            r_conn[date_list_var_name] = date_list_str
            r_conn('{var} = data.frame({var}, stringsAsFactors=F)'.format(var=date_list_var_name))
            r_conn('colnames({var}) <- c(\'Date\')'.format(var=date_list_var_name))
            r_conn('{var}$Date=as.Date({var}$Date)'.format(var=date_list_var_name))
        else:
            r_conn('{var} = data.frame(Date=as.Date(character()),stringsAsFactors = F)'.format(var=date_list_var_name))
        return

    @classmethod
    def create_time_series_frame(cls, r_conn, data_frame, date_var, data_frame_var_name):
        data_frame = data_frame.fillna(pd.np.nan)
        if date_var not in data_frame.columns:
            data_frame.reset_index(inplace=True)
            if date_var not in data_frame.columns:
                raise Exception('date var not in data frame')
        data_frame[date_var] = data_frame[date_var].apply(lambda d: d.strftime('%Y-%m-%d'))
        r_conn[data_frame_var_name] = data_frame.values
        r_conn('{var} <- data.frame({var},stringsAsFactors=F)'.format(var=data_frame_var_name))
        colnames = data_frame.columns.tolist()
        r_conn['cns'] = colnames
        r_conn('colnames({var}) <- cns'.format(var=data_frame_var_name))
        colnames.remove(date_var)
        r_conn('{var}${date_var} <- as.Date({var}${date_var})'.format(var=data_frame_var_name, date_var=date_var))
        list(map(
            lambda col_name: r_conn('{var}${col_name} <- as.double({var}${col_name})'.
                                    format(var=data_frame_var_name, col_name=col_name)),
            colnames))
        return
