import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('import_housing_estimates', Path(__file__).parents[1]/'scripts/import_housing_estimates.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_quantity_number_and_restricted_arithmetic():
    assert module.number('4,802.780') == 4802.78
    assert module.number('104.101') == 104.101
    assert module.number('KHỐI LƯỢNG') is None
    assert module.formula_value('BM-1: 2*7,29*1*1,15*1,3') == 2*7.29*1*1.15*1.3
    assert module.formula_value('__import__("os").system("exit")') is None
    assert module.formula_value('1/0') is None


def test_leading_legacy_mark_in_downloaded_drawing():
    from optimat.drawing.encoding import vni_to_unicode, ma_cu_2_to_unicode
    assert vni_to_unicode('ÙMAËT') == 'ÙMẶT'
    assert ma_cu_2_to_unicode('ÒMÀÛT') == 'ÒMẶT'


def test_continuation_and_repeated_stt_have_distinct_source_ids():
    rows=[['1','TT','Đào đất móng','m³','104.101','110,000','11,451,110',''],
          ['','','BM-1: 2*7,29*1*1,15*1,3','','21.797','','','']]
    next_page=[['STT','MÃ HIỆU','NỘI DUNG','ĐƠN VỊ','KHỐI LƯỢNG','','',''],
               ['','','BM-2: 2*4,89*1*1,15*1,3','','14.621','','',''],
               ['','TC','Cộng','','','','',''],
               ['1','TT','Xây tường','m³','12.5','1','12.5','']]
    works, raw = module.parse_rows([(3,[rows]),(4,[next_page])],'case')
    assert len(works)==2 and len(raw)==6
    assert works[0]['source']['page']==3
    assert works[0]['details'][1]['source']['page']==4
    assert works[0]['details'][0]['arithmetic_match'] is True
    assert works[0]['id'] != works[1]['id']
    assert works[1]['ma_cong_tac']=='XAY'
    assert works[0]['verification_status']=='chua_kiem'


def test_blank_rate_code_is_still_an_item_and_rounding_uses_printed_precision():
    works,_=module.parse_rows([(37,[[['17','','Aptomat chống rò','cái','2','10','20'],
                                   ['','','2,91*0,11*3,4*1,1','','1.20','','']]])],'case')
    assert len(works)==1 and works[0]['ma_dinh_muc']==''
    assert works[0]['details'][0]['arithmetic_match'] is True
