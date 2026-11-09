#!/usr/bin/env python3
"""build.py: lối vào cho bộ đăng bài (python3 tools/build.py [--offline]). Gọi theme.py để dựng lại trang chủ, khung bài, sitemap.
Chỉ dùng thư viện chuẩn, không gọi mạng, dưới 5 giây, idempotent, chỉ ghi các đường dẫn nằm trong danh sách cho phép."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import theme  # noqa: E402

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a == "--offline"]
    sys.exit(theme.main([str(HERE.parent)] + args))
