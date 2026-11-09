# Cấu hình site ls (Mẹo laptop hằng ngày). URL gốc chỉ nằm trong file này.
BASE_URL = "https://meo-laptop-vn.github.io/"
SITE_NAME = "Mẹo laptop hằng ngày"
PEN = "Lan"
MARK = "M"
AVATAR = "L"
TAGLINE = "Sổ tay mẹo vặt của Lan"
LATEST_N = 12

INDEX_TITLE = "Mẹo laptop hằng ngày - Thiết lập, sửa lỗi nhỏ và phụ kiện"
INDEX_DESC = ("Mẹo dùng laptop Windows 11 theo từng bước: phím tắt, bộ phụ kiện học và làm việc, hỗ trợ người thân từ xa. "
              "Viết gọn, có bảng đối chiếu cho máy 2025 và 2026.")
INDEX_OG_TITLE = INDEX_TITLE
INDEX_OG_DESC = INDEX_DESC
INDEX_H1 = "Những mẹo nhỏ giúp laptop dễ dùng hơn mỗi ngày"
STRAP = "Mình ghi lại các bước thiết lập, phụ kiện và cách hướng dẫn người thân dùng laptop Windows 11."

ABOUT_P = "Mình ghi lại các mẹo dùng laptop Windows 11, viết từng bước và có bảng đối chiếu."
ABOUT_HOME = (
    '<h2 class="sec-t">Về blog</h2>'
    '<p>Mình là Lan. Blog này là cuốn sổ mẹo mình dùng để ghi lại những việc nhỏ khi dùng laptop: '
    'thiết lập Windows 11 cho vừa tay, chọn phụ kiện học và làm việc, hướng dẫn người thân từ xa.</p>'
    '<p>Mỗi bài đi theo từng bước, ngắn gọn, kèm bảng đối chiếu khi cần so sánh. '
    'Mình chỉ nhắc đến máy đời 2025 và 2026 và không ghi giá.</p>'
    '<p>Nếu một bước nào làm chưa ra kết quả, phần cuối bài thường có lưu ý về lỗi hay gặp để bạn đối chiếu.</p>'
)

CATS = [("thiet-lap", "Thiết lập Windows"), ("phu-kien", "Phụ kiện"), ("ho-tro", "Hỗ trợ người thân")]
CAT_RULES = [
    ("phu-kien", "Phụ kiện", ["phu-kien", "numpad", "bang-ve"]),
    ("ho-tro", "Hỗ trợ người thân", ["nguoi-than", "tu-xa", "quick-assist"]),
    ("thiet-lap", "Thiết lập Windows", ["thiet-lap", "windows", "win"]),
]
CAT_DEFAULT = ("thiet-lap", "Thiết lập Windows")

FONTS_URL = ("https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&"
             "family=Nunito+Sans:wght@400;600;700&display=swap")

HEADER = (
    '<body>\n<a class="skip" href="#main">Bỏ qua đến nội dung</a>\n'
    '<header class="top"><div class="wrap mast">'
    '<a class="brand" href="@HOME@"><span class="mark" aria-hidden="true">@MARK@</span>'
    '<span class="bn">@NAME@</span></a>'
    '<p class="tag">@TAGLINE@</p></div>'
    '<nav class="nav" aria-label="Chính"><div class="wrap">@NAV@</div></nav></header>\n'
)
FOOTER = (
    '<footer class="foot"><div class="wrap fo">'
    '<p class="fn">@NAME@</p>'
    '<p>Blog cá nhân của @PEN@, ghi lại mẹo dùng laptop Windows 11 cho máy đời 2025 và 2026.</p>'
    '<p class="sm">Năm @YEAR@. Nội dung viết lại từ tài liệu công khai.</p>'
    '</div></footer>\n</body>\n</html>\n'
)
ABOUT = (
    '<section class="w w-about"><span class="av" aria-hidden="true">@AV@</span>'
    '<h2 class="w-t">@PEN@</h2><p>@ABOUT@</p><a class="more" href="@R@#ve-blog">Về blog</a></section>'
)
POST = (
    '@HEADER@'
    '<div class="wrap lay"><main id="main" class="col post">\n'
    '<p class="crumb"><a href="@R@">Trang chủ</a><span aria-hidden="true"> / </span><span>@CATLABEL@</span></p>\n'
    '@ARTICLE@\n@RELATED@\n</main>\n'
    '<aside class="side">@ABOUT@@CATS@</aside></div>\n'
    '@FOOTER@'
)
INDEX = (
    '@HEADER@'
    '<main id="main">\n'
    '<div class="wrap intro"><h1>@H1@</h1><p>@STRAP@</p></div>\n'
    '<div class="wrap lay"><div class="col">\n'
    '<section class="hero-wrap" aria-label="Bài nổi bật">@HERO@</section>\n'
    '<section id="bai-moi"><h2 class="sec-t">Bài mới nhất</h2>\n<div class="rows">\n@LATEST@\n</div></section>\n'
    '<section id="chu-de"><h2 class="sec-t">Theo chủ đề</h2>\n<div class="tps">@TOPICS@</div></section>\n'
    '<section id="ve-blog" class="about-home">@ABOUT_HOME@</section>\n'
    '</div>\n<aside class="side">@SIDEBAR@</aside></div>\n</main>\n'
    '@FOOTER@'
)
NOTFOUND = (
    '@HEADER@'
    '<main id="main" class="wrap nf"><h1>Không tìm thấy trang này</h1>'
    '<p>Đường dẫn có thể đã đổi hoặc bài chưa được đăng. Quay về trang chủ để xem danh sách bài.</p>'
    '<p><a class="btn" href="@R@">Về trang chủ</a></p></main>\n'
    '@FOOTER@'
)
CARDS = {
    "hero": (
        '<article class="lead"><a class="lead-media" href="@HREF@" tabindex="-1" aria-hidden="true">@MEDIA@</a>'
        '<div class="lead-tx"><p class="kick">@CAT@</p>'
        '<h2><a href="@HREF@">@TITLE@</a></h2><p class="dk">@DESC@</p>'
        '<p class="meta"><time datetime="@ISO@">@DATE@</time><span aria-hidden="true"> · </span>@READ@</p></div></article>'
    ),
    "latest": (
        '<article class="row"><a class="row-media" href="@HREF@" tabindex="-1" aria-hidden="true">@MEDIA@</a>'
        '<div class="row-tx"><p class="kick">@CAT@</p>'
        '<h3><a href="@HREF@">@TITLE@</a></h3><p class="dk">@DESC@</p>'
        '<p class="meta"><time datetime="@ISO@">@DATE@</time><span aria-hidden="true"> · </span>@READ@</p></div></article>'
    ),
}
