"""5.0 — lớp lưu trữ của Giai đoạn 5 (vòng lặp thẩm định – sửa – phê duyệt).

Ba module, tách theo thứ ai được phép nhập gì:

- `cau_hinh` — đọc cấu hình, báo trạng thái. KHÔNG nhập SQLAlchemy, để API vẫn
  khởi động được trên image chưa cài nhóm `db` và trên máy chưa cấu hình CSDL.
- `luoc_do` — MỘT lược đồ cho cả GĐ 5, viết bằng SQLAlchemy Core.
- `kho` — mọi truy cập CSDL đi qua đây. Giao diện và API không viết SQL.

Chạy thật trên PostgreSQL (service `copilot-db` trong compose); test chạy trên
SQLite trong bộ nhớ với CÙNG lược đồ, nên kiểm được ràng buộc mà không cần máy chủ.
"""
