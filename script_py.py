#/spark2.4/bin/pyspark --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.5,com.datastax.spark:spark-cassandra-connector_2.11:2.4.2 --driver-memory 512m --driver-cores 1 --master local[1]
# /spark2.4/bin/spark-submit data2/script_py.py

from pyspark.ml.evaluation import RegressionEvaluator, BinaryClassificationEvaluator
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.regression import LinearRegression
from pyspark.ml.tuning import ParamGridBuilder, TrainValidationSplit
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("student910_5_app").master("local[*]").getOrCreate()

data_path = "data2/houses.csv"
model_dir = "models"

# read data from storage
data = spark\
    .read\
    .format("csv")\
    .options(inferSchema=True, header=True) \
    .load(data_path)

data.show(3)
print(data.schema.json())

# target
target = ["price"]

# model evaluator
evaluator = RegressionEvaluator() \
        .setMetricName("rmse") \
        .setLabelCol("label") \
        .setPredictionCol("prediction")



def prepare_data_1(data, features, target):
    # features
    f_columns = ",".join(features).split(",")
    # target
    f_target = ",".join(target).split(",")
    f_target = list(map(lambda c: F.col(c).alias("label"), f_target))
    # all columns
    all_columns = ",".join(features + target).split(",")
    all_columns = list(map(lambda c: F.col(c), all_columns))
    # model data set
    model_data = data.select(all_columns)
    # preparation
    assembler = VectorAssembler(inputCols=f_columns, outputCol='features')
    model_data = assembler.transform(model_data)
    model_data = model_data.select('features', f_target[0])
    return model_data


def prepare_and_train_1(data, features, target):
    model_data = prepare_data_1(data, features, target)
    # train, test
    train, test = model_data.randomSplit([0.8, 0.2], seed=12345)
    # model
    lr = LinearRegression(featuresCol='features', labelCol='label', maxIter=10, regParam=0.01)
    # train model
    model = lr.fit(train)
    # check the model on the test data
    prediction = model.transform(test)
    prediction.show(5)
    evaluation_result = evaluator.evaluate(prediction)
    print("Evaluation result: {}".format(evaluation_result))
    return model




print("=== MODEL ===")
features = ["DistrictId","Rooms", "Square"] 
model_1 = prepare_and_train_1(data, features, target)


# Evaluation result: Evaluation result: 70568.2931549

model_1.write().overwrite().save(model_dir + "/model_1")