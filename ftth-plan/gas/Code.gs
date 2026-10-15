/**
 * FTTH Phố Đông - Apps Script web app (gắn vào file Google Sheets).
 * Giao diện: Index.html. Dữ liệu trạng thái: tab "Thuê bao" (cột "Mã căn hộ" và "Trạng thái").
 * Quyền: triển khai "Chạy với tư cách người dùng đang truy cập" => quyền đọc/ghi do chia sẻ file Sheets quyết định.
 */
var SHEET_NAME = 'Thuê bao';
var LOG_NAME = 'NhatKy';
var STATUSES = ['Chưa lắp', 'Đã đấu nối', 'Hoạt động', 'Sự cố'];

function doGet() {
  // Tìm tệp giao diện: tên chuẩn là "Index"; chấp nhận vài biến thể thường gặp khi tạo tệp.
  var names = ['Index', 'index', 'INDEX', 'Index.html', 'index.html'];
  var out = null;
  for (var k = 0; k < names.length && !out; k++) {
    try { out = HtmlService.createHtmlOutputFromFile(names[k]); } catch (e) { out = null; }
  }
  if (!out) {
    return HtmlService.createHtmlOutput(
      '<p style="font-family:sans-serif;padding:16px"><b>Chưa có tệp giao diện.</b><br>Trong Apps Script, bấm dấu + cạnh "Tệp" &gt; HTML, đặt tên đúng là <b>Index</b> (không gõ đuôi .html), dán nội dung file Index.html vào, lưu, rồi triển khai lại (Triển khai &gt; Quản lý bản triển khai &gt; bút &gt; Phiên bản mới).</p>');
  }
  return out
    .setTitle('FTTH Phố Đông')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function spreadsheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
    if (!id) throw new Error('Script chưa gắn với file Sheets (hoặc thiếu thuộc tính SHEET_ID).');
    ss = SpreadsheetApp.openById(id);
  }
  return ss;
}

function norm_(s) { return String(s).trim().toLowerCase(); }

function sheetInfo_() {
  var ss = spreadsheet_();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) throw new Error('Không thấy tab "' + SHEET_NAME + '" trong file Sheets.');
  var hdr = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(norm_);
  var code = hdr.indexOf('mã căn hộ') + 1, status = hdr.indexOf('trạng thái') + 1;
  if (!code || !status) throw new Error('Tab "' + SHEET_NAME + '" thiếu cột "Mã căn hộ" hoặc "Trạng thái" ở dòng 1.');
  return { ss: ss, sh: sh, code: code, status: status, rows: Math.max(0, sh.getLastRow() - 1) };
}

function email_() {
  try { return Session.getActiveUser().getEmail() || ''; } catch (e) { return ''; }
}

/** true / false nếu xác định được; null nếu không rõ (khi đó giao diện vẫn cho thử ghi). */
function canEdit_(ss) {
  try {
    var me = email_().toLowerCase();
    if (!me) return null;
    var owner = ss.getOwner();
    if (owner && owner.getEmail().toLowerCase() === me) return true;
    var eds = ss.getEditors().map(function (u) { return u.getEmail().toLowerCase(); });
    return eds.indexOf(me) >= 0;
  } catch (e) { return null; }
}

/** Trả {statuses: {mã: trạng thái}, user, canEdit}. */
function getStatuses() {
  var i = sheetInfo_();
  var statuses = {};
  if (i.rows > 0) {
    var codes = i.sh.getRange(2, i.code, i.rows, 1).getValues();
    var sts = i.sh.getRange(2, i.status, i.rows, 1).getValues();
    for (var r = 0; r < i.rows; r++) {
      var c = String(codes[r][0]).trim().toUpperCase(), s = String(sts[r][0]).trim();
      if (c && STATUSES.indexOf(s) >= 0) statuses[c] = s;
    }
  }
  return { statuses: statuses, user: email_(), canEdit: canEdit_(i.ss) };
}

/** Đổi trạng thái 1 căn hộ, ghi nhật ký (tab NhatKy). Ném lỗi nếu không có quyền ghi. */
function setStatus(code, status) {
  code = String(code).trim().toUpperCase();
  if (STATUSES.indexOf(status) < 0) throw new Error('Trạng thái không hợp lệ: ' + status);
  var i = sheetInfo_();
  var lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    var codes = i.sh.getRange(2, i.code, i.rows, 1).getValues();
    var row = -1;
    for (var r = 0; r < codes.length; r++) { if (String(codes[r][0]).trim().toUpperCase() === code) { row = r + 2; break; } }
    if (row < 0) throw new Error('Không thấy mã căn hộ ' + code);
    var cell = i.sh.getRange(row, i.status);
    var old = String(cell.getValue());
    cell.setValue(status);
    log_(i.ss, code, old, status);
  } finally { lock.releaseLock(); }
  return { ok: true };
}

function log_(ss, code, oldStatus, newStatus) {
  var lg = ss.getSheetByName(LOG_NAME);
  if (!lg) { lg = ss.insertSheet(LOG_NAME); lg.appendRow(['Thời gian', 'Tài khoản', 'Mã căn hộ', 'Trạng thái cũ', 'Trạng thái mới']); }
  lg.appendRow([new Date(), email_(), code, oldStatus, newStatus]);
}
