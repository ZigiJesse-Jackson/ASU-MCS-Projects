package cse512

object HotzoneUtils {
  def convert(element: Array[String]): Array[Double] = {
    val res = new Array[Double](element.length)
    for (i <- 0 to element.length-1)
      res(i) = element(i).toDouble
    return res
  }

  def ST_Contains(queryRectangle: String, pointString: String): Boolean = {
    // YOU NEED TO CHANGE THIS PART
    val rectanglePoints = convert(queryRectangle.split(','));
    val point = convert(pointString.split(','));

    if (
      rectanglePoints(0) <= point(0) && point(0) <= rectanglePoints(2) &&
        rectanglePoints(1) <= point(1) && point(1) <= rectanglePoints(3)
    ) return true;

    return false // YOU NEED TO CHANGE THIS PART
  }

  // YOU NEED TO CHANGE THIS PART

}
