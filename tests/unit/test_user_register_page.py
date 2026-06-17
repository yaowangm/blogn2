from pathlib import Path


REGISTER_PAGE = Path("src/static/user_register.html")


def test_register_page_requires_password_confirmation():
    html = REGISTER_PAGE.read_text(encoding="utf-8")

    assert 'id="confirmPassword"' in html
    assert 'name="confirmPassword"' in html
    assert "validateConfirmPassword()" in html
    assert "两次输入的密码不一致" in html
    assert "const isConfirmPasswordValid = this.validateConfirmPassword();" in html


def test_register_page_recommends_copyable_valid_password():
    html = REGISTER_PAGE.read_text(encoding="utf-8")

    assert 'id="recommendedPassword"' in html
    assert 'id="copyPasswordBtn"' in html
    assert "generateRecommendedPassword()" in html
    assert "window.crypto.getRandomValues" in html
    assert "while (chars.length < 14)" in html


def test_register_api_payload_excludes_client_only_password_fields():
    html = REGISTER_PAGE.read_text(encoding="utf-8")
    payload_start = html.index("const formData = {")
    payload_end = html.index("};", payload_start)
    payload_block = html[payload_start:payload_end]

    assert "password: document.getElementById('password').value" in payload_block
    assert "confirmPassword" not in payload_block
    assert "recommendedPassword" not in payload_block
