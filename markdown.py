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

markdown_table = """| Name                                     | Zone      | IP                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | CPU                | RAM          | Storage        | Sevices                                | Versions | Connection Info                                                                                 |
| ---------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------ | -------------- | -------------------------------------- | -------- | ----------------------------------------------------------------------------------------------- |
| fw.ranad.co.il                           | IL-PT     | 45.83.42.10<br>45.83.42.164<br>62.219.14.46<br>62.219.14.80<br>62.219.199.129<br>62.219.199.130<br>62.219.199.131<br>62.219.199.136<br>82.80.224.193<br>91.202.168.147<br>91.202.168.239<br>91.202.168.240<br>91.202.171.136<br>109.207.76.71  109.207.76.217  <br>185.28.154.1  <br>185.28.154.83  <br>185.28.154.125  <br>185.28.154.190  <br>185.28.154.192  <br>185.28.154.200  <br>185.139.231.160 185.139.231.195 <br>185.220.207.37  <br>185.220.207.38  <br>185.241.4.78  <br>194.36.89.48  <br>192.168.5.5 | 2D                 | 4096MB       | 50GB           | Sophos FW UTM9                         |          |                                                                                                 |
| fw.ranad.co.il_IL                        | IL        | 5.100.252.230<br>185.241.6.62  <br>195.28.181.131  <br>192.168.10.254                                                                                                                                                                                                                                                                                                                                                                                                                                               | 2D<br><br><br><br> | 2048MB       | 50GB           | Sophos FW UTM9                         |          |                                                                                                 |
| IsufitCore                               | IL-PT     | 62.219.199.136                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 4B                 | 4096MB       | 100GB          |                                        |          | 62.219.199.136<br>pAr9RDB42w7T5H                                                                |
| linuxfile-server<br>                     | IL-PT     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 1B                 | 1024MB       | 20GB           |                                        |          | Lw!iur34@2mbFWl2!@<br>62.219.14.46                                                              |
| Ranad_clone2_TID3905752                  | IL-PT     | 185.220.207.38                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 20B                | 131072MB     | 700GB<br>350GB | isufit<br>isufit.net                   |          | RDP:<br>administrator<br>Isufit2006!!!<br>Isufit2006<br>Desperado1234!                          |
| ranad-sip_restored_new_v2_TID4061137_V5  | IL-PT     | 192.168.5.252                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 1D<br>             | 2048MB<br>   | 100GB<br>      | ??                                     | ??       | 9tr7c3cs<br>91.202.168.240<br>192.168.5.252                                                     |
| Ranad-Win2k19_RESTORED_NEW               | IL-PT<br> | 62.219.199.131<br>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 20B<br>            | 131072MB<br> | 1.95TB<br>     | No password                            |          |                                                                                                 |
| ranad.cloud                              | IL-PT<br> | 192.168.5.180                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 28B<br>            | 131072MB<br> | 0.98TB<br>     | Cloud isufit                           |          | zLbCG4HHJaEKRU<br>185.28.154.190<br>Isufit2006!!! - password                                    |
| ranad.cloud-win-new                      | IL-PT<br> | 192.168.5.200                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 28B<br>            | 131072MB<br> | 1.95TB<br>     | ranad-software.com                     |          | RDP - 185.28.154.200<br>Isufit2006!!!1                                                          |
| RANAD.NET                                | IL-PT<br> | 194.36.89.48                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 28B<br>            | 131072MB<br> | 0.98TB<br>     | clients                                |          | Isufit2006!!!<br>0545928279                                                                     |
| srv12_ranad_win22                        | IL-PT<br> |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 32B<br>            | 262144MB<br> | 1.46TB<br>     | ranadt.net<br>Team Foundation Server   |          | Isufit2006!!!<br>185.28.154.83                                                                  |
| srv12.ranad.co.il-win22-NEW              | IL<br>    | 192.168.10.11                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 20B<br>            | 131072MB<br> | 2.93TB<br>     | isufit                                 |          | ApvNwVl9WgMRsX<br>Old ip -195.28.181.131<br>New - 185.241.6.62<br>5.100.255.36<br>Isufit2006!!! |
| srv2012.ranad.co.il_IL-PT_restore_324898 | IL-PT<br> | 45.83.42.16<br>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 20B<br>            | 98304MB<br>  | 1.46TB<br>     | ranad.org                              |          | Isufit2006!!!<br>109.207.76.217<br>קריאת שחזור - 32489837<br>new pass: Isufit2006!!!            |
| ts.2k19.ranad.co.il_clone                | IL-PT<br> | 185.220.207.37  <br>82.80.224.193                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 28B<br>            | 131072MB<br> | 800GB<br>      | isufit.plus<br>ranad.org.il            |          | administrator<br>Isufit2006!!!<br>82.80.224.193                                                 |
| ts.ranad.co.il_win2k19                   | IL-PT<br> | 192.168.5.136<br>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 28B<br>            | 131072MB<br> | 0.98TB<br>     | ranad.co                               |          | nxH85RisK6rkRL<br>62.219.199.130<br>91.202.171.136<br>Isufit2006!!!                             |
| Win2022-Ranad-New                        | IL-PT<br> | 103.45.244.83<br>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 20B<br>            | 131072MB<br> | 0.98TB<br>     | Clients                                |          | 103.45.244.83<br>Q4s0z0oATsldjpg<br>Isufit2006!!!                                               |
| Win2k12.Ranad_RestoredTID_33241864       | IL-PT<br> | 45.83.42.164<br>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | 20B<br>            | 131072MB<br> | 0.98TB<br>     | VA Server<br>TS Service<br>Clients<br> |          | 45.83.42.164:3389<br>gns<br>Isufit2006                                                          |
| Win2k19.RANAD                            | IL-PT<br> | 192.168.5.190<br>    """

excel_file = "C:\Users\alexk\Documents\test.xlsx"

markdown_to_excel(markdown_table, excel_file)