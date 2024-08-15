CREATE TABLE query1 AS SELECT genres.name as name, COUNT(hasagenre.movieid) as moviecount
FROM genres, hasagenre
WHERE hasagenre.genreid = genres.genreid
GROUP BY genres.genreid;

CREATE TABLE query2 AS SELECT genres.name as name, AVG(ratings.rating) as rating
FROM genres, hasagenre, ratings
WHERE genres.genreid = hasagenre.genreid AND hasagenre.movieid = ratings.movieid
GROUP BY genres.genreid;

CREATE TABLE query3 AS SELECT movies.title as title, count(ratings.rating) as countofratings
FROM movies, ratings
WHERE movies.movieid = ratings.movieid
GROUP BY movies.title
HAVING count(ratings.rating) >= 10;

CREATE TABLE query4 AS SELECT movies.movieid as movieid,  movies.title as title
FROM movies, hasagenre, genres
WHERE genres.name = 'Comedy' and hasagenre.genreid = genres.genreid and movies.movieid = hasagenre.movieid; 


CREATE TABLE query5 AS SELECT movies.title as title, avg(ratings.rating) as average
FROM movies, ratings
WHERE movies.movieid = ratings.movieid
GROUP by movies.movieid;

CREATE TABLE query6 AS SELECT avg(ratings.rating) as average
FROM ratings
WHERE ratings.movieid IN (
	SELECT hasagenre.movieid
	FROM hasagenre, genres
	WHERE genres.name = 'Comedy' AND hasagenre.genreid = genres.genreid
);

CREATE TABLE query7 AS SELECT avg(ratings.rating) as average
FROM ratings
WHERE ratings.movieid  IN (
	SELECT hasagenre.movieid
	FROM hasagenre, genres
	WHERE genres.name = 'Comedy' and hasagenre.genreid = genres.genreid
	INTERSECT
	SELECT hasagenre.movieid
	FROM hasagenre, genres
	WHERE genres.name = 'Romance' and hasagenre.genreid = genres.genreid
); 

CREATE TABLE query8 AS SELECT avg(ratings.rating) as average
FROM ratings
WHERE ratings.movieid  IN (
	SELECT hasagenre.movieid
	FROM hasagenre, genres
	WHERE genres.name = 'Romance' and hasagenre.genreid = genres.genreid
	EXCEPT
	SELECT hasagenre.movieid
	FROM hasagenre, genres
	WHERE genres.name = 'Comedy' and hasagenre.genreid = genres.genreid
);

CREATE TABLE query9 AS SELECT ratings.movieid as movieid, ratings.rating as rating
FROM ratings
WHERE ratings.userid = :v1;
