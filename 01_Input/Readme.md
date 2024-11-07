# Processing WID inequality and Chancel Data 

I combine data on global income/wealth inequality from [WID.world](https://wid.world) and 
carbon inequality associted with income/ wealth from [Lucas Chancel](https://lucaschancel.com/global-carbon-inequality-1990-2019/)
to generate a datastat of relative contributions to global CO2-e emissions of specific emitter
groups in selected countries and regions between 1990-2019. 

## Status 

- prototype: the project is just starting up and the code is all prototype

## Output 
- country_to_global_scaling_coefficients.csv: 2d table with years (1990-2019) as row index and ISO 3166-1 alpha-2 country codes as column index. The table value indicates the relative contribution of the conumption-based CO2-e emissions of an entire country (p0p100) to global emissions. For example, the value 0.2 for the US in 1990 indicates consumption based CO2-e emissions of all US Americans combined were 20% of the global CO2-e emissions in 1990. 
- region_to_global_scaling_coefficients.csv: Same as above, but for selected countries/regions (e.g. EU27) 
- XX_scaling.csv:  2d table with years (1990-2019) as row index and income/wealth groups (e.g. p90p100 for the top 10%) as column index. For a given country or region (XX) this indicates the relative contribution of an income/wealth group to the country's/region's total emissions. For example, for US_scaling.csv the value 0.27 for p90p100 in 1990 indicates that 27% of the US' total CO2-e consumption-based emissions stemmed from the wealthiest 10%. 

## Step by Step Guide: 

### Step 0: Set paths 
- Adjust paths in config.py to represent where you've locally stored this repository and associated data 

### Step 1: Download data 
- In your data directory (DATA_DIR) create a folder called 'Chancel' containing the data from [Lucas Chancel](https://lucaschancel.com/global-carbon-inequality-1990-2019/). Downloading the data directly should create three subfolders (Data, Do-files, Excel-Figures). 
- In your data directory (DATA_DIR) create a folder called 'WID' and a subfolder 'wid_all_data' containing the unarchived data from [WID.world](https://wid.world/data/) -> lower left 'Download Full Dataset'. There should be no subfolders in 'wid_all_data', i.e. the folder contains a README.md and files called WID_data_XX.csv.

### Step 2: Execute scripts
- Be mindful that WID.world is regularly updated. This can imply that you need to adjust the reference year for the conversion to PPP Euros. See https://wid.world/methodology/#library-methodological-notes for details. 
- Execute 000_WID_preprocessing.py and 001_CHANCEL_preprocessing.py to generate all outputs 
- Execute 010_WID_data_visualisation.py and 011_CHANCEL_data_visualisation.py to display/ check output 
- all important functions are in utils 