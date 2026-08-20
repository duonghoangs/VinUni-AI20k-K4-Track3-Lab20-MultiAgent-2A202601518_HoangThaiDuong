# Exit Ticket

## Khi nào nên dùng multi-agent?

Nên dùng khi câu hỏi có nhiều bước độc lập như truy xuất nguồn, đánh giá mâu thuẫn, kiểm tra bằng
chứng và tổng hợp báo cáo. Shared state và trace giúp xác định agent nào tạo dữ liệu, bước nào làm
mất provenance, và chi phí nào tạo ra cải thiện chất lượng. Quyết định cuối cùng phải dựa trên
benchmark của project, đặc biệt là quality, citation coverage và failure rate.

Trong benchmark OpenRouter hiện tại, multi-agent tăng citation coverage trung bình từ khoảng `43%`
lên `61%` và quality trung bình từ `8.27` lên `8.47`. Lợi ích rõ nhất xuất hiện ở hai query về
customer support và production guardrails, nơi workflow chuyên biệt tăng cả quality lẫn citation
coverage. Trace bốn bước cũng giúp kiểm tra handoff và provenance.

## Khi nào không nên dùng multi-agent?

Không nên dùng cho câu hỏi ngắn, một đường thông tin rõ ràng, hoặc khi baseline đã đạt chất lượng và
citation coverage tương đương. Trong các trường hợp đó, single-agent thường ít bước hơn, nhanh hơn,
rẻ hơn và có ít điểm lỗi phối hợp hơn.

Query GraphRAG minh họa đúng trường hợp này: baseline đạt quality `8.7`, cao hơn multi-agent `7.9`,
trong khi nhanh hơn khoảng ba lần và chi phí thấp hơn gần bốn lần. Tính trên cả ba query,
multi-agent mất trung bình khoảng `23.86s` so với `9.14s` của baseline và tốn khoảng `3.3x` chi phí.
Nếu câu hỏi hẹp hoặc không cần trace theo vai trò, baseline là lựa chọn hợp lý hơn.
