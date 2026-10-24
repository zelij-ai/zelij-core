# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · **Tiếng Việt** · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Xây dựng startup 100 % AI-native của bạn.** Một văn phòng nơi bốn tác nhân làm việc cho bạn: họ đề xuất, bạn quyết định. Máy của bạn, khóa Claude của bạn, dữ liệu của bạn; không có gì gửi đi đâu cả.

![Bể cá Zelij Core: nhà sáng lập và bốn tác nhân trao đổi, đề xuất quyết định và thực hiện những gì đã được duyệt](docs/img/aquarium.gif)

*Bể cá trong một ngày mô phỏng (ở đây hiển thị bằng tiếng Pháp). Trong bản cài đặt của bạn, mỗi thẻ là một hành động thật của các tác nhân, trực tiếp và có thể phát lại trong hai mươi bốn giờ. Màu vàng là bạn: không điều gì ràng buộc xảy ra trước quyết định của bạn. Các gương mặt là nhân vật hư cấu.*

## Lõi làm được gì

- **Văn phòng**: một trang. Các quyết định đang chờ, một yêu cầu gửi chánh văn phòng, những lần chạy gần nhất kèm chi phí, nhật ký, các tác nhân, các mô-đun đã cài.
- **Gói quyết định**: mục tiêu, đề xuất, vì sao lúc này, các lựa chọn, khuyến nghị, rủi ro, khả năng đảo ngược, kế hoạch, cách quay lui, tác động. Gói không đầy đủ thì không mở được. Duyệt, từ chối, hoặc yêu cầu thay đổi kèm một chỉ dẫn bắt buộc được chuyển cho tác nhân.
- **Quy tắc trong nhà**: không điều gì ràng buộc (tiền, công khai, xóa, không thể đảo ngược) được làm khi chưa có quyết định; một sự kiện phải có ngày và nguồn hoặc được đánh dấu « chưa kiểm chứng »; nhật ký không bao giờ bị xóa.
- **Cổng kết nối**: khóa Claude của nhà sáng lập, chi phí mỗi lần gọi tính từ mức dùng và bảng giá công khai có ngày, trần hằng tháng sẽ chặn khi chạm tới.
- **Bộ thực thi**: vòng lặp gọi có giới hạn (ngân sách lượt cho mỗi tác nhân), công cụ tiết chế, mô hình từ chối được xem như một kết quả.
- **Mô-đun**: cách duy nhất để mở rộng lõi. Giao diện ổn định, tệp kê khai `pack.json` do nhà phát hành ký bằng Ed25519, băm của từng tệp nằm trong chữ ký, kiểm tra trước khi cài. Các đích triển khai và tác nhân bổ sung đều đi qua đây.
- **Tài chính**: doanh thu đã xác nhận (nhập Stripe chỉ đọc hoặc nhập tay kèm chứng từ), chi phí đã khai lặp lại hằng tháng, chi phí tác nhân được đo, sổ tháng, xuất CSV cho kế toán. Không khai báo, không lập hóa đơn.
- **Liên hệ**: một thẻ cho mỗi người, cơ sở pháp lý bắt buộc, thời hạn lưu giữ, trao đổi, quyền đã thực hiện; một liên hệ phản đối sẽ không nhận gì nữa, một liên hệ hết hạn bị quên và chỉ còn nhật ký về quyền.
- **Xuất bản**: một trang do tác nhân marketing viết trở thành bản nháp, rồi thành một quyết định; được duyệt, nó được đề xuất cho website dưới dạng pull request GitHub hoặc bản nháp WordPress. Bước cuối, gộp hay đăng, là của bạn.
- **Trong túi**: mỗi quyết định đến điện thoại của bạn, qua e-mail với hai liên kết ký dùng một lần, hoặc qua Telegram với ba nút. Bạn duyệt khi xếp hàng ở ga tàu; bể cá chuyển động ngay khi bạn trả lời. Cùng một cửa, cùng một nhật ký như từ bàn làm việc.
- **Bể cá**: xem các tác nhân làm việc, mỗi bong bóng là một hành động thật trong 24 giờ qua; những vòng chấm là vị trí còn trống. Một trang công khai có thể chia sẻ, với huy hiệu « by zelij.ai ».
- **Danh mục**: những gì bản miễn phí không có, được nêu tên trung thực; một mô-đun mua từ nhà phát hành được cài tại đây, có ký và kiểm tra. Không khoản thanh toán nào đi qua văn phòng.
- **Xưởng phần mềm**: Người xây dựng đọc và đề xuất trên duy nhất một kho mã, qua các pull request đi qua cổng an ninh (300 dòng, chỉ văn bản, không bí mật, không tệp hạ tầng, phụ thuộc không có lỗ hổng đã biết theo OSV); đưa lên máy chủ Linux qua SSH hoặc lên OVH (tên miền và DNS qua API) với chuyển đổi nguyên tử, kiểm thử khói và quay lui; thăm dò tên miền; sao lưu văn phòng hằng ngày. Nó không bao giờ gộp, không bao giờ trả tiền, không bao giờ đụng vào văn phòng.
- **Các tác nhân**: một thư mục cho mỗi tác nhân, một `agent.md` với phần đầu đơn giản và chỉ dẫn bằng tiếng Pháp. Bốn tác nhân: Camille Aubert (chánh văn phòng), Élise Tanguy (tăng trưởng, marketing và sản phẩm), Nour Bellamy (tài chính và khách hàng), Sacha Ferrand (người xây dựng, xưởng phần mềm). Nhà sáng lập nói chuyện với từng người từ văn phòng; một gói đã duyệt chỉ định tác nhân và nhiệm vụ sẽ chạy ngay, trong giới hạn của kế hoạch.

## Thử trong một phút, không cần khóa

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Mở `http://localhost:8000` và vào bản trình diễn: một công ty hư cấu, bốn tác nhân mô phỏng, các quyết định cần duyệt, bể cá phát lại ngày làm việc của họ. Không khóa, không tài khoản, không chi phí; không gì được gửi tới mô hình và mọi thứ biến mất khi dừng. Khi đã tin, hãy chuyển sang cài đặt thật bên dưới. Bản thân văn phòng dùng tiếng Pháp.

## Khởi động

```bash
cp .env.example .env     # khóa Claude, trần chi phí, SECRET_KEY, mật khẩu cơ sở dữ liệu
docker compose up -d --build
```

Văn phòng trả lời tại `http://localhost:8000`. Không có SMTP, liên kết đăng nhập được ghi vào nhật ký container (`docker compose logs core-app`).

Hướng dẫn đầy đủ (tiếng Anh): **[Cài đặt](docs/INSTALLATION.en.md)** (từ máy trống đến văn phòng chạy https, SMTP, xưởng phần mềm, sao lưu, khắc phục sự cố), **[Hướng dẫn sử dụng](docs/MODE-D-EMPLOI.en.md)** (từng trang, các tác nhân, quyết định, chi phí). Ảnh của nhà sáng lập và các tác nhân đặt trong [`portraits/`](portraits/README.md) (mô tả bằng tiếng Pháp).

Từ ảnh đã phát hành, không cần dựng cục bộ (`CORE_IMAGE_TAG=v…` trong `.env` để cố định phiên bản):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Chạy cục bộ không cần Docker:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Khóa công khai của nhà phát hành

Các mô-đun trong danh mục được zelij.ai ký. Khóa công khai cần đặt vào `ZELIJ_CLE_PUBLIQUE` (đã có sẵn trong `.env.example`):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Bảo mật

Những gì lõi bảo đảm và được kiểm thử (`tests/test_securite.py`):

- **Mô-đun**: một mô-đun chỉ được cài và chạy khi có chữ ký của nhà phát hành (Ed25519), và chữ ký bao phủ băm SHA-256 của từng tệp mã: một tệp bị sửa, thêm hay xóa sau khi ký sẽ loại mô-đun ra khỏi cuộc chơi.
- **Đăng nhập**: liên kết dùng một lần có hiệu lực 20 phút, được băm trong cơ sở dữ liệu; phanh theo địa chỉ, theo IP và toàn cục trên các yêu cầu liên kết, để văn phòng không bao giờ thành trạm chuyển tiếp e-mail; không cấu hình SMTP trong môi trường thật thì không liên kết nào được tạo hay ghi lại.
- **Biểu mẫu**: cookie phiên HMAC `HttpOnly` `SameSite=Strict`, kiểm tra nguồn gốc và mã chống CSRF theo phiên trên mỗi POST.
- **Trang**: chính sách bảo mật nội dung nghiêm ngặt (`default-src 'self'`, không script nội tuyến, không khung), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS khi nguồn là https.
- **Tác nhân**: những gì một tác nhân đọc (trang web, tệp trong kho) đến với nó như nội dung bên ngoài được đóng khung, không bao giờ như chỉ dẫn; tác nhân chỉ chạy các công cụ ghi trên thẻ của mình và, ngay khi đã đọc dữ liệu riêng tư, chỉ còn được gọi website của công ty; nó chỉ đọc các địa chỉ https công khai (địa chỉ riêng, loopback, link-local và tên nội bộ bị từ chối ở mỗi bước chuyển hướng, phản hồi có giới hạn); cổng an ninh chặn bí mật, tệp hạ tầng, script bên thứ ba, khung và các lời gọi mạng.
- **Container**: người dùng không đặc quyền, hệ thống tệp chỉ đọc, không capability, không nâng quyền; khóa máy chủ SSH có thể được ghim (`SSH_CLE_HOTE`).
- **Xuất kế toán**: các ô trông giống công thức bảng tính được vô hiệu hóa.

Báo lỗ hổng tới `securite@zelij.ai`, không công bố trước khi sửa. Trước mỗi phiên bản, `pip-audit -r requirements.txt` và `bandit -r core scripts -ll` phải trả về rỗng.

## Đóng góp và theo dõi phiên bản

`CONTRIBUTING.md` (tiếng Pháp) nói cách một đóng góp đi vào một phiên bản, gồm cả quy tắc: đóng góp một đích triển khai thì được gói tương ứng miễn phí trọn đời. `SECURITY.md` nói cách báo lỗ hổng. `CHANGELOG.md` nói mỗi phiên bản thay đổi gì và nhà sáng lập còn phải làm gì.

## Kiểm thử và kiểm soát xuất bản

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Kiểm soát xuất bản từ chối khóa, địa chỉ IP, mã nội bộ, địa chỉ e-mail cá nhân, mật khẩu dạng rõ, và các thuật ngữ trong một danh sách riêng (`ZELIJ_CORE_INTERDITS`) không bao giờ nằm trong kho mã.

## Giấy phép

GNU AGPL v3. Bản quyền (C) 2026 zelij.ai. Bạn có thể dùng, sửa và phân phối lại lõi, với điều kiện công bố các sửa đổi của mình dưới cùng giấy phép. Bản đầy đủ vận hành zelij.ai vẫn thuộc về nhà phát hành.

by zelij.ai — https://zelij.ai/
