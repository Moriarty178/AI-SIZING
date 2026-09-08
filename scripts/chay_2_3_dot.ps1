# Chạy C2/2.3 (đọc ảnh bằng vision) trên MỘT ĐỢT hồ sơ — CẦN MÁY CÓ MODEL.
#
#   .\scripts\chay_2_3_dot.ps1 -UocTinh     # chỉ đếm, KHÔNG gọi model
#   .\scripts\chay_2_3_dot.ps1              # chạy thật
#   .\scripts\chay_2_3_dot.ps1 -Py "uv run python"      # ép trình thông dịch
#
# Danh sách dưới đây xếp theo SỐ ẢNH `console` đếm được offline ngày 2026-09-08 —
# console là nơi số đo tải nằm, tức là nơi 2.5 có gì để neo. Hai hồ sơ đã chạy
# (Vtag, PBH 4.0 bản 1) không có trong danh sách; đệm còn nguyên nếu chạy lại chúng.
#
# Mỗi hồ sơ ghi ra một file eval/reports/doc-anh-<tên>-<thời điểm>.json.
# Một hồ sơ hỏng KHÔNG làm dừng cả đợt — trừ hai trường hợp ở dưới.

param(
    [switch]$UocTinh,
    [int]$SongSong = 4,
    [string]$Model = "",
    [string]$Py = ""
)

$ErrorActionPreference = "Continue"
$goc = "danh_sach_sizings_da_duyet"

$hoSo = @(
    "cap bo sung VTracking 2.0.1 14716\Thiet ke va dinh co he thong_VTracking 2.0.1.docx",
    "cap moi PNM 57012\PL02_Sizing_callbot inbound CSKH_bosung2022_v1.1.DOCX",
    "cap moi callbot inbound CSKH_bosung videobot XMKH 35485\PL02_Sizing_callbot inbound CSKH_bosung videobot XMKH_v1.2v4.DOCX",
    "cap moi CALLBASE 44087\PL Sizing cap moi phan cung trien khai CallBase lay tin hieu qua Kafka_updated_v2.docx",
    "cap moi GSCG CSKH_bosung2022 23096\PL01_Sizing_giam sat cuoc goi CSKH_bosung2022_v1.0v3.docx",
    "cap moi PBH 4.0 20043\Sizing_PBH_4_v2.docx"
)

# --- chọn trình thông dịch --------------------------------------------------
# `py` và `python` có thể trỏ vào hai bản Python KHÁC nhau, và chỉ một bản có
# phụ thuộc. Đã gặp thật khi thử script này: `py` là Windows Store launcher,
# `python-docx` không có ở đó. Dò bằng cách thử import thật, không đoán theo tên.
function Chon-Python {
    param([string]$ep)
    if ($ep -ne "") { return $ep }
    foreach ($ung in @("python", "py", "uv run python")) {
        $phan = $ung.Split(" ")
        $lenh = $phan[0]
        if (-not (Get-Command $lenh -ErrorAction SilentlyContinue)) { continue }
        $doiSo = @()
        if ($phan.Count -gt 1) { $doiSo = $phan[1..($phan.Count - 1)] }
        $doiSo += @("-c", "import docx, PIL, openai")
        & $lenh @doiSo 2>$null
        if ($LASTEXITCODE -eq 0) { return $ung }
    }
    return ""
}

$pyCmd = Chon-Python $Py
if ($pyCmd -eq "") {
    Write-Host "KHÔNG tìm được Python có đủ phụ thuộc (python-docx, pillow, openai)." -ForegroundColor Red
    Write-Host "  Cài:  uv sync"
    Write-Host "  Hoặc ép:  .\scripts\chay_2_3_dot.ps1 -Py 'uv run python'"
    exit 2
}
$pyPhan = $pyCmd.Split(" ")
$pyLenh = $pyPhan[0]
$pyDau = @()
if ($pyPhan.Count -gt 1) { $pyDau = $pyPhan[1..($pyPhan.Count - 1)] }
Write-Host "trình thông dịch: $pyCmd"

# --- chạy đợt ---------------------------------------------------------------
$thanhCong = 0
$thatBai = @()
$batDau = Get-Date

for ($i = 0; $i -lt $hoSo.Count; $i++) {
    $h = $hoSo[$i]
    $duongDan = Join-Path $goc $h
    Write-Host ""
    Write-Host ("=" * 78)
    Write-Host ("[{0}/{1}] {2}" -f ($i + 1), $hoSo.Count, $h)
    Write-Host ("=" * 78)

    if (-not (Test-Path -LiteralPath $duongDan)) {
        # Hồ sơ chuyển chỗ / đổi tên: nói ra, đừng bỏ qua im lặng.
        Write-Host "  BỎ QUA — không tìm thấy file" -ForegroundColor Yellow
        $thatBai += $h
        continue
    }

    $doiSo = $pyDau + @("scripts\thu_doc_anh.py", $duongDan, "--song-song", $SongSong)
    if ($UocTinh) { $doiSo += "--uoc-tinh" }
    if ($Model -ne "") { $doiSo += @("--model", $Model) }

    & $pyLenh @doiSo
    $ma = $LASTEXITCODE
    if ($ma -eq 0) {
        $thanhCong++
        continue
    }
    $thatBai += $h

    # Mã 2 = cổng dừng của chính 2.3 (thiếu Pillow / chưa đặt vision_model).
    if ($ma -eq 2) {
        Write-Host ""
        Write-Host "DỪNG CẢ ĐỢT — cổng chặn ở trên cần xử lý trước." -ForegroundColor Red
        break
    }
    # Hồ sơ ĐẦU TIÊN hỏng khi chưa có hồ sơ nào chạy được ⇒ hỏng môi trường, không
    # phải hỏng riêng hồ sơ đó. Chạy tiếp chỉ đốt thời gian để nhận cùng một lỗi.
    if ($thanhCong -eq 0 -and $i -eq 0) {
        Write-Host ""
        Write-Host "DỪNG CẢ ĐỢT — hồ sơ đầu tiên đã hỏng, nhiều khả năng do môi trường." -ForegroundColor Red
        break
    }
}

$phut = ((Get-Date) - $batDau).TotalMinutes
Write-Host ""
Write-Host ("=" * 78)
Write-Host ("XONG: {0}/{1} hồ sơ · {2:N1} phút" -f $thanhCong, $hoSo.Count, $phut)
if ($thatBai.Count -gt 0) {
    Write-Host "Chưa chạy được:" -ForegroundColor Yellow
    foreach ($t in $thatBai) { Write-Host "  - $t" }
}
if (-not $UocTinh -and $thanhCong -gt 0) {
    Write-Host ""
    Write-Host "Các file cần gửi về (mới nhất trước):"
    Get-ChildItem eval\reports\doc-anh-*.json | Sort-Object LastWriteTime -Descending |
        Select-Object -First $thanhCong |
        ForEach-Object { Write-Host ("  {0}  ({1:N0} KB)" -f $_.Name, ($_.Length / 1KB)) }
}
