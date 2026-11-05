"""Display bounds không thay phạm vi nhận diện hoặc gốc overlay."""
import copy
import math
import re

import ezdxf
import pytest

from optimat.drawing.dxf_reader import Drawing,TextItem,read_dxf
from optimat.drawing.render import DrawingRenderer
from optimat.drawing.viewer import view_payload
from optimat.schemas import TakeoffResult,PlanTakeoff


def result():
    return TakeoffResult(walls=[],groups=[],openings_count=0)


def source(tmp_path,kind="arc",unit=4):
    doc=ezdxf.new();doc.header["$INSUNITS"]=unit
    k=1 if unit==4 else .001
    m=doc.modelspace();m.add_line((0,0),(1000*k,1000*k))
    if kind=="arc":m.add_arc((6000*k,0),600*k,0,90)
    elif kind=="text":m.add_text("REF",dxfattribs={"insert":(5000*k,5000*k),"height":200*k})
    elif kind=="circle":m.add_circle((6000*k,0),400*k)
    elif kind=="small_arc":m.add_arc((500*k,500*k),100*k,0,90)
    elif kind=="insert":
        b=doc.blocks.new("NOTE",base_point=(-120000*k,0))
        b.add_arc((-120000*k,0),600*k,0,90)
        b.add_text("REF",dxfattribs={"insert":(-120000*k,0),"height":200*k})
        m.add_blockref("NOTE",(6000*k,0))
    path=tmp_path/f"{kind}_{unit}.dxf";doc.saveas(path)
    return read_dxf(path)


def contains(box,x,y):
    return box[0]<=x<=box[2] and box[1]<=y<=box[3]


def starts(svg):
    a,_,_,d,e,f=map(float,re.search(r"matrix\(([^)]*)\)",svg).group(1).split(","))
    return [(a*float(x)+e,d*float(y)+f) for x,y in re.findall(r'<path d="M (-?[\d.]+) (-?[\d.]+)',svg)]


@pytest.mark.parametrize("kind",["arc","text","insert"])
def test_whole_view_keeps_remote_native_geometry_without_changing_analysis_bbox(tmp_path,kind):
    drawing=source(tmp_path,kind)
    measurement=result();before=measurement.model_dump();segments=copy.deepcopy(drawing.segments)
    data=view_payload(drawing,measurement,"SYNTHETIC")
    p=data["plans"][0]
    assert p["bbox_mm"]==[0,0,1000,1000] and p["size"]==[1000,1000] and p["origin"]==[0,1000]
    assert p["cad"].count("<path")==data["overview"]["cad"].count("<path")>=2
    x,y=(5000,-4000) if kind=="text" else (6000,1000)
    assert contains(p["display_bbox"],x,y) and contains(data["overview"]["display_bbox"],x,y)
    assert data["overview"]["origin"]==[0,1000]
    assert measurement.model_dump()==before and drawing.segments==segments


def test_small_arc_is_display_data_not_filtered_by_door_threshold(tmp_path):
    d=source(tmp_path,"small_arc")
    p=view_payload(d,result(),"R100",cad=False)["plans"][0]
    assert len(d.arcs)==len(p["arcs"])==1
    assert p["arcs"][0][:3]==[500,500,100]


def test_explicit_plan_is_bounded_but_whole_overview_contains_neighbor(tmp_path):
    d=source(tmp_path,"arc")
    plan=PlanTakeoff(name="Mặt bằng A",height_source="chưa có",bbox=[0,0,1000,1000],result=result())
    before=plan.model_dump()
    data=view_payload(d,[plan],"SYNTHETIC")
    p=data["plans"][0]
    assert p["cad"].count("<path")==1
    assert p["display_bbox"]==[-1500,-1500,2500,2500]
    assert data["overview"]["cad"].count("<path")==2
    assert contains(data["overview"]["display_bbox"],6600,1000)
    assert plan.model_dump()==before
    fallback=view_payload(d,[plan],"SYNTHETIC",cad=False)["plans"][0]
    assert fallback["display_bbox"]==p["display_bbox"]


def test_named_whole_plan_does_not_crop_to_recognition_box(tmp_path):
    d=source(tmp_path,"arc")
    plan=PlanTakeoff(name="Toàn bộ bản vẽ",height_source="chưa có",bbox=[0,0,1000,1000],result=result())
    p=view_payload(d,[plan],"SYNTHETIC")["plans"][0]
    assert p["cad"].count("<path")==2 and contains(p["display_bbox"],6600,1000)


@pytest.mark.parametrize("unit",[4,6])
def test_native_arc_coordinates_and_bounds_stay_in_viewer_mm(tmp_path,unit):
    d=source(tmp_path,"arc",unit)
    p=view_payload(d,result(),"SYNTHETIC")["plans"][0]
    assert p["origin"]==[0,1000] and contains(p["display_bbox"],6600,1000)
    assert any(math.dist(v,(6600,1000))<.05 for v in starts(p["cad"]))
    assert p["display_size"]==pytest.approx([p["display_bbox"][2]-p["display_bbox"][0],p["display_bbox"][3]-p["display_bbox"][1]])


def test_circle_native_bounds_cover_curve_beyond_segment_approximation(tmp_path):
    d=source(tmp_path,"circle")
    p=view_payload(d,result(),"SYNTHETIC")["plans"][0]
    assert contains(p["display_bbox"],6000,1400)


def test_crop_render_does_not_mutate_full_recorded_extent(tmp_path):
    d=source(tmp_path,"arc");renderer=DrawingRenderer(d.doc,d.unit_scale)
    before=renderer.bounds_mm
    renderer.view((0,0,1000,1000),(0,1000))
    whole=renderer.view(None,(0,1000))
    assert renderer.bounds_mm==before and whole.svg.count("<path")==2
    assert contains(whole.display_bbox,6600,1000)


def test_text_only_without_native_doc_has_finite_fallback_bounds():
    d=Drawing(segments=[],texts=[TextItem("REF",5000,5000,"TEXT","unicode",200)],blocks=[],hatches=[],layers=[],layer_classes={},unit_scale=1,warnings=[])
    p=view_payload(d,result(),"SYNTHETIC",cad=False)["plans"][0]
    assert p["bbox_mm"]==[0,0,1,1] and p["origin"]==[0,1]
    assert all(math.isfinite(v) for v in p["display_bbox"])
    assert contains(p["display_bbox"],5000,-4999)


def test_insert_origin_is_not_a_visible_point_for_fit_bounds(tmp_path):
    doc=ezdxf.new();doc.header["$INSUNITS"]=4
    doc.modelspace().add_line((0,0),(1000,1000))
    b=doc.blocks.new("REMOTE_ORIGIN",base_point=(1000000,0));b.add_line((0,0),(1000,0))
    doc.modelspace().add_blockref("REMOTE_ORIGIN",(1000000,0))
    path=tmp_path/"remote_origin.dxf";doc.saveas(path);d=read_dxf(path)
    p=view_payload(d,result(),"SYNTHETIC")["plans"][0]
    assert p["display_bbox"][2]<10000
