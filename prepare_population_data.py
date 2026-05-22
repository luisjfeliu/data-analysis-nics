import pandas as pd
import requests
import sys

def main():
    # 1. Download Census data (Vintage 2023 estimates)
    census_url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/state/totals/NST-EST2023-ALLDATA.csv"
    print(f"Downloading Census data from {census_url}...")
    try:
        census_df = pd.read_csv(census_url)
    except Exception as e:
        print(f"Error downloading Census data: {e}")
        sys.exit(1)

    # Filter for SUMLEV = 40 (States, DC, and Puerto Rico)
    states_census = census_df[census_df['SUMLEV'] == 40].copy()
    states_census = states_census[['NAME', 'POPESTIMATE2020', 'POPESTIMATE2021', 'POPESTIMATE2022', 'POPESTIMATE2023']]
    
    # Rename columns to match target schema
    states_census.rename(columns={
        'NAME': 'state',
        'POPESTIMATE2020': 'population_2020',
        'POPESTIMATE2021': 'population_2021',
        'POPESTIMATE2022': 'population_2022',
        'POPESTIMATE2023': 'population_2023'
    }, inplace=True)

    print(f"Successfully processed {len(states_census)} Census rows (50 states + DC + Puerto Rico).")

    # 2. Fetch World Bank data for GUM (Guam), MNP (Northern Mariana Islands), and VIR (U.S. Virgin Islands)
    wb_url = "https://api.worldbank.org/v2/country/GUM;MNP;VIR/indicator/SP.POP.TOTL?date=2020:2023&format=json"
    print(f"Fetching World Bank data from {wb_url}...")
    try:
        response = requests.get(wb_url)
        wb_data = response.json()
    except Exception as e:
        print(f"Error fetching World Bank data: {e}")
        sys.exit(1)

    # World Bank JSON structure is [metadata, records]
    if not isinstance(wb_data, list) or len(wb_data) < 2:
        print("Unexpected World Bank API response structure.")
        sys.exit(1)

    wb_records = wb_data[1]
    wb_list = []
    for r in wb_records:
        if r['value'] is not None:
            wb_list.append({
                'wb_state': r['country']['value'],
                'year': int(r['date']),
                'population': int(r['value'])
            })
    
    df_wb_raw = pd.DataFrame(wb_list)

    # Map World Bank names to standard NICS territory names
    wb_name_map = {
        'Guam': 'Guam',
        'Northern Mariana Islands': 'Mariana Islands',
        'Virgin Islands (U.S.)': 'Virgin Islands'
    }
    df_wb_raw['state'] = df_wb_raw['wb_state'].map(wb_name_map)
    
    # Pivot World Bank data to get years as columns
    df_wb_pivot = df_wb_raw.pivot(index='state', columns='year', values='population').reset_index()
    
    # Rename columns to match target schema
    df_wb_pivot.rename(columns={
        2020: 'population_2020',
        2021: 'population_2021',
        2022: 'population_2022',
        2023: 'population_2023'
    }, inplace=True)

    print(f"Successfully processed {len(df_wb_pivot)} World Bank rows (Guam, Mariana Islands, Virgin Islands).")

    # 3. Concatenate/Merge datasets
    final_df = pd.concat([states_census, df_wb_pivot], ignore_index=True)
    
    # Sort by state name alphabetically
    final_df.sort_values(by='state', inplace=True)
    final_df.reset_index(drop=True, inplace=True)

    # 4. Save to CSV in project directory
    output_path = "/Users/luis/Documents/projects/data-analysis-nics/us_population_2020_2023.csv"
    final_df.to_csv(output_path, index=False)
    print(f"Merged population estimates saved successfully to {output_path}")
    print(f"Total rows in output: {len(final_df)}")
    print(final_df.head(10))

if __name__ == "__main__":
    main()
