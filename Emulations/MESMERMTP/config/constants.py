from pathlib import Path

DATA_DIR            = Path('/mnt/CMIP6_storage/cmip6-ng/')
PRECIP_DIR          = DATA_DIR /  'pr/mon/g025/'
TAS_DIR             = DATA_DIR /  'tas/mon/g025/'
PROCESSED_DIR       = Path('/mnt/PROVIDE/sarah/mesmer-m-tp-dev/processed_CMIP6/')

CODE_DIR            = Path('/home/ubuntu/sarah/files/income_decile/')    

 
emu_vars            = ['tas', 'pr']
n_sindex            = 2652
n_months            = 12
ref_period          = [1850, 1900]
n_hist_years        = 165
n_ssp_years         = 86
n_ssps              = 5 
n_closest           = 150 

mi_ind              = [(m, i) for m in range(12) for i in range(n_sindex)]   