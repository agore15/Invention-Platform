import os; import sys; sys.path.append(os.path.dirname(os.path.abspath(__file__))); from pipeline import run_pipeline; run_pipeline(download_limit=1)
