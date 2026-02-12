"""
邮件发送工具

支持两种方式：
- SMTP：当配置 SMTP_HOST 或运行在 Docker 内（未配置时自动使用 localhost）时，连接该主机发信。
- sendmail 命令：非 Docker 且未配置 SMTP_HOST 时使用本机 sendmail 命令。
"""

import subprocess
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from src.config.app import get_mail_from, get_smtp_host, get_smtp_port, get_reset_link_expire_minutes

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_link: str, username: str) -> None:
    """
    发送密码重置邮件。

    Args:
        to_email: 收件人邮箱
        reset_link: 重置链接（完整 URL，如 https://bloggern.com/reset-password?token=xxx）
        username: 用户名（用于邮件正文称呼）

    Raises:
        RuntimeError: 当发送失败时
    """
    mail_from = get_mail_from()
    expire_minutes = get_reset_link_expire_minutes()
    subject = "Bloggern 密码重置"
    body = f"""您好，{username}：

您正在申请重置 Bloggern 账户密码。请点击以下链接设置新密码：

{reset_link}

该链接有效期为 {expire_minutes} 分钟，过期后需重新申请。

如果您没有申请重置密码，请忽略此邮件。

此邮件由系统自动发送，请勿直接回复。
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Bloggern", mail_from))
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    smtp_host = get_smtp_host()
    if smtp_host:
        _send_via_smtp(msg, mail_from, to_email, smtp_host)
    else:
        _send_via_sendmail(msg, to_email)


def _send_via_smtp(
    msg: MIMEMultipart, mail_from: str, to_email: str, smtp_host: str
) -> None:
    """通过 SMTP 连接宿主机 sendmail（如 Docker 内 SMTP_HOST=localhost）。"""
    port = get_smtp_port()
    try:
        with smtplib.SMTP(smtp_host, port, timeout=10) as smtp:
            smtp.sendmail(mail_from, [to_email], msg.as_string())
        logger.info("Password reset email sent to %s via SMTP %s:%s", to_email, smtp_host, port)
    except Exception as e:
        logger.exception("SMTP send failed to %s:%s: %s", smtp_host, port, e)
        raise RuntimeError(f"发送邮件失败: {e}") from e


def _send_via_sendmail(msg: MIMEMultipart, to_email: str) -> None:
    """通过本机 sendmail 命令发送。"""
    try:
        proc = subprocess.Popen(
            ["sendmail", "-t", "-oi"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        _, stderr = proc.communicate(input=msg.as_bytes())
        if proc.returncode != 0:
            err = (stderr or b"").decode("utf-8", errors="replace").strip()
            logger.error("sendmail failed: returncode=%s stderr=%s", proc.returncode, err)
            raise RuntimeError(f"发送邮件失败: {err or 'sendmail 返回非零'}")
        logger.info("Password reset email sent to %s", to_email)
    except FileNotFoundError:
        logger.error(
            "sendmail 命令不存在。本机部署请安装 sendmail；Docker 内一般会自动使用 SMTP 连宿主机，"
            "若仍报错请确认使用 host 网络或显式设置 SMTP_HOST=localhost。"
        )
        raise RuntimeError(
            "系统未安装 sendmail，无法发送邮件。"
            "若在 Docker 内运行，请确认使用 host 网络或显式设置 SMTP_HOST=localhost 后重启容器。"
        )
