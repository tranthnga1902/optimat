from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewOpening, ReviewPlan, ReviewWall, compute_review

wall = ReviewWall(id="B", cls="220", x1=0, y1=0, x2=3000, y2=0, masonry=False)
for x, y in [(0, 0), (-12.5, None), (None, -30)]:
    opening = ReviewOpening(id="N1", wall="B", x=x, y=y, w=None, h=2000)
    plan = ReviewPlan(file="SYN", plan="T1", height_mm=3000, walls=[wall], openings=[opening])
    result = compute_review(plan, Catalog.from_csv())
    saved = result.model_dump(mode="json")["outside_masonry_openings"][0]
    assert (saved["id"], saved["wall"], saved["x"], saved["y"], saved["w"]) == ("N1", "B", x, y, None)
    assert ReviewOpening.model_validate(saved).model_dump() == opening.model_dump()
print("PASS: outside masonry giữ ID/parent/null/0/âm/một trục và JSON restore (synthetic, không DB)")
