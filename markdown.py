import pandas as pd

def markdown_to_excel(markdown_table, excel_file):
  """Converts a Markdown table to an Excel file.

  Args:
    markdown_table: The Markdown table as a string.
    excel_file: The path to the output Excel file.
  """

  # Split the Markdown table into lines
  lines = markdown_table.splitlines()

  # Find the index of the header row
  header_index = next(i for i, line in enumerate(lines) if line.startswith('|'))

  # Extract header and data rows
  header_row = lines[header_index].strip('|').split('|')
  data_rows = [line.strip('|').split('|') for line in lines[header_index+1:] if line.strip()]

  # Create a Pandas DataFrame
  df = pd.DataFrame(data_rows, columns=header_row)

  # Write the DataFrame to an Excel file
  df.to_excel(excel_file, index=False)

markdown_to_excel(markdown_table, excel_file)