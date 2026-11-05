"""Dữ kiện thang do người dùng chọn, chưa áp vào lượng hoặc phê duyệt."""
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .project_files import SelectedFile


class StairLocation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    page: int | None = Field(default=None, ge=1)
    sheet: str | None = None
    handle: str | None = None
    note: str | None = None

    @model_validator(mode='after')
    def _location_required(self):
        if self.page is None and not any(v and v.strip() for v in (self.sheet, self.handle, self.note)):
            raise ValueError('Cần vị trí hoặc mô tả nguồn của dữ kiện.')
        return self


class StairFact(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field: Literal['from_floor', 'to_floor', 'z_from_mm', 'z_to_mm', 'run_mm', 'rise_mm', 'step_count',
                   'width_mm', 'tread_mm', 'riser_mm', 'waist_thickness_mm', 'thickness_basis',
                   'area_m2', 'thickness_mm', 'ownership', 'steps_material']
    value: float | str | None = None
    source: SelectedFile | None = None
    location: StairLocation | None = None

    @model_validator(mode='after')
    def _fact(self):
        if self.value is None:
            if self.source is not None or self.location is not None:
                raise ValueError('Dữ kiện chưa có giá trị không gắn nguồn như đã xác nhận.')
            return self
        if self.source is None or self.location is None:
            raise ValueError('Giá trị người dùng chọn cần phiên bản tệp và vị trí nguồn.')
        if self.field == 'steps_material':
            if self.value not in ('masonry', 'concrete', 'unknown'):
                raise ValueError('Vật liệu bậc không hợp lệ.')
        elif self.field == 'ownership':
            if self.value not in ('stair', 'floor', 'beam', 'unknown'):
                raise ValueError('Phạm vi phân bổ chiếu nghỉ không hợp lệ.')
        elif self.field == 'thickness_basis':
            if self.value != 'normal':
                raise ValueError('Dày bản thang chỉ nhận theo phương vuông góc.')
        elif self.field in ('from_floor', 'to_floor'):
            if not isinstance(self.value, str) or not self.value.strip() or len(self.value) > 120:
                raise ValueError('Tên tầng không hợp lệ.')
        elif (not isinstance(self.value, float) or not math.isfinite(self.value)
              or (self.field not in ('z_from_mm', 'z_to_mm') and self.value <= 0)
              or (self.field == 'step_count' and not self.value.is_integer())):
            raise ValueError('Giá trị số của thang không hợp lệ.')
        return self


class StairPart(BaseModel):
    model_config = ConfigDict(extra='forbid')
    part_id: str = Field(min_length=1, max_length=120)
    kind: Literal['stair', 'flight', 'landing', 'steps']
    facts: list[StairFact] = Field(default_factory=list, max_length=32)

    @model_validator(mode='after')
    def _unique_facts(self):
        if len({f.field for f in self.facts}) != len(self.facts):
            raise ValueError('Một bộ phận không thể có hai dữ kiện cùng trường.')
        allowed = {'stair': {'from_floor', 'to_floor', 'steps_material', 'waist_thickness_mm', 'thickness_basis'},
                   'flight': {'z_from_mm', 'z_to_mm', 'run_mm', 'rise_mm', 'step_count', 'width_mm', 'tread_mm',
                              'riser_mm', 'waist_thickness_mm', 'thickness_basis'},
                   'landing': {'z_from_mm', 'z_to_mm', 'area_m2', 'thickness_mm', 'ownership'},
                   'steps': {'step_count', 'width_mm', 'tread_mm', 'riser_mm', 'steps_material'}}
        if any(f.field not in allowed[self.kind] for f in self.facts):
            raise ValueError('Dữ kiện không phù hợp với loại bộ phận thang.')
        return self


class StairEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    profile_version: int = Field(ge=1)
    stair_id: str = Field(min_length=1, max_length=120)
    parts: list[StairPart] = Field(min_length=1, max_length=50)

    @model_validator(mode='after')
    def _unique_parts(self):
        if not self.stair_id.strip() or any(not part.part_id.strip() for part in self.parts):
            raise ValueError('Cần định danh thang và bộ phận.')
        if len({part.part_id for part in self.parts}) != len(self.parts):
            raise ValueError('Định danh bộ phận thang bị trùng.')
        if sum(part.kind == 'stair' for part in self.parts) > 1:
            raise ValueError('Một thang chỉ nhận một phần phạm vi chung.')
        return self


def stair_from_evidence(body: StairEvidenceRequest):
    """Chuyển lựa chọn tường minh sang model tính, không ghép thêm hình học."""
    from ..rough.stairs import Stair

    def source(fact):
        ref, loc = fact.source, fact.location
        position = ', '.join(f'{key}={value}' for key, value in loc.model_dump().items() if value is not None)
        return (f"Người dùng chọn, chưa kiểm: {ref.role} file_id={ref.file_id}, revision_id={ref.revision_id}, "
                f"sha256={ref.sha256}, {position}")

    stair = {'id': body.stair_id, 'source': 'manual', 'flights': None, 'landings': None}
    unmapped, materials = [], []
    scope = next((part for part in body.parts if part.kind == 'stair'), None)
    if scope:
        facts = {f.field: f for f in scope.facts if f.value is not None}
        for key in ('from_floor', 'to_floor'):
            if key in facts:
                stair[key] = facts[key].value
        if 'from_floor' in facts and 'to_floor' in facts:
            stair['scope_source'] = source(facts['from_floor']) + ' | ' + source(facts['to_floor'])
        elif 'from_floor' in facts or 'to_floor' in facts:
            stair.pop('from_floor', None)
            stair.pop('to_floor', None)
            unmapped.append('Chưa đủ nguồn cho cả tầng đầu và tầng cuối.')
        for field, destination in (('waist_thickness_mm', 'waist_thickness_mm'),
                                   ('thickness_basis', 'waist_thickness_basis')):
            if field in facts:
                stair[destination] = facts[field].value
        if 'waist_thickness_mm' in facts:
            stair['waist_thickness_source'] = source(facts['waist_thickness_mm'])
            if 'thickness_basis' in facts:
                stair['waist_thickness_source'] += ' | ' + source(facts['thickness_basis'])
        if 'steps_material' in facts:
            materials.append(facts['steps_material'])
    for part in body.parts:
        facts = {f.field: f for f in part.facts if f.value is not None}
        if part.kind == 'steps':
            if 'steps_material' in facts:
                materials.append(facts['steps_material'])
            if any(f.field != 'steps_material' and f.value is not None for f in part.facts):
                unmapped.append(f'{part.part_id}: hình học bậc chưa gắn vào một vế được chọn.')
            continue
        if part.kind not in ('flight', 'landing'):
            continue
        keys = (('run_mm', 'rise_mm', 'width_mm', 'waist_thickness_mm', 'thickness_basis',
                 'step_count', 'tread_mm', 'riser_mm') if part.kind == 'flight'
                else ('area_m2', 'thickness_mm', 'ownership'))
        item = {'id': part.part_id, 'field_sources': {}}
        for field, fact in facts.items():
            if field in keys:
                item[field] = fact.value
                item['field_sources'][field] = source(fact)
            else:
                unmapped.append(f'{part.part_id}: chưa ánh xạ {field} vào model tính.')
        group = 'flights' if part.kind == 'flight' else 'landings'
        if stair[group] is None:
            stair[group] = []
        stair[group].append(item)
    if len(materials) == 1:
        stair['steps_material'] = materials[0].value
        stair['steps_material_source'] = source(materials[0])
    elif len(materials) > 1:
        unmapped.append('Nhiều nguồn vật liệu bậc; cần chọn duy nhất cho thang.')
    return Stair.model_validate(stair).model_dump(), unmapped
