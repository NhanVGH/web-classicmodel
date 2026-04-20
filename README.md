# ClassicModels Analytics Website

Website phân tích cơ sở dữ liệu `classicmodels` với các chức năng:

- Tìm kiếm khách hàng và mặt hàng qua RESTful API
- Thống kê doanh số theo thời gian, khách hàng, dòng sản phẩm
- Báo cáo chi tiết giao dịch
- Pivot report động theo hàng, cột và chỉ tiêu
- Biểu đồ doanh số dựng từ dữ liệu API
- Truy xuất dữ liệu bằng `SQLAlchemy ORM`

## Công nghệ

- Backend: `FastAPI`
- ORM: `SQLAlchemy`
- Frontend: `HTML + CSS + JavaScript`
- Database: `MySQL classicmodels` qua `PyMySQL`

## Cấu trúc chính

```text
app/
  main.py               # khởi tạo FastAPI
  database.py           # engine + session
  models.py             # ORM model classicmodels
  routers/api.py        # RESTful API
  services/reporting.py # truy vấn tìm kiếm, thống kê, pivot, báo cáo
  templates/index.html  # giao diện dashboard
  static/css/styles.css
  static/js/app.js
```

## Cấu hình

1. Tạo file `.env` từ `.env.example`.
2. Cập nhật chuỗi kết nối:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost/classicmodels
```

Nếu bạn dùng user, password hoặc host khác thì thay lại cho phù hợp.

## Cài thư viện

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Chạy ứng dụng

Khuyến nghị dùng lệnh gọi trực tiếp Python trong virtual environment:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Hoặc nếu đã activate `.venv`, bạn có thể dùng:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Mở trình duyệt tại:

```text
http://127.0.0.1:8000
```

Nếu cổng `8000` đã được dùng, hãy dừng tiến trình cũ rồi chạy lại.

## REST API chính

- `GET /api/health`
- `GET /api/metadata`
- `GET /api/customers?q=atelier`
- `GET /api/products?q=ferrari`
- `GET /api/dashboard/summary`
- `GET /api/dashboard/charts`
- `GET /api/dashboard/details`
- `GET /api/dashboard/pivot`

## Gợi ý demo

- Lọc theo `date_from`, `date_to` để xem doanh số theo giai đoạn
- Lọc `customer_keyword` để xem top khách hàng
- Lọc `product_keyword` hoặc `product_line` để phân tích mặt hàng
- Đổi `pivot rows / columns / metric` để dựng báo cáo chéo
