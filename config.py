
# Set to your machine's R installation
# 'C:/Program Files/R/R-3.4.4/bin/R'
R_PATH = 'C:/Program Files/R/R-3.4.4/bin/R'
# Set to a location for caching data files
TMP_PATH = 'c:/tmp'
# Set to a location for storing images
PLOT_PATH = ''

if PLOT_PATH == '':
    PLOT_PATH = TMP_PATH

if R_PATH == '':
    raise Exception('R_PATH must be set')

if TMP_PATH == '':
    raise Exception('TMP_PATH must be set')
