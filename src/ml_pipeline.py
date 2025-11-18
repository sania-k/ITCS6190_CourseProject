from pyspark.ml.pipeline import PipelineModel

pipeline_path = "../notebooks/spark_gbt_model"

# Load the pipeline model
loaded_pipeline_model = PipelineModel.load(pipeline_path)