#!/usr/bin/env python3
"""
检查汐汐的单词学习报告邮件
- 检查指定邮箱今天是否收到单词报告
- 退出码：0=找到报告，1=未找到，2=连接/配置错误
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import sys
import os
import re

# ============ 配置区 ============
# 邮箱配置（请修改这里）
IMAP_SERVER = "imap.qq.com"  # QQ 邮箱 IMAP 服务器
IMAP_PORT = 993  # IMAP SSL 端口
EMAIL_ACCOUNT = ""  # 你的邮箱账号
EMAIL_PASSWORD = ""  # 邮箱授权码（不是登录密码）

# 邮件识别规则
SEARCH_KEYWORDS = ["单词助手学习报告"]  # 邮件主题包含的关键词
SENDER_KEYWORDS = []  # 可选：发件人关键词，如 ["xxlearning"]
# ===============================


def decode_mime_words(s):
    """解码 MIME 编码的字符串"""
    if not s:
        return ""
    decoded = ""
    for word, encoding in decode_header(s):
        if isinstance(word, bytes):
            try:
                decoded += word.decode(encoding or 'utf-8', errors='ignore')
            except:
                decoded += word.decode('latin-1', errors='ignore')
        else:
            decoded += word
    return decoded


def parse_date_from_subject(subject):
    """
    从邮件标题解析日期
    格式示例："单词助手学习报告：智能复习 - 2026-02-26 22:51"
    返回：datetime 对象或 None
    """
    # 匹配 YYYY-MM-DD 格式
    match = re.search(r'(\d{4}-\d{2}-\d{2})', subject)
    if match:
        try:
            date_str = match.group(1)
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            pass
    return None


def check_email_connection():
    """测试邮箱连接"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.logout()
        return True, "连接成功"
    except imaplib.IMAP4.error as e:
        return False, f"IMAP 登录失败：{str(e)}"
    except Exception as e:
        return False, f"连接异常：{str(e)}"


def search_today_emails():
    """搜索单词报告邮件，检查是否是今天的"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("INBOX")
        
        # 搜索所有未读邮件（或者最近 7 天的邮件）
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != "OK":
            mail.logout()
            return False, "搜索邮件失败"
        
        email_ids = messages[0].split()
        if not email_ids:
            mail.logout()
            return False, "没有未读邮件"
        
        today = datetime.now().date()
        
        # 遍历未读邮件
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # 解码主题
                    subject = decode_mime_words(msg.get("Subject", ""))
                    
                    # 解码发件人
                    from_ = decode_mime_words(msg.get("From", ""))
                    
                    # 检查是否匹配关键词
                    matched = False
                    
                    # 检查主题
                    for keyword in SEARCH_KEYWORDS:
                        if keyword.lower() in subject.lower():
                            matched = True
                            break
                    
                    # 检查发件人（如果配置了）
                    if SENDER_KEYWORDS and not matched:
                        for keyword in SENDER_KEYWORDS:
                            if keyword.lower() in from_.lower():
                                matched = True
                                break
                    
                    if matched:
                        # 解析标题中的日期
                        report_date = parse_date_from_subject(subject)
                        
                        if report_date:
                            if report_date.date() == today:
                                mail.logout()
                                return True, f"找到今日单词报告：{subject}"
                            else:
                                # 找到报告但不是今天的
                                mail.logout()
                                return False, f"找到单词报告但不是今日（报告日期：{report_date.date()}）"
                        else:
                            # 无法解析日期，默认认为是最近的报告
                            mail.logout()
                            return True, f"找到单词报告（无法解析日期）：{subject}"
        
        mail.logout()
        return False, "没有找到单词报告邮件"
        
    except imaplib.IMAP4.error as e:
        return False, f"IMAP 错误：{str(e)}"
    except Exception as e:
        return False, f"搜索异常：{str(e)}"


def main():
    # 检查配置
    if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
        print("错误：请先配置邮箱账号和密码", file=sys.stderr)
        sys.exit(2)
    
    # 先测试连接
    connected, conn_msg = check_email_connection()
    if not connected:
        print(f"连接失败：{conn_msg}", file=sys.stderr)
        sys.exit(2)
    
    # 搜索邮件
    found, msg = search_today_emails()
    
    if found:
        print(f"✅ {msg}")
        sys.exit(0)
    else:
        print(f"⚠️ {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
