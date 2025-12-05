# src/udfs.py
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

def arr_to_str_py(val):
    if val is None:
        return "None"
    if isinstance(val, list):
        if len(val) == 0:
            return "None"
        return ",".join(str(x) for x in val)
    return str(val)

arr_to_str = udf(arr_to_str_py, StringType())
