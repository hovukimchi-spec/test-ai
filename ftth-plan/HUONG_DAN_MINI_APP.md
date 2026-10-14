# Đóng gói thành mini app (PWA) cho iPhone

Thư mục `pwa/` (hoặc `ftth-pwa.zip`) là một ứng dụng web cài được: có biểu tượng riêng, mở toàn màn hình, chạy offline sau lần mở đầu.
iPhone chỉ cài được khi tệp nằm trên một địa chỉ **https**, nên cần đưa thư mục lên một chỗ lưu trữ web miễn phí (1 lần):

## Cách nhanh nhất: Netlify Drop (không cần tài khoản code)
1. Trên máy tính, giải nén `ftth-pwa.zip` ra một thư mục.
2. Mở https://app.netlify.com/drop, kéo thả thư mục vào. Netlify trả về một địa chỉ dạng `https://tên-ngẫu-nhiên.netlify.app`.
3. Trên iPhone mở địa chỉ đó bằng **Safari** → nút Chia sẻ → **Thêm vào Màn hình chính**. Xong: biểu tượng "FTTH Phố Đông" trên màn hình.

## Cách khác
- **Cloudflare Pages**: tạo project, upload thư mục `pwa/` (Direct Upload).
- **GitHub Pages**: đưa nội dung `pwa/` vào thư mục `docs/` của repo, Settings → Pages. Repo private cần gói trả phí.

## Lưu ý
- Ai có địa chỉ đều mở được sơ đồ (có mã căn hộ, tủ, sợi). Giữ địa chỉ nội bộ; cần bảo mật hơn thì đặt mật khẩu ở dịch vụ lưu trữ (Netlify/Cloudflare có tùy chọn).
- Cập nhật nội dung: chạy `python3 build_html.py && python3 build_pwa.py` rồi tải lại thư mục `pwa/` lên cùng địa chỉ. App tự cập nhật ở lần mở sau.
- Trạng thái căn hộ lưu trong bộ nhớ của app trên từng máy; chuyển qua lại bằng nút "CSV trạng thái".
- Đóng gói thành app trên App Store cần máy Mac, Xcode và tài khoản Apple Developer (99 USD/năm); PWA là cách đủ dùng cho việc này.
