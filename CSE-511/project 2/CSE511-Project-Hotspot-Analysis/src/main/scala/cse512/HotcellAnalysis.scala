package cse512

import org.apache.log4j.{Level, Logger}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions.udf
import org.apache.spark.sql.functions._

object HotcellAnalysis {
  Logger.getLogger("org.spark_project").setLevel(Level.WARN)
  Logger.getLogger("org.apache").setLevel(Level.WARN)
  Logger.getLogger("akka").setLevel(Level.WARN)
  Logger.getLogger("com").setLevel(Level.WARN)

def runHotcellAnalysis(spark: SparkSession, pointPath: String): DataFrame =
{
  // Load the original data from a data source
  var pickupInfo = spark.read.format("com.databricks.spark.csv").option("delimiter",";").option("header","false").load(pointPath);
  pickupInfo.createOrReplaceTempView("nyctaxitrips")
  pickupInfo.show()

  // Assign cell coordinates based on pickup points
  spark.udf.register("CalculateX",(pickupPoint: String)=>((
    HotcellUtils.CalculateCoordinate(pickupPoint, 0)
    )))
  spark.udf.register("CalculateY",(pickupPoint: String)=>((
    HotcellUtils.CalculateCoordinate(pickupPoint, 1)
    )))
  spark.udf.register("CalculateZ",(pickupTime: String)=>((
    HotcellUtils.CalculateCoordinate(pickupTime, 2)
    )))
  pickupInfo = spark.sql("select CalculateX(nyctaxitrips._c5),CalculateY(nyctaxitrips._c5), CalculateZ(nyctaxitrips._c1) from nyctaxitrips")
  var newCoordinateName = Seq("x", "y", "z")
  pickupInfo = pickupInfo.toDF(newCoordinateName:_*)
  pickupInfo.show()

  // Define the min and max of x, y, z
  val minX = -74.50/HotcellUtils.coordinateStep
  val maxX = -73.70/HotcellUtils.coordinateStep
  val minY = 40.50/HotcellUtils.coordinateStep
  val maxY = 40.90/HotcellUtils.coordinateStep
  val minZ = 1
  val maxZ = 31
  val numCells = (maxX - minX + 1)*(maxY - minY + 1)*(maxZ - minZ + 1)

  // YOU NEED TO CHANGE THIS PART
  pickupInfo = pickupInfo
    .select("x", "y", "z")
    .where("x >= " + minX + " AND x <= " + maxX
      + " AND y >= " + minY + " AND y <= " + maxY
      + " AND z >= " + minZ +  " AND z <= " + maxZ)
    .orderBy("z", "y", "x")

  val hotcellsDf = pickupInfo
    .groupBy("z", "y", "x").count()
    .withColumnRenamed("count", "cell_hotness")
    .orderBy("z", "y", "x")
  hotcellsDf.createOrReplaceTempView("hotcells")

  val avg = (hotcellsDf.select("cell_hotness").agg(sum("cell_hotness")).first().getLong(0).toDouble) / numCells
  val stdDev = scala.math.sqrt((hotcellsDf.withColumn("sqr_cell", pow(col("cell_hotness"), 2)).select("sqr_cell").agg(sum("sqr_cell")).first().getDouble(0) / numCells) - scala.math.pow(avg, 2))

  val adjHotCellNumber = spark.sql(
    "SELECT h1.x AS x, h1.y AS y, h1.z AS z, "
    + "sum(h2.cell_hotness) AS cellNumber "
    + "FROM hotcells AS h1, hotcells AS h2 "
    + "WHERE (h2.x = h1.x+1 OR h2.x = h1.x OR h2.x = h1.x-1) AND (h2.y = h1.y+1 OR h2.y = h1.y OR h2.y = h1.y-1) AND (h2.z = h1.z+1 OR h2.z = h1.z OR h2.z = h1.z-1)"
    + "GROUP BY h1.z, h1.x, h1.y "
    + "ORDER BY h1.z, h1.x, h1.y")

  val calculateNumberOfAdjFunc = udf(
    (min_x: Int, max_x: Int, min_y: Int, max_y: Int, min_z: Int, max_z: Int, x: Int, y: Int, z: Int)
    => HotcellUtils.calculateNumAdjCells(min_x, max_x, min_y, max_y, min_z, max_z, x, y, z))
  val sumAdjCellHotness = adjHotCellNumber.withColumn("sumAdjCellHotness", calculateNumberOfAdjFunc(lit(minX), lit(maxX), lit(minY), lit(maxY), lit(minZ), lit(maxZ), col("x"), col("y"), col("z")))

  val gScoreFunc = udf(
    (numCells: Int, x: Int, y: Int, z: Int, adjacentHotcell: Int, cellNumber: Int, avg: Double, stdDev: Double)
    => HotcellUtils.gScore(numCells, x, y, z, adjacentHotcell, cellNumber, avg, stdDev))
  val gScoreHotCell = sumAdjCellHotness.withColumn("gScore", gScoreFunc(lit(numCells), col("x"), col("y"), col("z"), col("sumAdjCellHotness"), col("cellNumber"), lit(avg), lit(stdDev))).orderBy(desc("gScore")).limit(50)

  pickupInfo = gScoreHotCell.select(col("x"), col("y"), col("z"))
  pickupInfo // YOU NEED TO CHANGE THIS PART
}
}
