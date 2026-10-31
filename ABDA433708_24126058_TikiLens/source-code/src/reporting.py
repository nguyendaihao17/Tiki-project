from io import BytesIO

import pandas as pd


def dataframe_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8-sig")


def excel_workbook_bytes(sheets):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet_name, dataframe in sheets.items():
            safe_sheet_name = sheet_name[:31]
            dataframe.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            worksheet = writer.sheets[safe_sheet_name]
            worksheet.freeze_panes(1, 0)
            if not dataframe.empty and len(dataframe.columns):
                worksheet.autofilter(0, 0, len(dataframe), len(dataframe.columns) - 1)
    return output.getvalue()
