-- ============================================================
-- cek_struktur_table.sql
-- TIDAK membuat database/table baru. Hanya untuk MENGECEK bahwa
-- struktur table "data" di database "salt_data" sudah sesuai
-- dengan yang dibutuhkan receive_data.php.
--
-- Jalankan di phpMyAdmin: pilih database salt_data -> tab SQL ->
-- paste ini -> Go.
-- ============================================================

DESCRIBE data;

-- Hasil yang diharapkan (nama & tipe kolom):
--   data_id   | int          | PRI | auto_increment
--   time      | timestamp    |     | DEFAULT CURRENT_TIMESTAMP
--   wtemp     | float        |
--   atemp     | float        |
--   humidity  | float        |
--   wlevel    | float        |
--   salinity  | float        |
--   box_id    | int          |

-- Cek juga privilege user dbaccess (opsional, untuk memastikan
-- dbaccess minimal punya izin INSERT & SELECT ke table ini):
SHOW GRANTS FOR 'dbaccess'@'localhost';
