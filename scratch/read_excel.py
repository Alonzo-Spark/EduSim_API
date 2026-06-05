import pandas as pd
import json

file_path = r"C:\Users\Mythri Banda\Downloads\projects\edusim\EduSim_Complete_ButtonLevel_TestCases.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names
    
    summary_data = []
    
    for sheet in sheet_names:
        df = xl.parse(sheet)
        summary_data.append({
            "Sheet": sheet,
            "Columns": df.columns.tolist(),
            "RowCount": len(df)
        })
        
    with open(r"C:\Users\Mythri Banda\Downloads\projects\edusim\EduSim_API\scratch\excel_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4)
        
    print("Done")
except Exception as e:
    print(f"Error reading excel: {e}")
