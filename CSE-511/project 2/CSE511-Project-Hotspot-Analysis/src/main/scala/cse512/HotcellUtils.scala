package cse512

import java.sql.Timestamp
import java.text.SimpleDateFormat
import java.util.Calendar

object HotcellUtils {
  val coordinateStep = 0.01

  def CalculateCoordinate(inputString: String, coordinateOffset: Int): Int =
  {
    // Configuration variable:
    // Coordinate step is the size of each cell on x and y
    var result = 0
    coordinateOffset match
    {
      case 0 => result = Math.floor((inputString.split(",")(0).replace("(","").toDouble/coordinateStep)).toInt
      case 1 => result = Math.floor(inputString.split(",")(1).replace(")","").toDouble/coordinateStep).toInt
      // We only consider the data from 2009 to 2012 inclusively, 4 years in total. Week 0 Day 0 is 2009-01-01
      case 2 => {
        val timestamp = HotcellUtils.timestampParser(inputString)
        result = HotcellUtils.dayOfMonth(timestamp) // Assume every month has 31 days
      }
    }
    return result
  }

  def timestampParser (timestampString: String): Timestamp =
  {
    val dateFormat = new SimpleDateFormat("yyyy-MM-dd hh:mm:ss")
    val parsedDate = dateFormat.parse(timestampString)
    val timeStamp = new Timestamp(parsedDate.getTime)
    return timeStamp
  }

  def dayOfYear (timestamp: Timestamp): Int =
  {
    val calendar = Calendar.getInstance
    calendar.setTimeInMillis(timestamp.getTime)
    return calendar.get(Calendar.DAY_OF_YEAR)
  }

  def dayOfMonth (timestamp: Timestamp): Int =
  {
    val calendar = Calendar.getInstance
    calendar.setTimeInMillis(timestamp.getTime)
    return calendar.get(Calendar.DAY_OF_MONTH)
  }

  // YOU NEED TO CHANGE THIS PART

  def calculateNumAdjCells(min_x: Int, max_x: Int, min_y: Int, max_y: Int, min_z: Int, max_z: Int, x: Int, y: Int, z: Int): Int = {
    var adjAxBoundCount = 0

    // cell lies on x bound
    if (x == min_x || x == max_x) {
      adjAxBoundCount += 1
    }
    // cell lies on y bound
    if (y == min_y || y == max_y) {
      adjAxBoundCount += 1
    }
    // cell lies on x bound
    if (z == min_z || z == max_z) {
      adjAxBoundCount += 1
    }

    adjAxBoundCount match {
      // cell lies on one bound
      case 1 => 17
      //cell lies on two bounds
      case 2 => 11
      // cell lies on all three bounds
      case 3 => 7
      // cell lies on no bounds
      case _ => 26
    }
  }
  def gScore(numCells: Int, x: Int, y: Int, z: Int, adjacentHotcell: Int, cellNumber: Int , avg: Double, stdDev: Double): Double = {
    var adjHotCell: Double = adjacentHotcell.toDouble
    var numOfCells: Double = numCells.toDouble
    (cellNumber.toDouble - (avg * adjHotCell)) / (stdDev * math.sqrt((( adjHotCell * numOfCells) - (adjHotCell * adjHotCell)) / (numOfCells - 1.0)))
  }
}




