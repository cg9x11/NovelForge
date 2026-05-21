<div align="center">

# NovelForge

<p><strong>Công cụ sáng tạo tiểu thuyết AI thế hệ mới</strong></p>

<p>
  <a href="#catalogue">Mục lục</a> •
  <a href="#corefeature">Tính năng cốt lõi</a> •
  <a href="#Updatelog">Nhật ký cập nhật</a> •
  <a href="#Run Guide">Hướng dẫn chạy</a> •
  <a href="#creative process">quy trình sáng tạo</a>
</p>

<p>
  <a href="#Cấu hình và tính năng nâng cao">Tính năng nâng cao</a> •
  <a href="#workflow hệ thống quy trình làm việc được mã hóa--workflow-agent">hệ thống quy trình làm việc</a> •
  <a href="#project Structure">Cấu trúc dự án</a> •
  <a href="./Contribution Guide.md">Hướng dẫn đóng góp</a> •
  <a href="./Follow-up Planning.md">Lập kế hoạch tiếp theo</a> •
  <a href="#Nhóm giao tiếp">Nhóm giao tiếp</a>
</p>


</div>

**NovelForge** là một công cụ viết được hỗ trợ bởi AI với tiềm năng tạo ra những cuốn tiểu thuyết nhiều triệu từ. Nó không chỉ là một trình soạn thảo mà còn là một giải pháp tích hợp xây dựng thế giới quan và tạo nội dung có cấu trúc.

Trong quá trình sáng tạo dạng dài, việc duy trì tính nhất quán, đảm bảo khả năng kiểm soát và kích thích nguồn cảm hứng liên tục là những thách thức lớn nhất. Để đạt được mục tiêu này, NovelForge được xây dựng dựa trên bốn khái niệm cốt lõi: **thẻ** mô-đun, **mô hình đầu ra động** có thể tùy chỉnh, **chèn ngữ cảnh** linh hoạt và **biểu đồ kiến ​​thức** đảm bảo tính nhất quán.

---

<a id="thư mục"></a>
## 📑 Mục lục

### Điều hướng nhanh

- [✨Tính năng cốt lõi](#corefeatures)
- [📅Nhật ký cập nhật](#UpdateLog)
- [🛠️Ngăn xếp công nghệ](#Ngăn xếp công nghệ)
- [🚀Hướng dẫn chạy](#Hướng dẫn chạy)
- [✍️Quy trình sáng tạo](#CreativeProcess)
- [⚙️ Chức năng và cấu hình nâng cao](#Chức năng và cấu hình nâng cao)
- [📂Cấu trúc dự án](#projectstructure)
- [🔭 Outlook](# Outlook)

### Nhảy theo chức năng

- [Lược đồ-đầu tiên: loại/cấu trúc thể hiện và tham số](#schema-first)
- [Prompt Workshop](#prompt-workshop)
- [Giải thích chi tiết về chèn ngữ cảnh (@DSL)](#context-dsl)
- [Hệ thống quy trình làm việc (quy trình làm việc được mã hóa + Tác nhân quy trình làm việc)](#workflow-system)
  - [Workflow Studio](#workflow-studio)
  - [Cấu hình kích hoạt](#workflow-triggers)
  - [Thanh trạng thái quy trình làm việc (chạy nền chung)](#workflow-status-bar)
  - [Tiến trình cấp nút và khôi phục gián đoạn (Beta)](#workflow-progress-recovery)
  - [Quy trình làm việc liên tục và Quy trình làm việc tạm thời](#workflow-persistent-vs-temporary)
  - [Mẫu quy trình công việc tích hợp sẵn](#workflow-buildins)
  - [Quy trình khởi tạo dự án](#workflow-project-init)
  - [Workflow Agent (quy trình viết ngôn ngữ tự nhiên)](#workflow-agent)
  - [Ví dụ về cách sử dụng quy trình làm việc (quy trình mở sách)](#workflow-examples)

### Hợp tác và lập kế hoạch

- [Hướng dẫn đóng góp](./Contribution Guide.md)
- [Lập kế hoạch tiếp theo](./Follow-up Planning.md)

---

<a id="Tính năng cốt lõi"></a>
## ✨ Tính năng cốt lõi

* **📚 Tạo thẻ dựa trên lược đồ**
    * Mỗi thẻ có thể xác định một cấu trúc (Schema) và việc tạo AI sẽ được xác minh theo cấu trúc đó, làm giảm kết quả đầu ra "trông có thể sử dụng được nhưng lại gây nhầm lẫn khi triển khai".

* **⚡ Truyền lệnh tạo thẻ AI**
    * Không còn "tạo toàn bộ phần cùng một lúc". Bây giờ là "yêu cầu đầu vào → điền vào luồng chi tiết của trường → xác nhận hoặc phản hồi của bạn tiếp tục được tạo", điều này dễ kiểm soát hơn và dễ sửa hơn. Quá trình tạo diễn ra suôn sẻ hơn và tránh phải chờ đợi kết quả tạo lâu.
    * Khả năng này tập trung vào việc tạo và cải thiện "thẻ hiện tại". Phiên này sẽ kết thúc sau khi đóng hộp thoại tạo.

* **📝 Kiểm soát số văn bản chương **
    * Tiếp tục văn bản chương hỗ trợ hai chế độ: `ràng buộc từ nhắc` và `chế độ điều khiển`.
    * `Ràng buộc từ nhắc nhở` tự nhiên hơn và chi phí thấp hơn; `Chế độ kiểm soát` sẽ chia ngân sách thành nhiều vòng theo tổng số từ mục tiêu, giúp việc kiểm soát ổn định hơn nhưng sẽ tiêu tốn nhiều token hơn.

* ****** Thẻ kết quả đánh giá và đánh giá chung**
    * Quá trình đánh giá áp dụng thống nhất quy trình "Xem trước bản nháp → Xác nhận và lưu dưới dạng thẻ kết quả đánh giá".
    * Các loại thẻ khác nhau có thể chuyển sang các từ nhắc đánh giá khác nhau, nhưng cấu trúc thẻ kết quả vẫn nhất quán để dễ dàng xem và tham khảo thống nhất.

* **🧠 Chèn ngữ cảnh + Tính nhất quán của Sơ đồ tri thức**
    * Tham chiếu chính xác dữ liệu dự án thông qua `@DSL`; kết hợp bản đồ mối quan hệ và thông tin động để làm cho thế hệ tiếp theo gần gũi hơn với nội dung văn bản và mối quan hệ vai trò.

* **🔮Trợ lý truyền cảm hứng (Đại lý)**
    * Đối thoại liên tục, thẻ tham khảo và công cụ gọi để sửa đổi nội dung. Bạn có thể tinh chỉnh cài đặt như thể bạn đang làm việc với đối tác, thay vì phải tạo lại toàn bộ thẻ nhiều lần.

* **🧩 Hệ thống quy trình làm việc dựa trên mã**
    * Đã được cơ cấu lại thành dòng chính của quy trình làm việc dựa trên mã (loại bỏ giải pháp DAG cũ), hỗ trợ chỉnh sửa trực quan, kích hoạt thực thi và tái sử dụng, đồng thời phù hợp để tự động hóa các quy trình sáng tạo phổ biến.

* **🤖 Tác nhân quy trình làm việc**
    * Bạn có thể mô tả trực tiếp các yêu cầu của mình bằng ngôn ngữ tự nhiên và để Tác nhân giúp bạn viết/sửa đổi mã quy trình công việc, xác minh và áp dụng các thay đổi.

* **💡 Bàn làm việc ý tưởng**
    * Hỗ trợ thẻ miễn phí, tài liệu tham khảo giữa các dự án và di chuyển/sao chép trở lại các dự án chính thức, phù hợp cho việc động não và kết tủa tài liệu.

---

<a id="Nhật ký cập nhật"></a>

## 📅 Nhật ký cập nhật
<chi tiết>
<tóm tắt>v0.9.5</tóm tắt>

- Sửa lỗi quy trình làm việc
- Thay đổi quy trình mở sách sang chế độ luồng lệnh mặc định để nâng cao tỷ lệ thành công
- Đã sửa một số vấn đề hiển thị UI ở các độ phân giải khác nhau
</ chi tiết>

<details>
<summary>v0.9.4</summary>

- **Nâng cao thông tin lớp bộ nhớ (vai trò/mối quan hệ/cảnh/tổ chức/mục/khái niệm)**
  - Xem trước trích xuất thống nhất/xác nhận quá trình viết
    Trong trình chỉnh sửa chương, các khả năng sau đã được hợp nhất thành quy trình "xem trước trước, sau đó xác nhận":

- Thông tin động nhân vật
    - Trích xuất các mối quan hệ thành đồ thị
    - Trạng thái cảnh
    - Tình trạng tổ chức
    - Tình trạng mặt hàng
    - Làm chủ khái niệm
  - Phương thức tương tác thống nhất là:
    - Bắt đầu trích xuất dựa trên văn bản chương hiện tại
    - Hiển thị kết quả xem trước trước
    -Hỗ trợ người dùng điều chỉnh thủ công trong bản xem trước
    - Xác nhận rồi ghi lại vào thẻ hoặc bản đồ
  - Lần này, khả năng trạng thái/bộ nhớ nhẹ của các loại thực thể sau đã được thêm và hoàn thiện (được sử dụng theo yêu cầu, không phải sử dụng tất cả để tránh làm tăng độ phức tạp của ngữ cảnh):
    - thẻ cảnh
    -Thẻ tổ chức
    - Thẻ vật phẩm
    - thẻ khái niệm
- Tối ưu hóa bố cục CSS trên thiết bị đầu cuối di động và thêm chức năng điều hướng ở góc dưới bên trái để hiển thị và ẩn.

- Các tối ưu hóa và sửa lỗi khác

</details>

<details>
<summary>v0.9.3</summary>

- **Tái cấu trúc điều khiển số văn bản chương**
  - Điều khiển đếm từ để tiếp tục văn bản chương hội tụ về hai chế độ:
    - `Ràng buộc từ nhắc`: chỉ giới hạn số từ ở cấp độ từ nhắc, giúp văn bản trở nên tự nhiên hơn và phù hợp với những tình huống yêu cầu số từ không đặc biệt khắt khe.
    - `Chế độ điều khiển`: Chia thành nhiều vòng và phân bổ ngân sách theo tổng số từ mục tiêu. Việc kiểm soát số từ ổn định hơn nhưng sẽ tiêu tốn nhiều mã thông báo hơn.
  - Chế độ kiểm soát hiện sử dụng chiến lược ngân sách nhiều vòng cố định để cải thiện tính ổn định và khả năng kiểm soát của các phần tiếp theo của chương dài.

- **Tái cấu trúc chức năng kiểm toán**
  - Quy trình xem xét được thống nhất là "đầu tiên tạo bản nháp đánh giá, sau đó xác nhận để tạo/cập nhật thẻ kết quả đánh giá"
  - Kết quả kiểm tra không còn dựa vào mô hình hồ sơ cũ mà được thống nhất thành `thẻ kiểm tra nội dung`
  - Thẻ kết quả kiểm toán sẽ được tự động lưu trữ vào thư mục `Kết quả kiểm toán` cấp cơ sở để xem và sử dụng lại tập trung.
  - Các lối vào ôn tập văn bản chương và trình soạn thảo thẻ chung được hợp nhất thành "nút ôn tập + chuyển từ nhắc nhở"

- **Các tối ưu hóa khác**
  - Cấu hình LLM được tối ưu hóa, khả năng tương thích chế độ Phản hồi (Trợ lý truyền cảm hứng vẫn chưa tương thích), sắp xếp xuất, trình chỉnh sửa chương và một số chi tiết giao diện người dùng
  - Đã sửa một số lỗi và cải thiện độ ổn định tổng thể

</details>

<details>
<summary>v0.9.2</summary>

- Đã thêm đánh giá chương, đánh giá giai đoạn và xem lịch sử đánh giá
  - Chỉ cần nhấp vào nút xem lại ở đầu thẻ văn bản của giai đoạn/chương. Sau khi xem xét hoàn tất, kết quả đánh giá sẽ bật lên.
  - Bạn có thể xem lịch sử kiểm tra ở cột bên phải
- Đã thêm tìm kiếm thẻ, thẻ loại thư mục và bắt đầu giao diện người dùng và mặt sau bằng một cú nhấp chuột, đồng thời khắc phục sự cố lưu và gấp cấu trúc cây
- Tự động kiểm tra sự khác biệt giữa siêu dữ liệu mô hình và cấu trúc bảng hiện có của cơ sở dữ liệu để phát hiện và hoàn thiện các cột còn thiếu để có thể “nối thêm một cách an toàn”
- Các tối ưu hóa khác

</details>

<details>
<summary>v0.9.1</summary>

- **Sơ đồ quan hệ hỗ trợ lưu trữ SQLite**
  - Hỗ trợ SQLite mới để lưu trữ biểu đồ mối quan hệ (và tương thích với Neo4j)
  - Đã thêm khả năng quản lý sơ đồ mối quan hệ: lọc, sửa đổi hàng loạt, nhập và xuất, v.v.

- **Tối ưu hóa các từ gợi ý liên quan đến việc tạo và đánh bóng văn bản chương**
  - Tối ưu hóa hiệu suất của các từ nhắc nhở như "tạo/đánh bóng/mở rộng nội dung" để cải thiện độ ổn định đầu ra và khả năng sử dụng
  - Tách nội dung liên quan đến các ràng buộc về kiểu dáng thành các phần cơ sở kiến thức để tạo điều kiện bảo trì độc lập và điều chỉnh nhanh chóng

- **Thêm chức năng đánh bóng/từ chối văn bản chương đã được sửa đổi**
  - Dịch vụ thay thế Ba Lan hỗ trợ các hoạt động "chấp nhận và thay thế/từ chối và khôi phục" để giảm nguy cơ thay thế nhầm
- Đã thêm chức năng sao chép cấu hình LLM: có thể sao chép và tinh chỉnh nhanh chóng dựa trên cấu hình hiện có, giảm chi phí cấu hình lặp lại
- Đã sửa một số lỗi và cải thiện độ ổn định tổng thể và trải nghiệm tương tác

</details>

<details>
<summary>v0.9.0</summary>

- 🚀 **Cập nhật đột phá: 0.9.0**

- ✨ **Xây dựng lại quy trình tạo thẻ AI**
  - Đã nâng cấp từ "Nhấp và chờ toàn bộ kết quả" thành "Yêu cầu đầu vào → Tạo độ chi tiết trường trong hộp thoại → Tiếp tục tạo xác nhận/phản hồi", giúp tăng cường đáng kể khả năng sử dụng và làm cho nó mượt mà hơn~
  - Quá trình phát điện dễ kiểm soát hơn và chi phí sửa đổi thấp hơn.

- 🧱 **Tái thiết hệ thống quy trình làm việc (khám phá)**
  - Chúng tôi đã di chuyển một cách thăm dò quy trình làm việc từ **trình soạn thảo kiểu DAG** cũ sang **quy trình làm việc dựa trên mã mới (câu lệnh kiểu Python + DSL thẻ đặc biệt)** và dần dần loại bỏ sơ đồ DAG cũ.
  - Hiện tại nó dựa nhiều hơn vào sự cân bằng toàn diện giữa khả năng bảo trì và tính thân thiện với AI.
  - **Ưu điểm của quy trình làm việc dựa trên mã (trải nghiệm hiện tại):**
    - Logic tuyến tính và rõ ràng hơn: các ngữ nghĩa như trình tự, chờ đợi (`Logic.Wait`), không đồng bộ (`async=true`) gần với quy trình thực thi thực tế hơn.
    - Quá trình xử lý tiến trình và các hoạt động không đồng bộ diễn ra tự nhiên hơn: người thực thi có thể được lên lịch theo kế hoạch câu lệnh mà không cần phải đi vòng quanh biểu đồ.
    - Thân thiện hơn với AI: cùng một chức năng thường có thể được thể hiện bằng hàng chục dòng mã; trong khi cấu hình DAG thường yêu cầu hàng trăm dòng mô tả nút và kết nối.
  - **Nhược điểm của quy trình làm việc dựa trên mã (cần trau chuốt liên tục):**
    - Không trực quan như DAG
    - Nhạy cảm hơn với định dạng chuỗi/mã: Các chi tiết như tuần tự hóa tham số, loại trường từ điển, tham chiếu biến, v.v. có nhiều khả năng gây ra lỗi xác minh hoặc lỗi chạy hơn, yêu cầu xác minh mạnh mẽ hơn và ràng buộc từ nhanh chóng.

- 🤖 **Đại lý quy trình làm việc mới**
  - Mục tiêu có thể được mô tả thông qua ngôn ngữ tự nhiên và mã quy trình làm việc có thể được Tác nhân tạo/sửa đổi và xác minh.
  - Hỗ trợ trải nghiệm thay đổi bảo mật "xem trước rồi áp dụng".
  - Có thể có một số lỗi

- 📚 **Cải tiến quy trình làm việc tích hợp**
  - Đã thêm các mẫu quy trình thực tế như "Quy trình giải nén sách" để tạo điều kiện thuận lợi cho việc giải nén và chuyển đổi thứ cấp.

- 🎨 **Tối ưu hóa giao diện người dùng và tương tác của Trợ lý truyền cảm hứng**
  - Kết xuất hội thoại, tương tác khu vực đầu vào, hiển thị lệnh gọi công cụ và tối ưu hóa trải nghiệm khác.

- 🧹 **Tái thiết dự án và cải thiện độ ổn định**
  - Cấu trúc thư mục front-end và back-end cũng như ranh giới mô-đun đã được thay đổi và tổ chức đáng kể, đồng thời cải thiện khả năng bảo trì mã.
  - Đã khắc phục một loạt vấn đề liên quan đến quy trình làm việc, chỉnh sửa tham số trực quan và tương tác với Tác nhân.

- ⚠️ Do phiên bản này có nhiều thay đổi lớn nên phiên bản cũ của cơ sở dữ liệu có thể không được sử dụng trực tiếp. Vui lòng thử di chuyển bằng cách sử dụng tập lệnh di chuyển đã xuất bản (không đảm bảo thành công, bạn nên sao lưu trước tệp db cơ sở dữ liệu!)

</details>

<details>
<summary>v0.8.6</summary>

- Thêm chức năng phát hiện cập nhật phiên bản, mặc định được tự động phát hiện (khi có phiên bản mới, một chấm đỏ nhỏ sẽ xuất hiện trong Cài đặt-Giới thiệu)
- Tối ưu hóa giao diện cấu hình LLM và thêm chức năng lấy danh sách các model có sẵn
- Đã thêm phiên bản Web thích ứng
- Tối ưu hóa mã và sửa lỗi

</details>

<details>
<summary>v0.8.5</summary>

- Thay thế hoàn toàn khung đại lý mới; chức năng trợ lý cảm hứng được tối ưu hóa và giao diện người dùng
- Đã thêm cài đặt liên quan đến trợ lý cảm hứng
- Chế độ React được triển khai lại để triển khai công cụ định dạng văn bản gọi cho các mô hình, phù hợp với các mô hình có khả năng gọi công cụ kém. Có thể bật trong Cài đặt-Trợ lý cảm hứng (mặc định tắt)
- Tương thích với mô hình suy luận và thêm chế độ tư duy
- Khuyến nghị các nhà cung cấp lựa chọn/sửa đổi mô hình như DeepSeek và Qwen phải tương thích với OpenAI, trong khi OpenAI chỉ được đặt thành các mô hình chính thức như GPT 5.
- Một số tối ưu hóa khác
- Tối ưu hóa mã và sửa lỗi

</details>

<details>
<summary>v0.8.3</summary>

- Tăng cường chức năng trợ lý cảm hứng
  - Đã thêm chế độ ReAct: tương thích với nhiều mô hình LLM hơn (gọi công cụ định dạng văn bản), chế độ tiêu chuẩn/ReAct có thể được chuyển đổi trong cài đặt
    (Lưu ý: Do hạn chế về thời gian nên việc triển khai chế độ ReAct tương đối khó khăn và có thể mắc một số lỗi. Nên ưu tiên sử dụng các công cụ gốc để gọi các mô hình có hỗ trợ tốt hơn)
  - Nâng cao trí thông minh theo ngữ cảnh: Giá trị trả về của công cụ bổ sung thêm thông tin thẻ gốc và AI có thể hiểu chính xác hơn mối quan hệ phân cấp thẻ.

- Tối ưu hóa giao diện người dùng và trải nghiệm
  - Tái tạo vùng thẻ tham khảo: bố cục cố định, nút `...(N)` luôn hiển thị, sử dụng Popover thay vì Modal
  - Công cụ tối ưu hóa hiển thị kết quả cuộc gọi: hiển thị trạng thái thành công/thất bại, hỗ trợ thẻ nhảy, có thể gập lại để xem JSON hoàn chỉnh
  - Đã khắc phục sự cố chồng chéo giữa thẻ tham chiếu và lựa chọn mô hình, đồng thời điều chỉnh độ cao của hộp nhập liệu
- Tối ưu hóa mã và sửa lỗi

</details>

<details>

<summary>v0.8.2</summary>

- Tối ưu hóa lệnh gọi công cụ trợ lý cảm hứng và thêm chức năng thử lại tự động. Số lần thử lại tối đa có thể được cấu hình thông qua tệp .env
- Chức năng kéo và thả thẻ nâng cao, cho phép sắp xếp miễn phí
- Tối ưu hóa giao diện người dùng trợ lý cảm hứng và hỗ trợ hiển thị đánh dấu
- Sửa lỗi và dọn sạch mã

</details>

<details>

<summary>v0.8.0</summary>

- Tái cấu trúc trình soạn thảo chương
  - Đã di chuyển từ cửa sổ riêng sang cột giữa của trình chỉnh sửa chính để thống nhất trải nghiệm chỉnh sửa
  - Đã thêm chỉnh sửa nhanh bằng nhấp chuột phải: nhấp chuột phải sau khi chọn văn bản để nhập yêu cầu đánh bóng/mở rộng
  - Tối ưu hóa việc lắp ráp bối cảnh: tự động bao gồm bối cảnh khi đánh bóng/mở rộng, giúp kết nối tự nhiên hơn
  - Làm nổi bật động nội dung do AI tạo

- Trợ lý cảm hứng nâng cao
  - Khả năng gọi công cụ mới (thử nghiệm): thẻ có thể được tạo/sửa đổi trực tiếp trong cuộc trò chuyện và hỗ trợ các thao tác như tìm kiếm và xem cấu trúc loại.
  - Quản lý lịch sử hội thoại: Lưu trữ lịch sử hội thoại theo dự án, hỗ trợ thêm/tải/xóa hội thoại
  - Phản hồi gọi công cụ thời gian thực: "Công cụ gọi ..." được hiển thị và cây thẻ sẽ tự động được làm mới sau khi hoàn thành
  - Tối ưu hóa việc xây dựng bối cảnh: tự động đưa cây cấu trúc dự án, thông tin thống kê và lịch sử hoạt động

- Tối ưu hóa hệ thống quy trình làm việc
  - Cơ chế đăng ký tự động nút: việc thêm một nút chỉ cần một dòng trang trí và giao diện người dùng được tự động đồng bộ hóa
  - Thư viện nút động: tải động danh sách nút từ phần phụ trợ, mở rộng cấu hình bằng không

- Tối ưu hóa giao diện người dùng và trải nghiệm
  - Đã khắc phục nhiều sự cố hiển thị ở chế độ tối
  - Tối ưu hóa bố cục trình chỉnh sửa thẻ và chi tiết tương tác
  - Cải thiện phản hồi trực quan cho đầu ra phát trực tuyến

Lưu ý: Nếu trước đây bạn chọn phát triển cục bộ, bạn cần cài đặt lại các yêu cầu phụ trợ khi cập nhật phiên bản hiện tại.

</details>

<details>

<summary>v0.7.8</summary>

- Hệ thống quy trình làm việc (thử nghiệm) tiếp tục phát triển
  - Đã thêm "Kích hoạt tạo dự án (onprojectcreate)" để thay thế mẫu dự án cũ bằng quy trình làm việc
  - Tối ưu hóa tương tác canvas: kéo và thả để tạo nút, xóa đường kết nối và định vị tọa độ chính xác hơn
  - Một số tối ưu hóa khả năng sử dụng trong studio quy trình công việc và bảng thông số nút
  - Lưu ý: Quy trình làm việc vẫn đang trong giai đoạn thử nghiệm và hiện chủ yếu được sử dụng để thay thế dần logic mã hóa cứng ban đầu. Vẫn còn nhiều chỗ cần cải thiện trong việc mở rộng các khả năng mới.

- Tối ưu hóa mã
  - Dọn dẹp code và giao diện liên quan đến mẫu dự án cũ và thống nhất vào hệ thống quy trình làm việc

</details>

<details>

<summary>v0.7.7</summary>

- Tối ưu thẻ tag công việc
  - Thêm mục nhãn và dữ liệu tùy chọn
  - Trích xuất dữ liệu danh mục mục thẻ và đặt nó làm kho lưu trữ tệp cơ sở kiến thức. Bạn có thể chỉnh sửa thẻ công việc trong Cài đặt-Cơ sở Kiến thức và tự do sửa đổi danh mục mục thẻ.
- Đã thêm chức năng ngắt khi thẻ AI được tạo
- Tối ưu hóa mã, sửa lỗi và định cấu hình xem có đặt lại cơ sở kiến thức, lời nhắc, v.v. khi khởi động thông qua .env hay không

</details>

<details>

<summary>v0.7.6</summary>

- Tăng cường quản lý LLM
  - Cấu hình LLM hỗ trợ "kết nối thử nghiệm".
  - Hỗ trợ cài đặt sử dụng: Bạn có thể đặt giới hạn trên của Token và giới hạn trên của cuộc gọi (-1 nghĩa là không giới hạn).
  - Danh sách hiển thị "đã sử dụng (đầu vào/đầu ra/cuộc gọi)" và cung cấp "thống kê đặt lại bằng một cú nhấp chuột". (Số liệu thống kê hiện tại về việc sử dụng mã thông báo là số liệu thống kê sơ bộ và phương pháp tính toán của các mô hình khác nhau có thể khác nhau, chỉ mang tính chất tham khảo)

- Tối ưu hóa code và trải nghiệm

</details>

<details>
<summary>v0.7.5</summary>

- Tối ưu hóa: Trợ lý truyền cảm hứng
  - Hỗ trợ tham chiếu miễn phí tới nhiều dữ liệu thẻ (dự án chéo, sao chép và gắn thẻ nguồn).
  - Có thể chọn mô hình LLM trong hộp thoại (có thể ghi đè cấu hình thẻ).
  - Lịch sử hội thoại được dự án lưu và khôi phục, không bị mất khi tải lại.
  - Một số chi tiết giao diện người dùng và tương tác được tối ưu hóa.

- Sơ bộ: Workflow (Thử nghiệm)
  - Đã thêm "Workflow Studio": canvas (Vue Flow), thanh bên tham số, thư viện nút và kích hoạt CRUD cơ bản.
  - Chạy và sự kiện: Hỗ trợ SSE, `run_completed` mang `affected_card_ids` và giao diện người dùng được làm mới chính xác theo độ chi tiết của thẻ.
  - Lưu ý quan trọng: Đây hiện là chức năng thử nghiệm và các chức năng như tương tác UI/DSL/xác minh/Runner/trình kích hoạt vẫn đang được cải thiện.

</details>

<details>
<summary>v0.7.0</summary>

- Mới: Trợ lý truyền cảm hứng
  - Các công cụ cộng tác đàm thoại ở bảng bên phải hỗ trợ thảo luận theo thời gian thực và tối ưu hóa lặp đi lặp lại nội dung thẻ.
  - Chức năng tham chiếu thẻ liên dự án có thể đưa dữ liệu thẻ từ bất kỳ dự án nào vào các cuộc hội thoại để kích thích sự va chạm sáng tạo.
  - Tự động tham chiếu thẻ hiện được chọn để chuyển đổi ngữ cảnh liền mạch.
  - "Tạo quyết toán" chỉ bằng một cú nhấp chuột để áp dụng trực tiếp kết quả hội thoại vào nội dung thẻ.
  - Đặt lại chức năng hội thoại để thuận tiện cho việc mở ra những cuộc thảo luận sáng tạo mới.

- Mới: Bàn làm việc ý tưởng
  - Chế độ cửa sổ độc lập cung cấp một môi trường tập trung để khám phá sáng tạo.
  - Hệ thống thẻ miễn phí, không bị ràng buộc bởi cấu trúc dự án.
  - Khả năng trích dẫn liên dự án và tích hợp sáng tạo.
  - Di chuyển/sao chép thẻ miễn phí vào các dự án chính thức chỉ bằng một cú nhấp chuột.

- Tối ưu hóa: Chức năng nhập thẻ
  - Nâng cấp "Nhập thẻ miễn phí" thành "Nhập thẻ" để hỗ trợ nhập từ bất kỳ dự án nào.
  - Cải thiện bộ chọn thẻ, nhóm theo loại và hỗ trợ gấp/mở rộng.
  - Tối ưu hóa bộ đệm dữ liệu tham chiếu để cải thiện hiệu suất và tốc độ phản hồi.

</details>

<details>
<summary>v0.6.5</summary>

- Mới: Mẫu dự án - Đã di chuyển sang hệ thống quy trình công việc trong v0.7.8
  - Đã thêm quản lý "Mẫu dự án" vào trang cài đặt, hỗ trợ định cấu hình các loại thẻ và trình tự được tạo tự động khi tạo dự án mới, hình thành một quy trình sáng tạo có thể tái sử dụng; nhiều mẫu có thể được duy trì.
  - Dự án mới hỗ trợ lựa chọn mẫu.
  - Mô hình dữ liệu mẫu mới và giao diện CRUD được thêm vào phần phụ trợ và mẫu dự án mặc định sẽ tự động được ghi khi ứng dụng khởi động.

</details>

---

<a id="Chồng công nghệ"></a>
## 🛠️ Ngăn xếp công nghệ

* **Giao diện người dùng:** Electron, Vue 3, TypeScript, Pinia, Element Plus
* **Phần cuối:** FastAPI, SQLModel (Pydantic + SQLAlchemy), Uvicorn
* **Cơ sở dữ liệu:** SQLite (Dữ liệu cốt lõi), Neo4j (Sơ đồ tri thức)

---

<a id="Hướng dẫn vận hành"></a>
## 🚀 Hướng dẫn sử dụng

Cho dù bạn muốn trải nghiệm trực tiếp hay tham gia phát triển, bạn đều có thể bắt đầu một cách dễ dàng.

### 0. Neo4j Desktop (tùy chọn, không bắt buộc)

Dự án đã sử dụng sqlite theo mặc định để triển khai lưu trữ biểu đồ mối quan hệ, nhưng nó cũng có thể được chuyển sang neo4j để lưu trữ. Các bước thực hiện như sau

* Vui lòng tải xuống và cài đặt **Neo4j Desktop**, phiên bản được đề xuất **5.16** trở lên.
* Địa chỉ tải xuống: [Neo4j Desktop](https://neo4j.com/download/)
* Sau khi cài đặt, hãy tạo một phiên bản cơ sở dữ liệu cục bộ và đảm bảo nó ở **trạng thái chạy**. Thông tin kết nối mặc định có thể được định cấu hình trong tệp `.env`.
![văn bản thay thế](docImgs/README/image-6.png)

### Cách 1: Chạy từ mã nguồn (nhà phát triển/tính năng mới nhất) (người không phải nhà phát triển nên sử dụng cách 2)

**1. Phần cuối (Python / FastAPI)**
``` bash
# Sao chép kho lưu trữ
bản sao git https://github.com/RhythmicWave/NovelForge.git
cd NovelForge/phụ trợ

conda create -n NovelForge python=3.11
conda activate NovelForge

# Cài đặt phụ thuộc
cài đặt pip -r require.txt

Sửa đổi tệp phụ trợ/.env.example thành .env

#Chạy dịch vụ phụ trợ
python main.py
```

**2. Giao diện người dùng (Node.js / Electron)**
``` bash
# Nhập thư mục front-end
cd ../frontend

# Cài đặt phụ thuộc
cài đặt npm

# Khởi động máy chủ phát triển
npm run dev
# Bạn cũng có thể sử dụng lệnh sau để khởi động trang web
// npm chạy dev:web
```

**3. Bắt đầu đồng thời mặt trước và mặt sau (npm) bằng một dòng lệnh**
``` bash
npm run dev
```

#### QUAN TRỌNG: BOOTSTRAP_OVERWRITE cho .env

> Khi khởi động backend, hệ thống sẽ khởi tạo/cập nhật các tài nguyên tích hợp (cơ sở kiến ​​thức, lời nhắc, quy trình làm việc, v.v.) nếu cần. Liệu các bản cập nhật ghi đè có được kiểm soát bởi `BOOTSTRAP_OVERWRITE` trong `.env` hay không.

- Cài đặt được đề xuất:
  - Nếu bạn chưa trực tiếp sửa đổi các tài nguyên tích hợp thì nên đặt thành:
    ``` tôi
    BOOTSTRAP_OVERWRITE=true
    ```
    Điều này sẽ tự động đồng bộ hóa cơ sở kiến thức/từ nhắc nhở/quy trình làm việc tích hợp mới nhất khi nâng cấp phiên bản hoặc khởi động lại.
  - Nếu bạn đã trực tiếp sửa đổi tài nguyên "tích hợp" thì nên đặt thành `false` để tránh bị ghi đè.

- Khuyến nghị (để tránh bị ghi đè):
  - Không chỉnh sửa trực tiếp tài nguyên "tích hợp".
  - Nếu bạn cần tùy chỉnh, vui lòng tạo một bản sao mới (sao chép cơ sở kiến ​​thức/từ nhắc/quy trình công việc và đổi tên) và sửa đổi nó trên bản sao. Bằng cách này, ngay cả khi `BOOTSTRAP_OVERWRITE=true` được đặt trong tương lai, bản sao tùy chỉnh của bạn sẽ không bị ghi đè bởi logic cập nhật.

### Cách 2: Sử dụng phiên bản phân phối (bắt đầu nhanh)

Các phiên bản phát hành đôi khi được đóng gói, không cần định cấu hình môi trường phát triển và có thể sử dụng ngay.

1. Đi đến trang **Bản phát hành** của dự án để tải xuống gói nén phiên bản di động mới nhất (`.zip` hoặc `.7z`).
2. Giải nén nó vào bất kỳ vị trí nào.
3. **(Quan trọng)** Trước khi chạy, vui lòng đảm bảo rằng phiên bản cơ sở dữ liệu trong Neo4j Desktop đã được khởi động.
4. Nhập thư mục đã giải nén, tìm thư mục `backend` và chỉnh sửa tệp `.env` nếu cần để định cấu hình kết nối cơ sở dữ liệu.
5. Chạy `backend/NovelForgeBackend.exe` để khởi động dịch vụ phụ trợ.
6. Trở lại cấp độ trước đó và chạy `NovelForge.exe` để khởi động chương trình chính.

> Hầu hết dữ liệu được lưu trữ trong cơ sở dữ liệu backend/novelforge.db. Khi phiên bản được cập nhật/di chuyển, chỉ cần sao chép tệp cơ sở dữ liệu vào vị trí tương ứng.
---

## ✍️Quy trình sáng tạo

1. **Định cấu hình Mô hình ngôn ngữ lớn (LLM)**
    * Sau lần khởi động đầu tiên, hãy thêm cấu hình mô hình AI của bạn vào cài đặt, chẳng hạn như Khóa API, URL cơ sở, v.v.
    ![văn bản thay thế](docImgs/README/image.png)
    Bạn nên sử dụng cấp độ Gemini 2.5Pro trở lên LLM để tạo.

2. **Tạo dự án và khởi tạo quy trình làm việc**
    * Khi tạo một dự án mới, bạn có thể chọn quy trình khởi tạo (thường là loại `onprojectcreate`) để tự động tạo các thẻ cài sẵn. Hệ thống có quy trình làm việc "Tạo dự án·Phương pháp tạo bông tuyết" tích hợp sẵn, quy trình này sẽ tự động tạo một bộ cây thẻ hoàn chỉnh theo Phương pháp tạo bông tuyết.
    ![văn bản thay thế](docImgs/README/image-1.png)

3. **Từ trên xuống, điền cài đặt cốt lõi**
    * Bắt đầu từ thẻ trên cùng và tiến hành từng bước (tóm tắt một câu → dàn ý câu chuyện → thế giới quan → bản thiết kế cốt lõi).
    * Mỗi thẻ có thể mở hộp thoại tạo AI, nhập các yêu cầu và hệ thống sẽ tạo thẻ đó theo cách phát trực tuyến theo mức độ chi tiết của trường.
    * Bạn có thể chọn "Xác nhận" sau khi tạo để thả trực tiếp vào thư viện hoặc gửi phản hồi để tiếp tục lặp lại. Nếu bạn không hài lòng, bạn không cần phải bắt đầu lại.
    Sau khi hoàn thành việc tạo thẻ bản thiết kế cốt lõi, hãy nhấp vào Lưu và các thẻ tập tương ứng sẽ được tạo tự động dựa trên số lượng tập.
    Chỉ cần tiếp tục hoàn thành việc tạo đề cương tập, bắt đầu từ Tập 1.
    Sau khi hoàn thành, các thẻ phụ dàn ý công đoạn và thẻ hướng dẫn viết sẽ được tạo tự động dựa trên số lượng công đoạn. Bạn nên tạo thẻ hướng dẫn viết trước, tạo thông tin hướng dẫn viết và sau đó tạo thẻ phác thảo giai đoạn.
    ![văn bản thay thế](docImgs/README/image-2.png)
    Quy trình ví dụ về thẻ do AI tạo:
    ![văn bản thay thế](docImgs/README/image-28.png)
    ![văn bản thay thế](docImgs/README/image-29.png)
    Sau khi tạo xong, nhấp vào Kết thúc và lưu thẻ. Hoặc nếu bạn không hài lòng ở một số lĩnh vực, vui lòng nhập hướng dẫn để phản hồi.

4. **Cải thiện nội dung với sự trợ giúp của trợ lý truyền cảm hứng**
    * Trong quá trình viết, nếu bạn muốn trau chuốt hoặc tối ưu hóa thêm nội dung thẻ, bạn có thể sử dụng trợ lý cảm hứng ở bên phải bất cứ lúc nào.
    * Sau khi chọn thẻ bất kỳ, trợ lý truyền cảm hứng sẽ tự động đọc nội dung thẻ để bạn tham khảo và suy nghĩ dễ dàng hơn.
    * Bạn có thể trực tiếp hỏi trợ lý những câu hỏi cụ thể như “Động cơ của nhân vật này có hợp lý không?”, “Làm thế nào để cảnh này căng thẳng hơn?”, v.v.
    * Trợ lý truyền cảm hứng sẽ đưa ra các đề xuất có mục tiêu dựa trên nội dung thẻ hiện tại. Bạn có thể liên lạc nhiều lần với trợ lý để dần dần cải thiện ý tưởng của mình.
    * Thông qua nút "Thêm tài liệu tham khảo", bạn cũng có thể thêm nội dung thẻ có liên quan của dự án hiện tại hoặc các dự án khác vào cuộc trò chuyện để khơi dậy nhiều tia sáng tạo hơn.
    * Trợ lý truyền cảm hứng có khả năng nhận biết ngữ cảnh và gọi các công cụ để sửa đổi/tạo nội dung thẻ (thử nghiệm)
    ![Văn bản thay thế](docImgs/README/image-20.png)

#### Hộp thoại do AI tạo ra và trợ lý truyền cảm hứng (cách chọn)

- **Hộp thoại tạo AI**: Tập trung vào thẻ đơn hiện tại, được sử dụng để tạo và lặp lại nhanh chóng nội dung của thẻ; phiên chỉ kéo dài cho đến khi kết thúc quá trình tạo này và phiên sẽ bị xóa sau khi đóng hộp thoại.
- **Trợ lý truyền cảm hứng**: Được sử dụng để đối thoại và sáng tạo liên tục trên các thẻ và dự án; nhiều thẻ có thể được tham chiếu để phân tích và tạo liên kết, đồng thời lịch sử hội thoại có thể được lưu liên tục.
- **Cách sử dụng được đề xuất**:
  - Mục tiêu là “viết thiệp này hay” → Sử dụng AI để tạo hộp thoại.
  - Mục tiêu là "tư duy liên kết xuyên suốt/thảo luận lâu dài/hợp tác nhiều thẻ" → Sử dụng trợ lý truyền cảm hứng.

5. **Sau khi hoàn thành việc tạo phác thảo giai đoạn, phác thảo chương và thẻ văn bản chương sẽ tự động được tạo và các thực thể cần tham gia vào mỗi chương sẽ tự động được thêm vào. **
    ![văn bản thay thế](docImgs/README/image-3.png)

6. **Vào Tạo chương**
    * Sau khi hoàn thành các bước trên, bấm vào thẻ văn bản chương tương ứng để mở trình soạn thảo chương và vào giao diện viết cốt lõi. Bảng ngữ cảnh ở bên phải tự động chuẩn bị tất cả thông tin cơ bản bạn cần cho chương hiện tại.
    ![Văn bản thay thế](docImgs/README/image-27.png)

    * Bạn có thể nhấn Continue để viết cho thế hệ AI (nếu chưa có nội dung sẽ tự động viết lại từ đầu).
    * Có thể chọn hai chế độ kiểm soát số từ khi tiếp tục viết:
         - **Ràng buộc từ nhắc**: Chỉ hạn chế số lượng từ ở cấp độ từ nhắc, giúp văn bản trở nên tự nhiên hơn và tiết kiệm mã thông báo.
         - **Chế độ kiểm soát**: Chia ngân sách thành nhiều vòng theo tổng số từ mục tiêu, phù hợp với tình huống tổng số từ của các chương nghiêm ngặt hơn nhưng sẽ tiêu tốn nhiều token hơn.
    * Nếu bạn không hài lòng với nội dung được tạo, bạn có thể chọn nội dung và nhấp chuột phải để chỉnh sửa nhanh, sau đó nhập yêu cầu và nhấp vào Ba Lan/Mở rộng để viết lại phần nội dung này.
    ![Văn bản thay thế](docImgs/README/image-8.png)

* Văn bản chương cũng hỗ trợ ôn tập trực tiếp:
         - Nhấp vào nút **Kiểm tra** ở trên cùng để thực hiện kiểm tra
         - Bạn có thể chuyển đổi các từ nhắc ôn tập thông qua nút thả xuống ở bên phải nút
         - Việc xem xét sẽ quay lại bản nháp trước, sau đó lưu dưới dạng thẻ kết quả xem xét sau khi xác nhận.
         - Các kết quả đã lưu sẽ tự động được đặt vào thư mục **Kết quả kiểm toán** cấp cơ sở và có thể được xem ở bảng bên phải

* Sau khi tạo nội dung xong click vào mối quan hệ trong hình để phân tích mối quan hệ giữa các nhân vật và lưu vào bản đồ kiến ​​thức để tham khảo ở những lần viết tiếp theo.
    ![Văn bản thay thế](docImgs/README/image-7.png)
    Sau khi giải nén xong nhấn vào Xác nhận để lưu vào cơ sở dữ liệu neo4j.
    ![văn bản thay thế](docImgs/README/image-5.png)

* Nên trích xuất lại thông tin động của ký tự và sử dụng mô hình chi phí thấp hơn để trích xuất nó.

* Sau khi hoàn thành các bước trên, thông tin của các đơn vị tham gia có liên quan sẽ tự động được đưa vào khi tạo chương tiếp theo.
    ![văn bản thay thế](docImgs/README/image-9.png)

7. **Bàn làm việc đầy cảm hứng: Nắm bắt tia sáng sáng tạo**
    * Có ý tưởng mới nhưng chưa biết nên thuộc dự án nào? Nhấp vào nút "Cảm hứng" ở đầu trang để mở cửa sổ bàn làm việc truyền cảm hứng độc lập.
    * Tại đây, bạn có thể ghi lại nhiều ý tưởng khác nhau và tạo các loại thẻ khác nhau một cách thoải mái mà không cần phải xem xét cấu trúc dự án và tập trung vào việc đưa cảm hứng của mình vào thực tế.
    * Trợ lý truyền cảm hứng bên phải hỗ trợ tham khảo nội dung thẻ của bất kỳ dự án nào, giúp bạn dễ dàng kiểm tra, so sánh, tổng hợp giữa các dự án để truyền cảm hứng sáng tạo hơn.
    * Khi một ý tưởng dần hình thành, chỉ cần sử dụng chức năng "Di chuyển/Sao chép vào dự án" ở trên cùng để thêm thẻ miễn phí vào dự án chính thức chỉ bằng một cú nhấp chuột, và sự sáng tạo sẽ được kết nối một cách tự nhiên với những sáng tạo tiếp theo.
    ![Văn bản thay thế](docImgs/README/image-21.png)
    ![Văn bản thay thế](docImgs/README/image-22.png)
---

## ⚙️ Chức năng và cấu hình nâng cao

Mặc dù NovelForge cung cấp quy trình làm việc sáng tạo được đề xuất nhưng sức mạnh thực sự của nó nằm ở mức độ linh hoạt cao. Bạn hoàn toàn có thể từ bỏ các cài đặt trước và sử dụng các công cụ sau để lắp ráp hệ thống sáng tạo của riêng mình.

<a id="schema-first"></a>
### Schema-first: cấu trúc kiểu/thể hiện và các tham số

* Trong `Cài đặt -> Loại thẻ`, hãy sử dụng trình tạo lược đồ để xác định `json_schema` cho loại (hỗ trợ các loại cơ sở, quan hệ (nhúng), bộ dữ liệu, v.v.). Lược đồ loại sẽ được sử dụng làm cấu trúc mặc định cho các thẻ loại này.
    ![văn bản thay thế](docImgs/README/image-10.png)
    ![văn bản thay thế](docImgs/README/image-11.png)

* Trong một thẻ cụ thể, bạn có thể mở `Structure` (Schema Studio) để ghi đè cấu trúc của phiên bản thẻ hoặc "Áp dụng để nhập" chỉ bằng một cú nhấp chuột.
    ![văn bản thay thế](docImgs/README/image-12.png)

    ![alt text](docImgs/README/image-13.png)

Sau khi được áp dụng cho một loại, các thẻ tiếp theo thuộc loại đó sẽ sử dụng cấu trúc mới.

* Thông số AI của thẻ: Đặt mô hình, từ nhắc nhở, nhiệt độ và các thông số khác thông qua thanh công cụ soạn thảo (`llm_config_id`, `prompt_name`, `nhiệt độ`, `max_tokens`, `timeout`).
    ![văn bản thay thế](docImgs/README/image-14.png)

* Sau khi hoàn thành các cài đặt trên, bạn có thể tạo loại thẻ này trong dự án và thực hiện tạo AI. Hệ thống sẽ sử dụng "Lược đồ hợp lệ" của thẻ để xác minh và xuất dữ liệu có cấu trúc.
    ![văn bản thay thế](docImgs/README/image-15.png)
    Khi tạo thẻ mới, bạn cũng có thể kéo thẻ trực tiếp từ thẻ hiện có xuống dưới cùng để tự động tạo thẻ.
    ![văn bản thay thế](docImgs/README/image-16.png)

    ![alt text](docImgs/README/image-17.png)

* Lược đồ hỗ trợ nhúng (`$ref` thành loại `$defs`) và có thể kết hợp cũng như sử dụng lại các cấu trúc hiện có để tạo điều kiện thuận lợi cho việc xây dựng các khả năng tổng hợp.

![văn bản thay thế](docImgs/README/image-18.png)

Lưu ý, hãy thử thêm mô hình mới thay vì sửa đổi cấu trúc mô hình hiện có để tránh xung đột với dữ liệu hiện có.

### Review chương và review chung

Ngoài văn bản chương, các thẻ khác (chẳng hạn như dàn ý giai đoạn, văn bản chung, v.v.) cũng có thể trực tiếp sử dụng nút **Đánh giá** ở trên cùng.

- Lối vào ôn tập được thống nhất thành một nút và các từ nhắc ôn tập có thể được chuyển đổi ở bên phải nút
- Theo mặc định, phác thảo giai đoạn sử dụng từ nhắc `giai đoạn xem xét`
- Các thẻ thông thường sử dụng từ nhắc `General Review` theo mặc định
- Kết quả review được lưu thống nhất dưới dạng `thẻ review nội dung`

Bằng cách này, bạn có thể định cấu hình các tiêu chuẩn đánh giá khác nhau cho các loại thẻ khác nhau trong khi vẫn duy trì cấu trúc kết quả đánh giá và phương pháp xem thống nhất.

<a id="prompt-workshop"></a>
### Hội thảo nhắc nhở

* Đằng sau tất cả các chức năng AI là các mẫu từ gợi ý có thể chỉnh sửa. Tại đây bạn có thể sửa đổi các mẫu cài sẵn hoặc tạo các mẫu hoàn toàn mới.
* **Chèn cơ sở kiến ​​thức**: Hỗ trợ tham chiếu động đến nội dung "cơ sở kiến ​​thức" bằng các từ gợi ý thông qua cú pháp `@KB{name=tên cơ sở kiến ​​thức}`, cung cấp thông tin cơ bản phong phú hơn cho AI.

<a id="context-dsl"></a>
### Giải thích chi tiết về chèn bối cảnh (@DSL)

Đây là một tính năng của NovelForge. Nó cho phép bạn sử dụng ký hiệu `@` để tham chiếu chính xác bất kỳ dữ liệu nào trong dự án dưới dạng ngữ cảnh trong mẫu từ nhắc.

* **Trích dẫn theo tiêu đề**: `@cardtitle` hoặc `@cardtitle.content.certain field`
* **Tham khảo theo loại**: `@type:Character Card` (tất cả các thẻ nhân vật)
* **Tài liệu tham khảo đặc biệt**: `@self` (thẻ hiện tại), `@parent` (thẻ gốc)
* **Bộ lọc mạnh mẽ**:
    * `[trước]`: Lấy thẻ trước cùng cấp.
    * `[previous:global:n]`: Lấy n thẻ cùng loại gần nhất theo thứ tự chung (thứ tự cây).
    * `[anh chị em]`: Nhận tất cả các thẻ anh chị em cùng cấp.
    * `[index=...]`: Nhận theo số sê-ri, hỗ trợ các biểu thức, chẳng hạn như `$self.content.volume_number - 1`.
    * `[filter:...]`: Lọc theo điều kiện, chẳng hạn như `[filter:content.level > 5]` hoặc `[filter:content.name in $self.content.entity_list]`.
* **Lựa chọn cấp độ trường**: Có thể chọn toàn bộ dữ liệu thẻ hoặc có thể chọn riêng lẻ các trường của thẻ.

Ví dụ: trích dẫn tiêu đề chương và văn bản gốc của 3 chương cuối:
![Văn bản thay thế](docImgs/README/image-23.png)

<a id="workflow-system"></a>
### Hệ thống quy trình làm việc (quy trình làm việc được mã hóa + Tác nhân quy trình làm việc)

Hệ thống quy trình công việc được sử dụng để tổ chức các hành động sáng tạo phổ biến (khởi tạo dự án, tự động tạo thẻ con sau khi lưu, xử lý hàng loạt nội dung, v.v.) thành các quy trình có thể sử dụng lại và tự động thực hiện chúng vào thời điểm thích hợp.

Hiện tại, quá trình xây dựng lại dòng chính dựa trên mã đã hoàn tất và giải pháp quy trình làm việc kiểu DAG cũ đã bị xóa.

<a id="workflow-studio"></a>
#### Hệ thống quy trình làm việc

- Truy cập trang Quy trình công việc để chỉnh sửa quy trình công việc ở chế độ xem mã và hình ảnh.
- Quy trình có thể được xây dựng nhanh chóng thông qua thư viện nút hoặc mã có thể được viết/sửa đổi trực tiếp.
- Bảng tham số hỗ trợ chỉnh sửa và xác minh theo thời gian thực và các sửa đổi có thể được áp dụng một cách an toàn cho mã quy trình làm việc.
- Hỗ trợ xem các bản ghi đang chạy, kết quả thực hiện và thông báo lỗi để thuận tiện cho việc gỡ lỗi lặp lại.

![alt text](docImgs/README/image-30.png)

<a id="workflow-triggers"></a>
#### Cấu hình kích hoạt

Mỗi quy trình công việc có thể được cấu hình bằng một hoặc nhiều trình kích hoạt để xác định thời điểm thực thi tự động:

- **Kích hoạt khi lưu**: Tự động thực thi khi lưu loại thẻ được chỉ định
- **Kích hoạt khi tạo dự án**: Tự động thực thi sau khi tạo dự án mới (thường được sử dụng để khởi tạo dự án)

<a id="workflow-status-bar"></a>
#### Thanh trạng thái quy trình làm việc (chạy nền chung)

- Sau khi quy trình làm việc chạy, trạng thái sẽ được hiển thị trên thanh trạng thái quy trình làm việc chung (không giới hạn ở trang quy trình làm việc).
- Bạn có thể chuyển sang các trang khác để tiếp tục tạo và quy trình làm việc được thực hiện ở chế độ nền.
- Thanh trạng thái sẽ hiển thị số lượng đang chạy, nút hiện tại, tiến độ tổng thể và trạng thái hoàn thành.

![alt text](docImgs/README/image-25.png)

<a id="workflow-progress-recovery"></a>
#### Tiến trình cấp nút và phục hồi gián đoạn (Beta)

- Hệ thống hỗ trợ báo cáo tiến trình cấp nút và bạn có thể xem "nút nào hiện đang được thực thi".
- Hỗ trợ tạm dừng/tiếp tục thực thi và giữ nguyên trạng thái đang chạy để tiếp tục chạy.
- Hỗ trợ tính kiên trì và xem các bản ghi đang chạy.
- Lưu ý: Phần khả năng này đã có sẵn và có thể có một số vấn đề về ranh giới trong các quy trình phức tạp (chẳng hạn như các kịch bản khôi phục riêng lẻ).

<a id="workflow-persistent-vs-temporary"></a>
#### Quy trình làm việc liên tục và quy trình làm việc tạm thời

- **Quy trình làm việc tạm thời (mặc định)**: Bản ghi đang chạy được sử dụng để xem và gỡ lỗi hiện tại và sẽ tự động được làm sạch sau.
- **Quy trình làm việc liên tục**: Sau khi bật "lưu liên tục", các bản ghi đang chạy sẽ được lưu giữ trong thời gian dài (bị ảnh hưởng bởi chính sách lưu giữ của hệ thống).

<a id="workflow-buildins"></a>
#### Mẫu quy trình làm việc tích hợp sẵn

Hệ thống được cài đặt sẵn một số quy trình công việc phổ biến, có thể được sử dụng trực tiếp hoặc làm tài liệu tham khảo:

- **Tạo dự án·Phương pháp tạo bông tuyết**: Khi tạo một dự án mới, cấu trúc thẻ ban đầu sẽ tự động được tạo theo Phương pháp tạo bông tuyết.
- **Chế độ xem thế giới·Chuyển tổ chức**: Tự động tạo thẻ tổ chức từ danh sách lực lượng được đặt trong chế độ xem thế giới
- **Core Blueprint·Lost Card**: Tự động tạo thẻ nhân vật, thẻ cảnh và thẻ tập dựa trên nội dung của bản thiết kế
- **Phác thảo giấy·Thẻ vị trí**: Tự động tạo dàn ý giai đoạn và hướng dẫn viết dựa trên dàn ý giấy
- **Phác thảo giai đoạn·Thẻ chương**: Tự động tạo đề cương chương và thẻ văn bản dựa trên danh sách chương của phác thảo giai đoạn
- **Quy trình tháo dỡ sách**: Dùng để tháo rời cấu trúc văn bản hiện có và triển khai vào hệ thống thẻ

<a id="workflow-project-init"></a>
#### Quy trình khởi tạo dự án

Khi tạo dự án mới, bạn có thể chọn quy trình làm việc có trình kích hoạt `onprojectcreate` làm mẫu dự án:

- "Tạo dự án·Phương pháp tạo bông tuyết" được chọn theo mặc định, tự động tạo các thẻ như thẻ công việc, mánh gian lận, tóm tắt một câu, dàn ý câu chuyện, cài đặt thế giới quan và bản thiết kế cốt lõi.
- Bạn cũng có thể tạo quy trình khởi tạo dự án của riêng mình trong studio quy trình công việc để tùy chỉnh hoàn toàn cấu trúc bắt đầu dự án
- Hỗ trợ logic khởi tạo phức tạp, chẳng hạn như tạo các cấu trúc thẻ khác nhau dựa trên các điều kiện

![Alt text](docImgs/README/image-26.png)

<a id="workflow-agent"></a>
#### Workflow Agent (quy trình viết bằng ngôn ngữ tự nhiên)

- Mở tác nhân quy trình công việc trên trang quy trình công việc và nói mục tiêu của bạn với nó, chẳng hạn như "Tạo quy trình tranh luận đa AI và xuất nó cho dự án đã chỉ định."
- Đại lý sẽ tự động đọc quy trình làm việc hiện tại, tạo kế hoạch sửa đổi và cung cấp kết quả áp dụng sau khi xác minh.
- Sử dụng phương pháp này, bạn không cần xây dựng quy trình làm việc của riêng mình và có thể nhanh chóng triển khai các quy trình phức tạp.
- Có thể vẫn còn một số lỗi

![văn bản thay thế](docImgs/README/image-31.png)
![văn bản thay thế](docImgs/README/image-32.png)
![văn bản thay thế](docImgs/README/image-33.png)
![văn bản thay thế](docImgs/README/image-34.png)
![văn bản thay thế](docImgs/README/image-35.png)
(Giao diện thực hiện ở bên phải là màn hình hiển thị tiến trình chi tiết và thanh trạng thái quy trình làm việc là màn hình hiển thị tiến trình đơn giản)
Việc thực thi một số tác vụ dài hạn có thể được chuyển sang các giao diện khác mà không cần chờ đợi trong giao diện quy trình làm việc. Sau khi thực hiện xong, thanh trạng thái quy trình làm việc sẽ nhấp nháy.

<a id="workflow-examples"></a>
#### Ví dụ về cách sử dụng quy trình làm việc
Quy trình mở sách
Tạo một dự án trống trước tiên
![văn bản thay thế](docImgs/README/image-36.png)

Vào giao diện quy trình làm việc và chọn quy trình mở sách

![alt text](docImgs/README/image-37.png)

Đặt dự án mục tiêu, tên mô hình và thư mục chương tiểu thuyết

![alt text](docImgs/README/image-38.png)

Lưu ý rằng tệp tiểu thuyết phải được lưu trữ theo cách đáp ứng các yêu cầu về định dạng đặt trước, chẳng hạn như chia thành từng chương và lưu trữ dưới dạng tệp txt.
![văn bản thay thế](docImgs/README/image-41.png)

Bấm để thực hiện

Kết quả khi giải nén sách:
![văn bản thay thế](docImgs/README/image-39.png)

Trích xuất dàn ý của chương → chia mạch truyện thành các giai đoạn → tiến hành phân tích tổng thể dựa trên cách kể chuyện của tất cả các giai đoạn

---

## Thỏa thuận cấp phép
Dự án này áp dụng mô hình ủy quyền giấy phép kép:

- Theo mặc định, dự án này được cấp phép theo Giấy phép Công cộng GNU Affero v3.0 (AGPLv3)
- Cung cấp dịch vụ cho mục đích thương mại: Để sử dụng dự án này (hoặc phiên bản sửa đổi) làm phụ trợ để cung cấp dịch vụ cho bên thứ ba trong SaaS, hosting hoặc các hình thức khác, phải có giấy phép ủy quyền thương mại của tác giả.

Vui lòng tuân thủ các điều khoản của thỏa thuận nguồn mở và nhận được ủy quyền tương ứng trong các trường hợp áp dụng.

---

## 📂 Cấu trúc dự án

```
NovelForge/
  ├── backend/        # Backend FastAPI (Phân hệ dịch vụ phía sau)
  │   ├── app/
  │   │   ├── api/        # Định tuyến API (API Routing)
  │   │   ├── db/         # Mô hình cơ sở dữ liệu & Phiên làm việc (Database Models & Sessions)
  │   │   ├── schemas/    # Mô hình dữ liệu Pydantic (Pydantic Data Models)
  │   │   └── services/   # Logic nghiệp vụ cốt lõi (Core Business Logic)
  │   └── main.py       # Điểm khởi chạy (Entry Point)
  │
  └── frontend/       # Frontend Electron + Vue3 (Phần giao diện người dùng)
      └── src/
          ├── main/       # Luồng xử lý chính của Electron (Electron Main Process)
          ├── preload/    # Kịch bản tải trước (Preload Scripts)
          └── renderer/   # Luồng kết xuất của Vue (Vue Renderer Process)
              └── src/
                  ├── components/ # Thành phần Vue (Vue Components)
                  ├── services/   # Dịch vụ giao diện người dùng (Frontend Services)
                  ├── stores/     # Quản lý trạng thái Pinia (Pinia State Management)
                  └── views/      # Giao diện trang hiển thị (Page Views)
```

---

<a id="Nhìn về phía trước"></a>
## Triển vọng

NovelForge vẫn đang trong giai đoạn đầu của quá trình lặp lại và tác giả nhận thức rõ rằng dự án vẫn còn rất nhiều cơ hội để cải thiện về quy trình sáng tạo, duy trì tính nhất quán, thiết kế giao diện người dùng, trải nghiệm tương tác, v.v.

Những công cụ tốt nhất được sinh ra từ trí tuệ của cộng đồng. Cho dù bạn là người sáng tạo hay nhà phát triển, bạn đều được chào đón chân thành:

* Gửi đề xuất hoặc phản hồi về tính năng có giá trị trong **Vấn đề**.
* Chia sẻ những hiểu biết độc đáo của bạn về quá trình sáng tạo.
