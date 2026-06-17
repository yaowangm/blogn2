from pathlib import Path


RESET_PASSWORD_PAGE = Path("src/static/reset-password.html")


def test_reset_password_page_shows_recommended_password():
    html = RESET_PASSWORD_PAGE.read_text(encoding="utf-8")

    assert 'id="recommendedPassword"' in html
    assert 'id="copyPasswordBtn"' in html
    assert 'id="refreshPasswordBtn"' in html
    assert "generateRecommendedPassword()" in html
    assert "document.execCommand('copy')" in html


def test_reset_password_page_keeps_reset_payload_unchanged():
    html = RESET_PASSWORD_PAGE.read_text(encoding="utf-8")
    payload_start = html.index("body: JSON.stringify({ token: token, new_password: newPassword })")

    assert "confirm_password" in html
    assert "new_password: newPassword" in html[payload_start:]
    assert "recommendedPassword" not in html[payload_start:payload_start + 200]
