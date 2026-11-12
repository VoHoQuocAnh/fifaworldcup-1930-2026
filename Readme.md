# ⚽ FiFaWorldCup-1930-2026 — Dự Đoán Kết Quả FIFA World Cup

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Pipeline-orange?logo=scikit-learn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Classifier-green)
![Flask](https://img.shields.io/badge/Flask-Web%20API%20%2B%20SQLite-000000?logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React%20%2B%20Framer%20Motion-3D%20Deck-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

Dự án áp dụng các kỹ thuật học máy (**Machine Learning Pipeline**) kết hợp thống kê bóng đá chuyên sâu (**Poisson Distribution & Expected Goals - xG**) để phân tích tập dữ liệu lịch sử các kỳ **FIFA World Cup từ năm 1930 đến 2026** (1.069 trận đấu). 

Hệ thống được thiết kế theo kiến trúc **Multi-Stage 3D Deck View** siêu tối giản (giảm 80% chữ, tập trung vào visual cues), tích hợp **8 phong cách thiết kế UI xu hướng** (Minimalist, 3D Graphics, Bold Typography, Gradient, Glassmorphism, Dark/Neo-Light Mode, Retro-Futurism cyber-grid và Neo-Brutalism).

---

## 🚀 Các Tính Năng Nổi Bật Mới Nhất

### 1. 🌟 Kiến Trúc Giao Diện 5-Stage 3D Deck View
- **Điều hướng 3D mượt mà**: Thay thế cuộn dọc truyền thống bằng không gian 3D (`perspective: 1200px`, `rotateX`, `rotateY`, `translateZ`, `blur`, `scale`).
- **Floating 3D Dock**: Thanh điều hướng nổi ở đáy màn hình + phím tắt mũi tên (`⬅️` / `➡️`) chuyển cảnh tức thì:
  - **`Stage 01: MATCH ARENA`**: Chọn 2 đội thi đấu với thẻ 3D Tilt phản xạ chuột, nút Swap và các trận cầu kinh điển. Bấm `⚡ PREDICT` sẽ tự động chuyển cảnh 3D sang Stage 02.
  - **`Stage 02: AI VERDICT & COUNCIL`**: Tỉ số xG, thanh xác suất 3 màu, Hội đồng 4 mô hình AI (Council of AI) & Lịch sử đối đầu trực tiếp (H2H).
  - **`Stage 03: RADAR & POISSON MATRIX`**: 
    - **5-Axis Tactical Radar SVG**: So sánh 5 trục chỉ số (Tấn công, Phòng ngự, Hiệu suất thắng, Bản lĩnh Knockout, Kinh nghiệm WC).
    - **5×5 Poisson Scoreline Heatmap**: Ma trận nhiệt xác suất tất cả tỉ số từ 0-0 đến 4-4+.
  - **`Stage 04: 2026 BRACKET SIMULATOR`**: Giả lập toàn bộ **88 trận đấu** World Cup 2026 (72 trận vòng bảng + 16 trận knockout từ Vòng 1/8 đến Chung kết) với chế độ AI chuẩn hoặc Monte Carlo bất ngờ.
  - **`Stage 05: GROUPS A–L & DATA VAULT`**: Poster tương tác 12 bảng đấu World Cup 2026 và Kho dữ liệu SQLite tra cứu 964 trận đấu lịch sử.

### 2. 🧠 Giải Thích Mô Hình AI (Explainable AI - XAI)
- Phân rã trực quan các yếu tố tác động (Feature Importance): Trọng số hàng công xG, độ kỵ giơ đối đầu, phong độ World Cup.
- **Kịch bản Hiệp phụ & Luân lưu 11m (Penalty Shootout)**: Tự động kích hoạt khi trận đấu bước vào vòng Knockout có xác suất hòa cao, tính toán tỷ lệ bản lĩnh sút penalty dựa trên dữ liệu lịch sử.

### 3. ⚛️ Deliverable Component React Độc Lập
- Cung cấp sẵn file [`UI/WorldCup3DDeck.jsx`](file:///d:/LearnAI_ML/Fifaworldcup_ML/UI/WorldCup3DDeck.jsx) viết bằng **React + Tailwind CSS + Framer Motion**, sẵn sàng tái sử dụng hoặc tích hợp vào các dự án web hiện đại (Next.js / Vite).

---

## 📁 Cấu trúc thư mục dự án

```text
Fifaworldcup_ML/
│
├── Data/
│   └── fifa.csv                     # Tập dữ liệu lịch sử World Cup (1930 - 2026)
│
├── Models/                          # Thư mục chứa các module thuật toán & Pipeline
│   ├── __init__.py                  # Đánh dấu package Python
│   ├── preprocessor.py              # Feature Engineering & ColumnTransformer (OneHotEncoder + Scaler)
│   ├── Linear_regression.py         # Hồi quy tuyến tính (Ridge Pipeline) dự đoán số bàn thắng
│   ├── Logistic_regression.py       # Hồi quy Logistic phân loại kết quả
│   ├── knn.py                       # K-Nearest Neighbors Pipeline
│   ├── Decision_tree.py             # Cây quyết định (Decision Tree Pipeline)
│   ├── Random_forest.py             # Rừng ngẫu nhiên (Random Forest Pipeline)
│   └── Xgboost.py                   # Thuật toán phân loại XGBoost Pipeline
│
├── UI/                              # Ứng dụng Web 3D Deck (Frontend + Backend + SQLite Database)
│   ├── app.py                       # Flask Backend REST API (Predict, Simulate Tournament, History)
│   ├── database.py                  # Quản lý SQLite, tính toán 5 chỉ số Radar & thống kê đội
│   ├── worldcup.db                  # Cơ sở dữ liệu SQLite (964 trận, metrics & lịch sử dự đoán)
│   ├── WorldCup3DDeck.jsx           # Component React + Tailwind + Framer Motion 3D Deck độc lập
│   ├── templates/
│   │   └── index.html               # Giao diện 5-Stage 3D Deck, Floating Dock & Canvas Particles
│   └── static/
│       ├── css/style.css            # 8 phong cách thiết kế UI, hiệu ứng xoay 3D GPU & Neo-Brutalism
│       ├── js/app.js                # Bộ điều khiển chuyển sân khấu 3D, Radar SVG & Poisson Heatmap
│       └── images/                  # Tài nguyên hình ảnh giao diện World Cup 2026
│           ├── wc2026_bg.jpg        # Ảnh nền bóng FIFA World Cup 2026
│           ├── wc2026_groups.png    # Poster 12 bảng đấu World Cup 2026 (A - L)
│           ├── wc_stadium_hero.png  # Ảnh Cúp Vàng & đèn pha sân vận động
│           └── trophy_center.png    # Ảnh Cúp Vàng trung tâm bảng đấu
│
├── saved_models/                    # Lưu trữ Pipeline mô hình tối ưu nhất (.pkl)
│   ├── best_model.pkl               # Pipeline(Preprocessor + Best Model) tự động chọn
│   └── model_bundle.pkl             # Gói toàn bộ 5 mô hình + mô hình dự đoán bàn thắng
│
├── Main.py                          # File thực thi huấn luyện & đánh giá chính (Main Pipeline)
├── predict.py                       # Script suy luận, tính Poisson 5x5, XAI & Penalty Shootout
├── model_comparison.png             # Biểu đồ so sánh độ chính xác giữa các model
├── Dockerfile                       # Cấu hình đóng gói ứng dụng bằng Docker (Python 3.11-slim)
├── docker-compose.yml               # Cấu hình triển khai container & ánh xạ cổng (2912:5000)
├── .dockerignore                    # Danh sách file/thư mục bỏ qua khi build Docker Image
├── requirements.txt                 # Danh sách các thư viện phụ thuộc
├── Readme.md                        # Tài liệu hướng dẫn dự án
└── .gitignore                       # Cấu hình bỏ qua file rác khi đẩy Git
```

---

## 📊 Kết quả so sánh mô hình (Results)

Dưới đây là biểu đồ so sánh độ chính xác (**Accuracy**) giữa các mô hình phân loại sau khi chuẩn hóa dữ liệu lịch sử và đóng gói `Pipeline` chống rò rỉ dữ liệu (Data Leakage):

![So sánh mô hình](model_comparison.png)

### 📌 Đánh giá
- 🥇 **XGBoost (~55.61%):** Học tuần tự kết hợp điều chuẩn (`reg_lambda`, `subsample`), xử lý xuất sắc dữ liệu đặc trưng bóng đá và được hệ thống **tự động chọn lưu** vào `saved_models/best_model.pkl`.
- 🥈 **Random Forest (~54.67%):** Điểm số bám sát XGBoost, hoạt động ổn định và chống quá khớp tốt.
- 🥉 **KNN (~51.40%) & Logistic Regression (~50.47%):** Cho kết quả khả quan khi dữ liệu được chuẩn hóa qua `StandardScaler` trong Pipeline.
- ⚠️ **Decision Tree (~49.07%):** Dễ bị Overfitting trên tập dữ liệu lịch sử nhiều biến phân loại.

> Trong bài toán phân loại 3 lớp bóng đá (Thắng / Hòa / Thua — xác suất ngẫu nhiên là `33.3%`), việc đạt độ chính xác thực tế **~55% – 56%** không rò rỉ dữ liệu cùng ước lượng phân phối bàn thắng $xG$ là kết quả rất tốt trên dữ liệu World Cup.

---

## ⚙️ Hướng dẫn cài đặt và sử dụng (How to Run)

### Cách 1: Chạy trực tiếp bằng Python

#### 1. Clone repository & Cài đặt thư viện
```bash
git clone https://github.com/VoHoQuocAnh/Fifaworldcup_ML.git
cd Fifaworldcup_ML
pip install -r requirements.txt
```

#### 2. Huấn luyện mô hình (nếu muốn train lại)
```bash
python Main.py
```

#### 3. Dự đoán cặp đấu bất kỳ trên Terminal (`predict.py`)
- **Chế độ nhập tương tác trực tiếp:**
  ```bash
  python predict.py
  ```
- **Chế độ truyền tham số nhanh qua CLI:**
  ```bash
  python predict.py --team1 "Argentina" --team2 "France" --stage "Final" --year 2026
  ```

#### 4. Khởi chạy Giao diện Web 3D Deck (`UI/`)
```bash
python UI/app.py
```
Mở trình duyệt truy cập: **http://127.0.0.1:5000**

---

### Cách 2: Chạy thông qua Docker & Docker Compose 🐳

Dự án đã được container hóa hoàn chỉnh:

```bash
docker-compose up --build -d
```
Sau đó mở trình duyệt truy cập: 👉 **http://localhost:2912**

*(Cổng `2912` trên máy của bạn được ánh xạ tới cổng `5000` bên trong container, volume liên kết trực tiếp giúp dữ liệu SQLite và code luôn đồng bộ).*

---

## 👤 Tác giả (Author)
- **Họ và tên:** Võ Hồ Quốc Anh
- **Email:** vohoquocnanh2024@gmail.com
- **GitHub:** [VoHoQuocAnh](https://github.com/VoHoQuocAnh)
