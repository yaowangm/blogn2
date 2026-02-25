"""
邮件发送单元测试

测试 SMTP 认证、超时与 sendmail 路径，不真实发信。
"""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.email_sender import (
    send_password_reset_email,
    _send_via_smtp,
    _send_via_sendmail,
    _SENDMAIL_COMMUNICATE_TIMEOUT,
)


class TestSendViaSmtp:
    """_send_via_smtp 单元测试"""

    @pytest.mark.unit
    def test_smtp_auth_calls_starttls_and_login_when_credentials_set(self):
        """配置 SMTP_USER/SMTP_PASSWORD 时调用 starttls 与 login"""
        with patch("src.utils.email_sender.get_smtp_port", return_value=25):
            with patch("src.utils.email_sender.get_smtp_user", return_value="user@example.com"):
                with patch("src.utils.email_sender.get_smtp_password", return_value="secret"):
                    with patch("smtplib.SMTP") as mock_smtp_class:
                        mock_smtp = MagicMock()
                        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
                        mock_smtp.__exit__ = MagicMock(return_value=False)
                        mock_smtp_class.return_value = mock_smtp
                        msg = MagicMock()
                        msg.as_string.return_value = ""

                        _send_via_smtp(msg, "from@x.com", "to@x.com", "smtp.example.com")

                        mock_smtp.starttls.assert_called_once()
                        mock_smtp.login.assert_called_once_with("user@example.com", "secret")
                        mock_smtp.sendmail.assert_called_once()

    @pytest.mark.unit
    def test_smtp_socket_timeout_set_before_sendmail(self):
        """发信前对 sock 设置更长超时，与连接超时分离"""
        with patch("src.utils.email_sender.get_smtp_port", return_value=25):
            with patch("src.utils.email_sender.get_smtp_user", return_value=None):
                with patch("src.utils.email_sender.get_smtp_password", return_value=None):
                    with patch("smtplib.SMTP") as mock_smtp_class:
                        mock_sock = MagicMock()
                        mock_smtp = MagicMock()
                        mock_smtp.sock = mock_sock
                        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
                        mock_smtp.__exit__ = MagicMock(return_value=False)
                        mock_smtp_class.return_value = mock_smtp
                        msg = MagicMock()
                        msg.as_string.return_value = ""

                        _send_via_smtp(msg, "from@x.com", "to@x.com", "localhost")

                        mock_sock.settimeout.assert_called_once_with(30)

    @pytest.mark.unit
    def test_send_password_reset_email_calls_send_via_smtp_when_host_set(self):
        """配置 SMTP_HOST 时走 _send_via_smtp"""
        with patch("src.utils.email_sender.get_mail_from", return_value="noreply@example.com"):
            with patch("src.utils.email_sender.get_reset_link_expire_minutes", return_value=60):
                with patch("src.utils.email_sender.get_smtp_host", return_value="smtp.example.com"):
                    with patch("src.utils.email_sender._send_via_smtp") as mock_send:
                        send_password_reset_email(
                            to_email="u@x.com",
                            reset_link="https://example.com/reset?token=abc",
                            username="User",
                        )
                        mock_send.assert_called_once()
                        args = mock_send.call_args[0]
                        assert args[1] == "noreply@example.com"
                        assert args[2] == "u@x.com"
                        assert args[3] == "smtp.example.com"


class TestSendViaSendmail:
    """_send_via_sendmail 单元测试（含超时）"""

    @pytest.mark.unit
    def test_sendmail_communicate_called_with_timeout(self):
        """sendmail 子进程 communicate 带超时，避免无限阻塞"""
        msg = MagicMock()
        msg.as_bytes.return_value = b""
        with patch("src.utils.email_sender.subprocess.Popen") as mock_popen:
            proc = MagicMock()
            proc.communicate.return_value = (None, b"")
            proc.returncode = 0
            mock_popen.return_value = proc

            _send_via_sendmail(msg, "user@example.com")

            proc.communicate.assert_called_once()
            call_kw = proc.communicate.call_args[1]
            assert call_kw.get("timeout") == _SENDMAIL_COMMUNICATE_TIMEOUT

    @pytest.mark.unit
    def test_sendmail_timeout_expired_kills_and_raises(self):
        """sendmail 超时则 kill 进程并抛出 RuntimeError"""
        import subprocess
        msg = MagicMock()
        msg.as_bytes.return_value = b""
        with patch("src.utils.email_sender.subprocess.Popen") as mock_popen:
            proc = MagicMock()
            proc.communicate.side_effect = subprocess.TimeoutExpired("sendmail", 30)
            mock_popen.return_value = proc

            with pytest.raises(RuntimeError) as exc_info:
                _send_via_sendmail(msg, "user@example.com")
            assert "超时" in str(exc_info.value)
            proc.kill.assert_called_once()
            proc.wait.assert_called_once()
