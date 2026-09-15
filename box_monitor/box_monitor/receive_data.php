<?php
/**
 * receive_data.php
 * =================
 * Menerima data sensor dari Raspberry Pi (POST, format JSON) lalu
 * menyimpannya ke database MySQL yang SUDAH ADA: salt_data.data
 *
 * Dipanggil otomatis oleh server.py di Raspberry Pi setiap ada data
 * sensor baru masuk. Tidak perlu diakses manual lewat browser.
 */

header("Content-Type: application/json");

// ------------------------------------------------------------------
// KONFIGURASI - SESUAIKAN BAGIAN INI
// ------------------------------------------------------------------
// MySQL ada di SATU SERVER YANG SAMA dengan Apache/PHP ini (103.163.184.28),
// jadi host-nya "localhost", BUKAN IP server lain.
define("DB_HOST", "localhost");
define("DB_NAME", "salt_data");    // database yang SUDAH ADA, jangan diganti
define("DB_USER", "dbaccess");
define("DB_PASS", "cs.binus@23paskal");

// HARUS SAMA PERSIS dengan SERVER_API_KEY di config.py Raspberry Pi
define("API_KEY", "boxmonitor-rahasia-ganti-ini");

// ------------------------------------------------------------------
// Hanya terima method POST
// ------------------------------------------------------------------
if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Method not allowed, gunakan POST."]);
    exit;
}

// ------------------------------------------------------------------
// Ambil & decode body JSON
// ------------------------------------------------------------------
$raw_body = file_get_contents("php://input");
$data = json_decode($raw_body, true);

if (!is_array($data)) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Body bukan JSON yang valid."]);
    exit;
}

// ------------------------------------------------------------------
// Cek API key (supaya tidak sembarang orang bisa isi database ini)
// ------------------------------------------------------------------
if (!isset($data["api_key"]) || $data["api_key"] !== API_KEY) {
    http_response_code(401);
    echo json_encode(["status" => "error", "message" => "API key salah/tidak ada."]);
    exit;
}

// ------------------------------------------------------------------
// Validasi field sensor yang wajib ada
// (catatan: "timestamp" TIDAK wajib & TIDAK dipakai untuk INSERT,
// karena kolom "time" di tabel sudah otomatis CURRENT_TIMESTAMP)
// ------------------------------------------------------------------
$required_fields = ["box_id", "salinitas", "air_temp", "water_temp", "humidity", "water_level"];
foreach ($required_fields as $field) {
    if (!isset($data[$field])) {
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Field '$field' tidak ada."]);
        exit;
    }
}

// ------------------------------------------------------------------
// Mapping box_id string -> integer
// Raspberry Pi mengirim "box001", "box002", dst.
// Kolom box_id di database bertipe INT, jadi ambil angkanya saja.
// "box003" -> 3
// ------------------------------------------------------------------
function extract_box_number($box_id_str) {
    if (preg_match('/(\d+)/', $box_id_str, $matches)) {
        return intval($matches[1]);
    }
    return null;
}

$box_id_raw = trim($data["box_id"]);
$box_id_int = extract_box_number($box_id_raw);

if ($box_id_int === null) {
    http_response_code(400);
    echo json_encode([
        "status" => "error",
        "message" => "box_id '$box_id_raw' tidak mengandung angka, tidak bisa di-mapping ke integer.",
    ]);
    exit;
}

// ------------------------------------------------------------------
// Mapping nama field JSON (Raspberry Pi) -> nama kolom database
//   water_temp  -> wtemp
//   air_temp    -> atemp
//   humidity    -> humidity
//   water_level -> wlevel
//   salinitas   -> salinity
//   box_id      -> box_id (sudah di-mapping ke integer di atas)
// ------------------------------------------------------------------
$wtemp    = floatval($data["water_temp"]);
$atemp    = floatval($data["air_temp"]);
$humidity = floatval($data["humidity"]);
$wlevel   = floatval($data["water_level"]);
$salinity = floatval($data["salinitas"]);

// ------------------------------------------------------------------
// Simpan ke database (pakai prepared statement, aman dari SQL injection)
// Kolom data_id & time TIDAK diisi manual -> MySQL yang otomatis
// mengisi (AUTO_INCREMENT & DEFAULT CURRENT_TIMESTAMP).
// ------------------------------------------------------------------
try {
    $pdo = new PDO(
        "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
        DB_USER,
        DB_PASS,
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
    );

    $stmt = $pdo->prepare(
        "INSERT INTO data (wtemp, atemp, humidity, wlevel, salinity, box_id)
         VALUES (:wtemp, :atemp, :humidity, :wlevel, :salinity, :box_id)"
    );

    $stmt->execute([
        ":wtemp"    => $wtemp,
        ":atemp"    => $atemp,
        ":humidity" => $humidity,
        ":wlevel"   => $wlevel,
        ":salinity" => $salinity,
        ":box_id"   => $box_id_int,
    ]);

    http_response_code(200);
    echo json_encode([
        "status"  => "ok",
        "message" => "Data box '$box_id_raw' berhasil disimpan.",
        "data_id" => $pdo->lastInsertId(),
    ]);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        "status" => "error",
        "message" => "Gagal menyimpan ke database: " . $e->getMessage(),
    ]);
}
