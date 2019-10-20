import os
import pandas as pd
from r_garch.r_utilities import SOURCE_FILE


cur_path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(cur_path, "../data")
DATA_FILE = os.path.join(data_path, 'sample_data.txt')

DATA_COLUMNS = ['Date', 'Close']
TEST_DISTS = ['std', 'norm']
MODEL_TYPES = ['eGARCH', 'csGARCH', 'gjrGARCH']
LOOK_BACKS = [252*2, 252*5, 252*10, -1]
START_DATE = pd.Timestamp(2018,1,1)
#START_DATE = pd.Timestamp(1998,1,1)
N_SIM = 5000
N_FORECAST = 21

R_CONN_INITIALIZATION_STRING = "source(\"" + SOURCE_FILE + "\")"