-- deletes duplicate reviews
-- DO NOT USE; this needs an index in the WHERE so that it deletes all but one duplicate record.

delete
from reviews a
	using reviews b
where
	-- a.index < b.index
	a.username = b.username
	and a.review_title = b.review_title
