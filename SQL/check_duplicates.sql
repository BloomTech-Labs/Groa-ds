-- checks database for duplicates

SELECT username, movie_id, review_title, COUNT(*)
FROM reviews
GROUP BY username, movie_id, review_title
HAVING COUNT(*) > 1
ORDER BY count(*) DESC
LIMIT 100;