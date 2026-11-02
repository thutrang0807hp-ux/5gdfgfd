# GFlow Studio

**[Tải GFlow Studio Portable cho Windows x64 — khoảng 80 MB](https://github.com/thutrang0807hp-ux/5gdfgfd/raw/refs/heads/main/GFlow-Studio-Portable-Windows.zip)**

Giải nén toàn bộ ZIP, mở thư mục `GFlow-Studio-Portable`, nhấp đúp
**`MO-UNG-DUNG.bat`**. Không cần cài Python, pip hoặc chạy bộ cài cũ.
Máy cần Windows 10/11 x64 và Google Chrome. Đăng nhập Google Flow trong cửa sổ
Chrome của ứng dụng để tạo nội dung thật. Nếu GitHub yêu cầu đăng nhập, dùng tài
khoản có quyền truy cập repository này.

SHA-256 của gói tải ở [GFlow-Studio-Portable-Windows.sha256](GFlow-Studio-Portable-Windows.sha256).

**Đang dùng bản portable cũ?** Tải [bản cập nhật nhỏ](https://github.com/thutrang0807hp-ux/5gdfgfd/raw/refs/heads/main/GFlow-Studio-Cap-Nhat.zip),
giải nén rồi chép `CAP-NHAT.bat` vào cạnh `MO-UNG-DUNG.bat` trong thư mục đang dùng.
Mở `CAP-NHAT.bat`, đóng cửa sổ dòng lệnh GFlow cũ rồi nhấn Enter như hướng dẫn.
Tệp cập nhật tự tải mã phiên bản cố định, kiểm tra SHA-256 và chỉ thay tệp ứng dụng;
giữ nguyên tài khoản, catalog video, lịch sử và video đã tải. Cần Internet khi cập nhật.

### Video đã tạo trên Flow nhưng phần mềm báo lỗi tải về

Nếu thông báo có `signed media URL returned HTTP 302` và đề nghị
`gflow data download <mã-video>`, video đã có trên Flow nhưng chưa tải được về máy.
Bản mới hiển thị **Đã tạo trên Flow · chưa tải về** cùng nút **Tải lại video đã tạo**.
Nút chỉ gọi `gflow data download`, không gửi lại yêu cầu tạo và không dùng thêm
credit. Các lỗi cũ có mã tải lại sẽ được nhận diện khi mở lại ứng dụng.

Cũng có ô nhập mã video trong phần Lịch sử để tải lại khi không còn tác vụ cũ.
Phải dùng đúng hồ sơ tài khoản và giữ thư mục `data/profiles` của bản đã tạo video,
vì lệnh tải lại cần bản ghi video trong catalog. Một yêu cầu tải lại vẫn có thể lỗi
nếu Flow chưa cung cấp được liên kết mới; thông báo lỗi sẽ nằm trong chi tiết.

### Không để trang Flow nhảy lên màn hình

Tùy chọn **Tự thu nhỏ cửa sổ Chrome của Flow khi tạo/tải** bật mặc định trên
Windows. Ứng dụng theo dõi Chrome do tiến trình gflow của tác vụ đó mở và thu nhỏ
cửa sổ; không thao tác cửa sổ Chrome không thuộc tác vụ. Đây là thu nhỏ Chrome,
không phải chạy trình duyệt headless: cửa sổ có thể hiện thoáng qua lúc khởi động.
Đăng nhập luôn giữ cửa sổ hiện để người dùng thao tác. Lựa chọn áp dụng cho tác vụ
tiếp theo: bỏ chọn trước khi chạy nếu cần xem hoặc thao tác trong Chrome.

Đã kiểm thử nhận diện lỗi tải, di chuyển lịch sử cũ, hàng đợi tải lại không tạo mới,
truyền tùy chọn thu nhỏ và giao diện bằng Chromium. Chưa có phiên Google thật để
xác minh tải lại clip, hoặc máy Windows để kiểm chứng Win32 thu nhỏ cửa sổ.

## Bản Windows portable — mở để chạy, không cài Python

Gói `GFlow-Studio-Portable-Windows.zip` chứa sẵn Python 3.12 dành cho Windows
x64, gflow-cli và các thư viện Windows đã biên dịch. Giải nén toàn bộ rồi mở
`MO-UNG-DUNG.bat`. Không chạy bộ cài của bản cũ, không dùng Python 3.15 trên
máy và không cần Visual C++ Build Tools. Ứng dụng tự chọn cổng trống và mở trình
duyệt. Cần Google Chrome để đăng nhập Google Flow; tạo nội dung cần Internet.

Phiên đăng nhập nằm trong `data/profiles`, kết quả ở `app/out`. Đóng ứng dụng
và xóa cả thư mục portable để gỡ. Bản đóng gói đã kiểm tra wheel Windows,
kiến trúc PE x64 và tính toàn vẹn ZIP; chưa kiểm thử chạy trực tiếp trên Windows.

Lỗi `building lz4` của bộ cài cũ xảy ra khi chọn Python 3.15. Bản portable có
sẵn `_block.cp312-win_amd64.pyd`, dùng Python 3.12 riêng nên không chạy bước
biên dịch đó.

## Bản web mô phỏng, không cần cài đặt

Mở `demo/index.html` bằng Chrome. Tất cả giao diện, đồ họa và mã chạy nằm trong
một tệp HTML; không cần Python, tài khoản, API hoặc Internet. Có chọn ảnh/chuyển
động, phong cách, tỉ lệ, tiến trình, hủy và thư viện lưu trong trình duyệt.

Sau khi tạo, nhấn **Tải SVG mô phỏng** để lưu tranh hoặc hoạt cảnh SVG. Nút
**Tải bản web HTML** lưu toàn bộ ứng dụng thành tệp HTML có thể mở lại. Chuyển
động là SVG, không phải video MP4. Đây là mô phỏng bằng các mẫu đồ họa, không
gọi Google Flow hay tạo nội dung AI thật. Lịch sử lưu theo trình duyệt/địa chỉ;
đổi địa chỉ hoặc mở tệp tại đường dẫn khác có thể dùng thư viện riêng.

Nếu máy chủ Python của dự án đang chạy, bản mô phỏng ở đường dẫn `/demo`.
Để phục vụ riêng bản mô phỏng: `python -m http.server 8766 --bind 127.0.0.1 --directory demo`
từ thư mục dự án. Đây là máy chủ nội bộ, chưa phải website công khai.

## Bản tích hợp Google Flow

Giao diện web tiếng Việt cho [ffroliva/gflow-cli](https://github.com/ffroliva/gflow-cli),
tạo ảnh và video bằng tài khoản Google Flow của chính bạn. Giao diện chạy trên máy
tính, dùng lệnh thật của gflow-cli; không có ảnh/video kết quả giả lập.

## Cài trên máy tính

Cần Python 3.11+, Git, [uv](https://docs.astral.sh/uv/getting-started/installation/)
và Google Chrome. Đặt hai repository cạnh nhau:

```text
thu-muc/
  5gdfgfd/
  gflow-cli/
```

Mở terminal trong `thu-muc` rồi chạy:

```sh
git clone https://github.com/ffroliva/gflow-cli.git
cd gflow-cli
git checkout 1619429f12e31a806590a19e1a3f3218f291d582
uv sync --frozen
uv run --frozen playwright install chromium
```

Sau đó mở `5gdfgfd/start.bat` trên Windows hoặc chạy `sh start.sh` trong thư mục
`5gdfgfd` trên macOS/Linux. Trình duyệt tự mở giao diện. Nếu không tự mở, nhập
`http://127.0.0.1:8765` vào trình duyệt **trên chính máy chạy ứng dụng**.
Giữ terminal mở; nhấn Ctrl+C để dừng. Có thể chọn cổng khác bằng `sh start.sh --port 8766`.

Lệnh tương đương trong môi trường đám mây hiện tại:

```sh
cd /workspace/5gdfgfd
/workspace/gflow-cli/.venv/bin/python app.py --port 8765
```

## Sử dụng

1. Giữ tên hồ sơ `default`, nhấn **Đăng nhập Google** và đăng nhập trong cửa sổ
   Chrome mở trên máy chạy ứng dụng. Ứng dụng không nhận mật khẩu Google.
2. Nhấn **Kiểm tra phiên** và chờ kết quả trong lịch sử. Trạng thái “đã lưu phiên”
   chỉ xác nhận dữ liệu có trên đĩa; kiểm tra phiên xác minh với Google.
3. Chọn tạo ảnh hoặc video, nhập mô tả và chọn tỉ lệ. Với ảnh, có thể chọn model.
   Video dùng model mặc định hiện tại của Flow và cần xác nhận sử dụng credit.
4. Nhấn tạo. Ứng dụng thực thi lần lượt từng tác vụ để tránh xung đột Chrome.
   Kết quả thành công có hình/video xem trực tiếp và nút tải về.
5. Khi lỗi, mở **Chi tiết tác vụ**. Không tự động thử lại. Sau timeout hoặc gián
   đoạn, kiểm tra dự án trên Flow trước khi gửi lại để tránh tạo trùng hoặc tốn credit.

Tác vụ và lịch sử được lưu trong `.data/`, sản phẩm tải về trong `out/`.
Phiên Google được gflow-cli lưu trong thư mục dữ liệu người dùng của nó.
Không chia sẻ thư mục phiên đăng nhập. Có thể dùng tên hồ sơ khác để đăng nhập
tài khoản khác; dùng cùng tên khi đăng nhập, kiểm tra và tạo nội dung.

## Giới hạn hiện tại

- Đã xây giao diện, tích hợp CLI, hàng đợi, lưu lịch sử và tải kết quả.
- Tạo ảnh/video thật cần tài khoản có quyền Google Flow, phiên Chrome hợp lệ và
  màn hình để đăng nhập. Không cung cấp sẵn tài khoản hoặc credit.
- Trên máy chủ không có màn hình, nút đăng nhập được vô hiệu hóa. Chạy trên máy
  tính có Chrome là quy trình chính cho người dùng.
- Chỉ phục vụ tại loopback để dùng cá nhân. Chưa có đăng nhập nhiều người dùng
  hoặc triển khai dịch vụ công khai.
- gflow-cli là dự án độc lập, chưa ổn định; thay đổi từ Google có thể ảnh hưởng
  việc tạo nội dung. Giấy phép upstream MIT tại `../gflow-cli/LICENSE`.

## Kiểm thử

```sh
cd /workspace/5gdfgfd
/workspace/gflow-cli/.venv/bin/python -m pytest tests -q
```

Kiểm thử xác minh API, hàng đợi, phục hồi lịch sử, xác nhận video, giới hạn đường
dẫn, chặn yêu cầu từ website khác và lỗi thiếu đăng nhập từ CLI thật. Các kiểm thử
này không xác minh ảnh/video tạo thành công từ Google.
