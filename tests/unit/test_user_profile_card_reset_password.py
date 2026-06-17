from pathlib import Path


PROFILE_CARD = Path("src/static/js/components/user-profile-card.js")


def test_profile_card_reset_modal_recommends_password():
    content = PROFILE_CARD.read_text(encoding="utf-8")

    assert 'id="recommendedPassword"' in content
    assert 'id="copyPasswordBtn"' in content
    assert 'id="refreshPasswordBtn"' in content
    assert "generateRecommendedPassword()" in content
    assert "copyRecommendedPassword()" in content


def test_profile_card_reset_payload_is_unchanged():
    content = PROFILE_CARD.read_text(encoding="utf-8")
    start = content.index("body: JSON.stringify({")
    end = content.index("});", start)
    payload_block = content[start:end]

    assert "new_password: newPassword" in payload_block
    assert "recommendedPassword" not in payload_block
    assert "confirmPassword" not in payload_block
