async function checkAdviceScope() {
  const { default: assert } = await import('node:assert/strict');
  const fs = await import('node:fs');
  const path = await import('node:path');
  const { default: Module } = await import('node:module');
  const { default: ts } = await import('typescript');

  const file = path.resolve(__dirname, '../src/app/(user)/dieu-chinh/advice-scope.ts');
  const loaded = new Module(file, module);
  loaded._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  }).outputText, file);
  const { adviceScope } = loaded.exports;

  const works = ['COT', 'DAM', 'COT'].map((code, i) => ({
    code, plan: 'T1', name: code, element: String(i), quantity: 1, unit: 'm³', missing: []
  }));
  const use = (rowIndex, quantity, via) => ({ work: works[rowIndex].code, plan: 'T1', rowIndex, quantity, via });
  const grouped = { work: 'COT', plan: 'T1', quantity: 9, via: 'Tổng các cột' };
  function scope(uses, { checked = [0], selected = null, total = 7, waste = 7.7, missing = [] } = {}) {
    const work = { projectUid: 'p', drawingId: 'd', reviewId: 'r', result: { works, materials: [{
      material_id: 'XM', name: 'Xi măng', unit: 'tấn', quantity: total, quantity_with_waste: waste,
      complete: true, missing, uses
    }] } };
    return adviceScope(work, { checked, partial: true }, selected, 'v');
  }
  function checkPartial(line, quantity, sources) {
    assert.equal(line.quantity, quantity);
    assert.equal(line.quantity_with_waste, null);
    assert.equal(line.complete, false);
    assert.ok(line.missing.length);
    assert.deepEqual(line.sources, sources);
  }

  const mixed = scope([use(0, 3, 'Nguồn cột'), use(1, 4, 'Nguồn dầm')]);
  const line = mixed.materials[0];
  checkPartial(line, 3, ['Nguồn cột']);
  assert.equal(line.lineId, 'm0');
  assert.deepEqual(mixed.binding, { projectUid: 'p', drawingId: 'd', reviewId: 'r', materialRevision: 'v' });
  assert.deepEqual(mixed.works.map(row => row.checked), [true, false, false]);
  assert.deepEqual(line.uses.map(u => [u.quantity, u.via]), [[3, 'Nguồn cột'], [null, '']]);

  checkPartial(scope([use(0, 0, 'Số 0 đã kiểm'), use(1, null, 'Chưa kiểm')]).materials[0], 0, ['Số 0 đã kiểm']);
  checkPartial(scope([use(1, 4, 'Chưa kiểm')]).materials[0], null, []);
  checkPartial(scope([use(0, null, 'Quy cách chưa đủ'), use(1, 4, 'Chưa kiểm')]).materials[0], null, ['Quy cách chưa đủ']);
  const part = scope([use(0, 3, 'Đã tính'), use(0, null, 'Thiếu kích thước'), use(1, 4, 'Chưa kiểm')], { total: null });
  checkPartial(part.materials[0], 3, ['Đã tính', 'Thiếu kích thước']);
  assert.equal(part.materials[0].uses[1].quantity, null);
  checkPartial(scope([use(0, 2, 'Cộng'), use(0, -3, 'Trừ'), use(1, 4, 'Chưa kiểm')]).materials[0], -1, ['Cộng', 'Trừ']);

  checkPartial(scope([grouped]).materials[0], null, []);
  checkPartial(scope([grouped, use(1, 4, 'Chưa kiểm')], { checked: [0, 2] }).materials[0], 9, ['Tổng các cột']);
  const ambiguous = scope([grouped, use(0, 2, 'Một cột')], { checked: [0, 2], selected: 0 });
  checkPartial(ambiguous.materials[0], null, []);
  assert.ok(ambiguous.materials[0].uses.every(u => u.quantity === null && u.via === ''));
  const selectedLine = scope([use(0, 3, 'Cột'), use(1, 4, 'Dầm')], { selected: 0 }).materials[0];
  assert.equal(selectedLine.quantity, 3);
  assert.equal(selectedLine.quantity_with_waste, null);
  assert.deepEqual(selectedLine.sources, ['Cột']);
  works[0].missing = ['Chỉ A thiếu sàn', 'Cả A và B thiếu chứng từ'];
  works[2].missing = ['Chỉ B thiếu cao độ', 'Cả A và B thiếu chứng từ'];
  const sharedUses = [use(0, null, 'Đoạn A'), use(2, 0.29, 'Đoạn B')];
  for (const id of ['Bê tông thương phẩm', 'Cấp phối trộn tại chỗ']) {
    const materialGap = id + ': thiếu đơn giá áp dụng';
    const missing = [...new Set([...works[0].missing, ...works[2].missing, materialGap])];
    const fromB = scope(sharedUses, { checked:[2], selected:2, missing }).materials[0];
    assert.equal(fromB.quantity, 0.29);
    assert.ok(!fromB.missing.includes('Chỉ A thiếu sàn'), 'Đoạn A không thuộc phạm vi B');
    assert.ok([...works[2].missing,materialGap].every(s=>fromB.missing.includes(s)));
    const all = scope(sharedUses, { checked:[0,2], missing }).materials[0];
    assert.deepEqual(all.missing, missing);
  }
  works[0].missing = []; works[2].missing = [];
  checkPartial(scope([{ ...use(1, 4, 'Sai dòng'), rowIndex: 0 }]).materials[0], null, []);

  // Tổng chuẩn có thể giữ độ chính xác khác các phần góp đã làm tròn.
  const full = scope([use(0, 3, 'Cột'), use(1, 4, 'Dầm')], { checked: [0, 1], total: 7.001, waste: 7.701 }).materials[0];
  assert.equal(full.quantity, 7.001);
  assert.equal(full.quantity_with_waste, 7.701);
  assert.equal(full.complete, true);
  assert.deepEqual(full.sources, ['Cột', 'Dầm']);
  console.log('PASS: phần góp đã kiểm, số 0, lượng thiếu, khoản trừ, nguồn gộp và tổng chuẩn.');
}

checkAdviceScope().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
