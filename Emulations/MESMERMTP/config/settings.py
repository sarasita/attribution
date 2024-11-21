from pathlib import Path

OUTPUT_DIR     = Path('/mnt/PROVIDE/sarah/income_decile/')

ssp_ids          = ['ssp119', 'ssp126', 'ssp245', 'ssp370', 'ssp585'] 
ref_period       = [1850, 1900]
model_ids        = ['ACCESS-CM2',
                    'ACCESS-ESM1-5',
                    'AWI-CM-1-1-MR',
                    'CESM2-WACCM',
                    'CESM2',
                    'CMCC-CM2-SR5',
                    'CNRM-CM6-1-HR',
                    'CNRM-CM6-1',
                    'CNRM-ESM2-1',
                    'CanESM5',
                    'E3SM-1-1',
                    'FGOALS-f3-L',
                    'FGOALS-g3',
                    'FIO-ESM-2-0',
                    'HadGEM3-GC31-LL',
                    'HadGEM3-GC31-MM',
                    'IPSL-CM6A-LR',
                    'MPI-ESM1-2-HR',
                    'MPI-ESM1-2-LR',
                    'MRI-ESM2-0',
                    'NESM3',
                    'NorESM2-LM',
                    'NorESM2-MM',
                    'UKESM1-0-LL']
training_ids =     ['r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f2',
                    'r1i1p1f2',
                    'r1i1p1f2',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f3',
                    'r1i1p1f3',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f1',
                    'r1i1p1f2']
model_training_mapping = dict(zip(model_ids, training_ids))
n_models               = len(model_ids)
model_ids_veri  = ['ACCESS-ESM1-5', 'CanESM5', 'MPI-ESM1-2-LR']








