
import os
import re
import logging
from typing import Optional

logger = logging.getLogger("S9Checker")


API_KEY_PATTERNS = [
    {
        "name": "AWS Access Key",
        "pattern": r"(?:^|[^A-Za-z0-9/+=])(AKIA[0-9A-Z]{16})(?:[^A-Za-z0-9/+=]|$)",
        "severity": "critical",
        "description": "Amazon Web Services access key",
    },
    {
        "name": "AWS Secret Key",
        "pattern": r"(?:aws_secret_access_key|secret_key)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
        "severity": "critical",
        "description": "Amazon Web Services secret key",
    },
    {
        "name": "Google API Key",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(AIza[0-9A-Za-z_-]{35})(?:[^A-Za-z0-9_-]|$)",
        "severity": "high",
        "description": "Google API key (Maps, YouTube, etc.)",
    },
    {
        "name": "Google OAuth Client ID",
        "pattern": r"(?:^|[0-9-])([0-9]{12}-[a-z0-9_]{32}\.apps\.googleusercontent\.com)(?:[\"'\s]|$)",
        "severity": "medium",
        "description": "Google OAuth client ID",
    },
    {
        "name": "Discord Bot Token",
        "pattern": r"(?:discord|bot)[-_]?token['\"]?\s*[:=]\s*['\"]?([MN][A-Za-z0-9_-]{23,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,})['\"]?",
        "severity": "critical",
        "description": "Discord bot token",
    },
    {
        "name": "Discord Webhook URL",
        "pattern": r"(https://(?:discord|ptb|canary)\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+)",
        "severity": "high",
        "description": "Discord webhook URL",
    },
    {
        "name": "GitHub Token",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})(?:[^A-Za-z0-9_-]|$)",
        "severity": "critical",
        "description": "GitHub personal access token",
    },
    {
        "name": "GitLab Token",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(glpat-[A-Za-z0-9_-]{20,})(?:[^A-Za-z0-9_-]|$)",
        "severity": "critical",
        "description": "GitLab personal access token",
    },
    {
        "name": "Slack Bot Token",
        "pattern": r"(?:xoxb-[0-9]{10,}-[A-Za-z0-9]{24,})",
        "severity": "high",
        "description": "Slack bot token",
    },
    {
        "name": "Slack User Token",
        "pattern": r"(?:xoxp-[0-9]{10,}-[0-9]{10,}-[0-9]{10,}-[a-z0-9]{32})",
        "severity": "high",
        "description": "Slack user token",
    },
    {
        "name": "Slack Webhook URL",
        "pattern": r"(https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+)",
        "severity": "medium",
        "description": "Slack incoming webhook URL",
    },
    {
        "name": "Stripe API Key",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(sk_live_[0-9a-zA-Z]{24,}|pk_live_[0-9a-zA-Z]{24,}|rk_live_[0-9a-zA-Z]{24,})(?:[^A-Za-z0-9_-]|$)",
        "severity": "critical",
        "description": "Stripe live API key",
    },
    {
        "name": "Stripe Test Key",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(sk_test_[0-9a-zA-Z]{24,})(?:[^A-Za-z0-9_-]|$)",
        "severity": "low",
        "description": "Stripe test API key",
    },
    {
        "name": "Telegram Bot Token",
        "pattern": r"(?:telegram|bot)[-_]?token['\"]?\s*[:=]\s*['\"]?([0-9]{8,10}:[A-Za-z0-9_-]{35})['\"]?",
        "severity": "high",
        "description": "Telegram bot token",
    },
    {
        "name": "SendGrid API Key",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43})(?:[^A-Za-z0-9_-]|$)",
        "severity": "critical",
        "description": "SendGrid API key",
    },
    {
        "name": "Twilio API Key",
        "pattern": r"(?:twilio|twil)[-_]?api[_-]?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9]{32})['\"]?",
        "severity": "high",
        "description": "Twilio API key",
    },
    {
        "name": "Heroku API Key",
        "pattern": r"(?:heroku)[-_]?api[_-]?key['\"]?\s*[:=]\s*['\"]?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})['\"]?",
        "severity": "high",
        "description": "Heroku API key",
    },
    {
        "name": "Mailgun API Key",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(key-[0-9a-zA-Z]{32})(?:[^A-Za-z0-9_-]|$)",
        "severity": "high",
        "description": "Mailgun API key",
    },
    {
        "name": "NPM Token",
        "pattern": r"(?:npm[_-]?token|NPM_TOKEN)['\"]?\s*[:=]\s*['\"]?(npm_[A-Za-z0-9]{36})['\"]?",
        "severity": "high",
        "description": "NPM access token",
    },
    {
        "name": "PyPI Token",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(pypi-[A-Za-z0-9_-]{160,})(?:[^A-Za-z0-9_-]|$)",
        "severity": "high",
        "description": "PyPI API token",
    },
    {
        "name": "OpenAI API Key",
        "pattern": r"(?:^|[^A-Za-z0-9_-])(sk-[A-Za-z0-9]{48})(?:[^A-Za-z0-9_-]|$)",
        "severity": "critical",
        "description": "OpenAI API key",
    },
    {
        "name": "Alibaba Cloud Key",
        "pattern": r"(?:ALIBABA|alicloud)[-_]?access[_-]?key['\"]?\s*[:=]\s*['\"]?(LTAI[A-Za-z0-9]{12,20})['\"]?",
        "severity": "high",
        "description": "Alibaba Cloud access key",
    },
    {
        "name": "Sentry DSN",
        "pattern": r"(https://[a-f0-9]{32}@[a-z0-9.-]+/[0-9]+)",
        "severity": "medium",
        "description": "Sentry DSN (may contain embedded token)",
    },
    {
        "name": "Shopify Token",
        "pattern": r"(?:shpat|shppa|shpss|shpca)_[a-fA-F0-9]{32}",
        "severity": "high",
        "description": "Shopify access token",
    },
    {
        "name": "MySQL Connection String",
        "pattern": r"mysql://[^:]+:[^@]+@[^/\s]+/[^\s]+",
        "severity": "critical",
        "description": "MySQL connection string with credentials",
    },
    {
        "name": "PostgreSQL Connection String",
        "pattern": r"postgres(?:ql)?://[^:]+:[^@]+@[^/\s]+/[^\s]+",
        "severity": "critical",
        "description": "PostgreSQL connection string with credentials",
    },
    {
        "name": "MongoDB Connection String",
        "pattern": r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^/\s]+/[^\s]+",
        "severity": "critical",
        "description": "MongoDB connection string with credentials",
    },
    {
        "name": "Redis Connection String",
        "pattern": r"redis://[^:]+:[^@]+@[^/\s]+",
        "severity": "high",
        "description": "Redis connection string with credentials",
    },
    {
        "name": "Generic API Key",
        "pattern": r"(?:api[_-]?key|apikey|api[_-]?secret)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_-]{32,64})['\"]?",
        "severity": "medium",
        "description": "Generic API key pattern",
    },
    {
        "name": "Private Key Block",
        "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "severity": "critical",
        "description": "Cryptographic private key",
    },
    {
        "name": "JWT Token",
        "pattern": r"(?:^|[^A-Za-z0-9._-])(eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})(?:[^A-Za-z0-9._-]|$)",
        "severity": "medium",
        "description": "JSON Web Token (may contain sensitive claims)",
    },
]

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".ttf", ".otf", ".woff", ".woff2",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
}

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_LINE_LENGTH = 10000


class APIKeyScanner:

    def __init__(self):
        self._compiled = [(p["name"], re.compile(p["pattern"], re.IGNORECASE),
                           p["severity"], p["description"])
                          for p in API_KEY_PATTERNS]

    def scan_file(self, filepath: str) -> list[dict]:
        if not os.path.isfile(filepath):
            return []

        ext = os.path.splitext(filepath)[1].lower()
        if ext in IGNORED_EXTENSIONS:
            return []

        try:
            size = os.path.getsize(filepath)
            if size > MAX_FILE_SIZE:
                logger.warning(f"Skipping {filepath}: {size} bytes exceeds limit")
                return []
        except OSError:
            return []

        findings = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if len(line) > MAX_LINE_LENGTH:
                        continue
                    for name, pattern, severity, description in self._compiled:
                        matches = pattern.finditer(line)
                        for match in matches:
                            value = match.group(1) if match.lastindex else match.group(0)
                            findings.append({
                                "file": filepath,
                                "line": line_num,
                                "name": name,
                                "severity": severity,
                                "description": description,
                                "value": value[:60] + "..." if len(value) > 60 else value,
                                "context": line.strip()[:120],
                            })
        except (OSError, UnicodeDecodeError):
            pass

        return findings

    def scan_directory(self, directory: str, recursive: bool = True) -> list[dict]:
        all_findings = []
        scanned = 0

        for root, dirs, files in os.walk(directory):
            dirs[:] = [
                d for d in dirs
                if d not in {".git", ".svn", "__pycache__", "node_modules",
                             ".venv", "venv", ".env", "dist", "build"}
            ]

            for filename in files:
                filepath = os.path.join(root, filename)
                findings = self.scan_file(filepath)
                all_findings.extend(findings)
                scanned += 1

            if not recursive:
                break

        logger.info(f"Scanned {scanned} files, found {len(all_findings)} potential leaks")
        return all_findings

    def scan_text(self, text: str, source: str = "<input>") -> list[dict]:
        findings = []
        for line_num, line in enumerate(text.split("\n"), 1):
            for name, pattern, severity, description in self._compiled:
                matches = pattern.finditer(line)
                for match in matches:
                    value = match.group(1) if match.lastindex else match.group(0)
                    findings.append({
                        "file": source,
                        "line": line_num,
                        "name": name,
                        "severity": severity,
                        "description": description,
                        "value": value[:60] + "..." if len(value) > 60 else value,
                        "context": line.strip()[:120],
                    })
        return findings
