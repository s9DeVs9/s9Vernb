
import asyncio
import aiohttp
import logging
import re
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger("S9Checker")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SCAN_LEVELS = {
    "quick": {
        "name": "Quick",
        "description": "Minimal requests - robots.txt, sitemap, headers",
        "checks": ["robots", "sitemap", "headers"],
    },
    "minimal": {
        "name": "Minimal",
        "description": "Quick + common sensitive files + admin panels",
        "checks": ["robots", "sitemap", "headers", "sensitive", "admin"],
    },
    "hard": {
        "name": "Hard",
        "description": "Full scan - all checks + backup files + configs",
        "checks": ["robots", "sitemap", "headers", "sensitive", "admin", "backup", "configs", "dirs"],
    },
    "long": {
        "name": "Long",
        "description": "Deep scan - everything + DB dumps + exhaustive path check",
        "checks": ["robots", "sitemap", "headers", "sensitive", "admin", "backup", "configs", "dirs", "databases", "exhaustive"],
    },
}

SENSITIVE_FILES = [
    ("/.env", "critical", "Environment config - may contain secrets"),
    ("/.env.local", "critical", "Local environment config"),
    ("/.env.production", "critical", "Production environment config"),
    ("/.git/config", "critical", "Git config - may expose repo URL and credentials"),
    ("/.git/HEAD", "high", "Git HEAD reference"),
    ("/.gitignore", "low", "Git ignore file"),
    ("/.htaccess", "high", "Apache config file"),
    ("/.htpasswd", "critical", "Apache password file"),
    ("/.DS_Store", "medium", "macOS directory metadata"),
    ("/web.config", "medium", "IIS configuration file"),
    ("/composer.json", "medium", "PHP dependencies"),
    ("/composer.lock", "medium", "PHP dependency lock file"),
    ("/package.json", "medium", "Node.js dependencies"),
    ("/package-lock.json", "low", "Node.js dependency lock"),
    ("/yarn.lock", "low", "Yarn lock file"),
    ("/Gemfile", "medium", "Ruby dependencies"),
    ("/requirements.txt", "medium", "Python dependencies"),
    ("/Dockerfile", "medium", "Docker config"),
    ("/docker-compose.yml", "medium", "Docker Compose config"),
    ("/.dockerenv", "high", "Docker environment indicator"),
    ("/server-status", "high", "Apache server status"),
    ("/server-info", "high", "Apache server info"),
    ("/phpinfo.php", "high", "PHP info page"),
    ("/info.php", "high", "PHP info page"),
    ("/test.php", "medium", "Test PHP file"),
    ("/debug", "medium", "Debug endpoint"),
    ("/trace.axd", "high", "ASP.NET trace"),
    ("/elmah.axd", "high", "ASP.NET error log"),
    ("/.svn/entries", "high", "SVN metadata"),
    ("/.svn/wc.db", "critical", "SVN working copy DB"),
    ("/.bzr/README", "medium", "Bazaar VCS metadata"),
    ("/.hg/dirstate", "medium", "Mercurial VCS metadata"),
    ("/crossdomain.xml", "low", "Flash cross-domain policy"),
    ("/clientaccesspolicy.xml", "low", "Silverlight cross-domain policy"),
    ("/favicon.ico", "low", "Favicon"),
    ("/readme.html", "low", "Readme file"),
    ("/README.md", "low", "README file"),
    ("/LICENSE", "low", "License file"),
    ("/CHANGES", "low", "Changelog"),
    ("/robots.txt", "low", "Robots file"),
    ("/sitemap.xml", "low", "Sitemap"),
    ("/wp-config.php.bak", "critical", "WordPress config backup"),
    ("/config.php.bak", "critical", "Config backup"),
    ("/database.sql", "critical", "SQL database dump"),
    ("/dump.sql", "critical", "SQL database dump"),
    ("/backup.sql", "critical", "SQL database dump"),
    ("/db.sql", "critical", "SQL database dump"),
    ("/.bash_history", "critical", "Bash history"),
    ("/.ssh/id_rsa", "critical", "SSH private key"),
    ("/.ssh/authorized_keys", "high", "SSH authorized keys"),
    ("/id_rsa", "critical", "SSH private key"),
    ("/.aws/credentials", "critical", "AWS credentials"),
    ("/.aws/config", "high", "AWS config"),
    ("/.npmrc", "medium", "NPM config"),
    ("/.env.bak", "critical", "Environment config backup"),
    ("/config.yml.bak", "critical", "Config backup"),
    ("/database.yml.bak", "critical", "Database config backup"),
]

ADMIN_PANELS = [
    ("/wp-admin/", "WordPress Admin"),
    ("/wp-admin/index.php", "WordPress Admin Login"),
    ("/administrator/", "Joomla Admin"),
    ("/administrator/index.php", "Joomla Admin Login"),
    ("/admin/", "Generic Admin"),
    ("/admin/login", "Generic Admin Login"),
    ("/user/login", "Drupal Login"),
    ("/admin/content", "Drupal Admin"),
    ("/cpanel", "cPanel"),
    ("/whm", "WHM"),
    ("/phpmyadmin/", "phpMyAdmin"),
    ("/adminer.php", "Adminer DB Tool"),
    ("/adminer/", "Adminer DB Tool"),
    ("/pma/", "phpMyAdmin Alt"),
    ("/mysql/", "MySQL Admin"),
    ("/adminer.php?server=1&username=root", "Adminer Root Access"),
    ("/.well-known/", "Well-Known URI"),
    ("/server-status", "Apache Status"),
    ("/server-info", "Apache Info"),
    ("/nginx_status", "Nginx Status"),
    ("/phpinfo.php", "PHP Info"),
    ("/info.php", "PHP Info"),
    ("/debug/default/view", "Symfony Debug"),
    ("/_profiler/", "Symfony Profiler"),
    ("/_profiler/phpinfo", "Symfony PHPInfo"),
    ("/api/", "API Endpoint"),
    ("/graphql", "GraphQL Endpoint"),
    ("/swagger/", "Swagger UI"),
    ("/swagger-ui/", "Swagger UI"),
    ("/api-docs", "API Docs"),
    ("/debug/vars", "Debug Vars"),
    ("/actuator", "Spring Boot Actuator"),
    ("/actuator/health", "Spring Boot Health"),
    ("/actuator/env", "Spring Boot Env (Critical)"),
]

BACKUP_PATTERNS = [
    ("/backup.zip", "critical", "Backup archive"),
    ("/backup.tar.gz", "critical", "Backup archive"),
    ("/backup.sql.gz", "critical", "Compressed SQL backup"),
    ("/site.zip", "critical", "Site backup archive"),
    ("/site.tar.gz", "critical", "Site backup archive"),
    ("/www.zip", "critical", "Web root backup"),
    ("/www.tar.gz", "critical", "Web root backup"),
    ("/html.zip", "critical", "HTML backup"),
    ("/public_html.zip", "critical", "Public HTML backup"),
    ("/database.zip", "critical", "Database backup"),
    ("/db_backup.zip", "critical", "Database backup"),
    ("/data.sql", "critical", "SQL data dump"),
    ("/export.sql", "critical", "SQL export"),
    ("/dump.sql.gz", "critical", "Compressed SQL dump"),
    ("/mysql_backup.sql", "critical", "MySQL backup"),
    ("/wp-content.zip", "high", "WordPress content backup"),
    ("/wp-content/uploads/", "medium", "WordPress uploads dir"),
    ("/media/", "medium", "Media directory"),
    ("/old/", "medium", "Old files directory"),
    ("/backup/", "medium", "Backup directory"),
    ("/bak/", "medium", "Backup directory"),
    ("/temp/", "low", "Temp directory"),
    ("/tmp/", "low", "Temp directory"),
]

CONFIG_FILES = [
    ("/config.php", "critical", "PHP config - may contain DB credentials"),
    ("/config.php.bak", "critical", "PHP config backup"),
    ("/configuration.php", "critical", "Joomla config"),
    ("/wp-config.php", "critical", "WordPress config"),
    ("/wp-config.php.bak", "critical", "WordPress config backup"),
    ("/wp-config.php.old", "critical", "WordPress config old"),
    ("/settings.py", "critical", "Django settings"),
    ("/database.yml", "critical", "Rails database config"),
    ("/database.yml.bak", "critical", "Rails DB config backup"),
    ("/config.yml", "high", "YAML config"),
    ("/config.yml.bak", "critical", "YAML config backup"),
    ("/config.json", "high", "JSON config"),
    ("/.env", "critical", "Environment config"),
    ("/.env.local", "critical", "Local env config"),
    ("/.env.production", "critical", "Production env"),
    ("/.env.staging", "critical", "Staging env"),
    ("/.env.development", "high", "Dev env config"),
    ("/application.properties", "high", "Spring Boot config"),
    ("/application.yml", "high", "Spring Boot config"),
    ("/appsettings.json", "high", "ASP.NET config"),
    ("/web.config.bak", "critical", "IIS config backup"),
    ("/.config", "medium", "Generic config"),
    ("/config.ini", "high", "INI config"),
    ("/config.xml", "high", "XML config"),
    ("/db.php", "critical", "Database connection file"),
    ("/database.php", "critical", "Database file"),
    ("/conn.php", "critical", "Connection file"),
    ("/connect.php", "critical", "Connection file"),
    ("/connection.php", "critical", "Connection file"),
    ("/credentials.php", "critical", "Credentials file"),
    ("/secrets.php", "critical", "Secrets file"),
]

DIR_LIST_DIRS = [
    "/uploads/",
    "/images/",
    "/img/",
    "/css/",
    "/js/",
    "/assets/",
    "/static/",
    "/files/",
    "/documents/",
    "/downloads/",
    "/temp/",
    "/tmp/",
    "/backup/",
    "/data/",
    "/db/",
    "/sql/",
    "/logs/",
    "/log/",
    "/debug/",
    "/test/",
    "/tests/",
    "/old/",
    "/new/",
    "/dev/",
    "/staging/",
    "/archive/",
    "/exports/",
    "/imports/",
    "/media/",
    "/attachments/",
    "/public/",
    "/private/",
    "/secret/",
    "/hidden/",
    "/admin/",
    "/config/",
    "/inc/",
    "/include/",
    "/includes/",
    "/lib/",
    "/libs/",
    "/vendor/",
    "/node_modules/",
    "/.git/",
]

DB_DUMP_PATTERNS = [
    ("/*.sql", "SQL dump files"),
    ("/*.sql.gz", "Compressed SQL dumps"),
    ("/*.sql.bak", "SQL backup files"),
    ("/*.sqlite", "SQLite databases"),
    ("/*.sqlite3", "SQLite3 databases"),
    ("/*.db", "Database files"),
    ("/*.mdb", "Access databases"),
    ("/*.csv", "CSV data exports"),
    ("/*.xml", "XML data exports"),
    ("/*.json", "JSON data exports"),
    ("/*.dump", "Database dumps"),
    ("/*.bak.sql", "SQL backup files"),
]


class SiteRecon:

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout

    async def scan(self, url: str, level: str = "minimal") -> dict:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        if level not in SCAN_LEVELS:
            level = "minimal"

        checks = SCAN_LEVELS[level]["checks"]

        result = {
            "url": url,
            "scan_level": level,
            "scan_level_name": SCAN_LEVELS[level]["name"],
            "robots": {"found": False, "content": "", "disallowed": [], "sitemaps": []},
            "sitemap": {"found": False, "urls": [], "count": 0},
            "headers": {},
            "sensitive_files": [],
            "admin_panels": [],
            "backup_files": [],
            "config_files": [],
            "directory_listing": [],
            "database_exposure": [],
            "findings_count": 0,
            "error": "",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if "headers" in checks:
                    await self._check_headers(session, url, result)

                if "robots" in checks:
                    await self._check_robots(session, url, result)

                if "sitemap" in checks:
                    await self._check_sitemap(session, url, result)

                if "sensitive" in checks:
                    await self._check_files(session, url, SENSITIVE_FILES, "sensitive_files", result)

                if "admin" in checks:
                    await self._check_admin_panels(session, url, result)

                if "backup" in checks:
                    await self._check_files(session, url, BACKUP_PATTERNS, "backup_files", result)

                if "configs" in checks:
                    await self._check_files(session, url, CONFIG_FILES, "config_files", result)

                if "dirs" in checks:
                    await self._check_directory_listing(session, url, result)

                if "databases" in checks:
                    await self._check_database_exposure(session, url, result)

                if "exhaustive" in checks:
                    await self._exhaustive_path_check(session, url, result)

                result["findings_count"] = (
                    len(result["sensitive_files"])
                    + len(result["admin_panels"])
                    + len(result["backup_files"])
                    + len(result["config_files"])
                    + len(result["directory_listing"])
                    + len(result["database_exposure"])
                )

        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)[:100]}"
        except asyncio.TimeoutError:
            result["error"] = "Request timed out"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)[:100]}"

        return result

    async def _check_headers(self, session: aiohttp.ClientSession, url: str, result: dict) -> None:
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with session.get(
                url, proxy=self.proxy, ssl=False,
                allow_redirects=True, timeout=timeout,
                headers={"User-Agent": USER_AGENT},
            ) as resp:
                result["headers"] = dict(resp.headers)
                result["status_code"] = resp.status
                result["final_url"] = str(resp.url)
        except Exception:
            pass

    async def _check_robots(self, session: aiohttp.ClientSession, url: str, result: dict) -> None:
        try:
            robots_url = urljoin(url, "/robots.txt")
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(
                robots_url, proxy=self.proxy, ssl=False,
                timeout=timeout, headers={"User-Agent": USER_AGENT},
            ) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    result["robots"]["found"] = True
                    result["robots"]["content"] = content[:5000]

                    for line in content.split("\n"):
                        line = line.strip()
                        if line.lower().startswith("disallow:"):
                            path = line.split(":", 1)[1].strip()
                            if path:
                                result["robots"]["disallowed"].append(path)
                        elif line.lower().startswith("sitemap:"):
                            sitemap = line.split(":", 1)[1].strip()
                            result["robots"]["sitemaps"].append(sitemap)
        except Exception:
            pass

    async def _check_sitemap(self, session: aiohttp.ClientSession, url: str, result: dict) -> None:
        sitemap_urls = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap.txt"]
        for sitemap_path in sitemap_urls:
            try:
                sitemap_url = urljoin(url, sitemap_path)
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(
                    sitemap_url, proxy=self.proxy, ssl=False,
                    timeout=timeout, headers={"User-Agent": USER_AGENT},
                ) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        urls = re.findall(r"<loc>(.*?)</loc>", content)
                        if urls:
                            result["sitemap"]["found"] = True
                            result["sitemap"]["urls"].extend(urls[:200])
                            result["sitemap"]["count"] = len(urls)
                            break
            except Exception:
                continue

    async def _check_files(self, session: aiohttp.ClientSession, base_url: str,
                           file_list: list, result_key: str, result: dict) -> None:
        semaphore = asyncio.Semaphore(10)

        async def check_one(file_entry):
            path, severity, description = file_entry
            async with semaphore:
                try:
                    test_url = urljoin(base_url, path)
                    timeout = aiohttp.ClientTimeout(total=8)
                    async with session.get(
                        test_url, proxy=self.proxy, ssl=False,
                        allow_redirects=False, timeout=timeout,
                        headers={"User-Agent": USER_AGENT},
                    ) as resp:
                        if resp.status in (200, 403):
                            content_preview = ""
                            if resp.status == 200:
                                try:
                                    body = await resp.text()
                                    content_preview = body[:200]
                                except Exception:
                                    pass
                            result[result_key].append({
                                "path": path,
                                "status": resp.status,
                                "severity": severity,
                                "description": description,
                                "content_preview": content_preview,
                            })
                except Exception:
                    pass

        await asyncio.gather(*[check_one(f) for f in file_list])

    async def _check_admin_panels(self, session: aiohttp.ClientSession, base_url: str, result: dict) -> None:
        semaphore = asyncio.Semaphore(10)

        async def check_one(panel):
            path, name = panel
            async with semaphore:
                try:
                    test_url = urljoin(base_url, path)
                    timeout = aiohttp.ClientTimeout(total=8)
                    async with session.get(
                        test_url, proxy=self.proxy, ssl=False,
                        allow_redirects=True, timeout=timeout,
                        headers={"User-Agent": USER_AGENT},
                    ) as resp:
                        if resp.status in (200, 403):
                            body = ""
                            if resp.status == 200:
                                try:
                                    body = (await resp.text())[:300]
                                except Exception:
                                    pass
                            severity = "high" if resp.status == 200 else "medium"
                            result["admin_panels"].append({
                                "path": path,
                                "name": name,
                                "status": resp.status,
                                "severity": severity,
                                "body_preview": body,
                            })
                except Exception:
                    pass

        await asyncio.gather(*[check_one(p) for p in ADMIN_PANELS])

    async def _check_directory_listing(self, session: aiohttp.ClientSession, base_url: str, result: dict) -> None:
        semaphore = asyncio.Semaphore(10)

        async def check_one(d):
            async with semaphore:
                try:
                    test_url = urljoin(base_url, d)
                    timeout = aiohttp.ClientTimeout(total=8)
                    async with session.get(
                        test_url, proxy=self.proxy, ssl=False,
                        allow_redirects=False, timeout=timeout,
                        headers={"User-Agent": USER_AGENT},
                    ) as resp:
                        if resp.status == 200:
                            body = (await resp.text())[:1000].lower()
                            listing_indicators = [
                                "index of", "<title>index of", "parent directory",
                                "directory listing", "[to parent directory]",
                                "last modified", "pre>", "directory of",
                            ]
                            if any(ind in body for ind in listing_indicators):
                                result["directory_listing"].append({
                                    "path": d,
                                    "severity": "high",
                                    "description": "Directory listing enabled",
                                })
                except Exception:
                    pass

        await asyncio.gather(*[check_one(d) for d in DIR_LIST_DIRS])

    async def _check_database_exposure(self, session: aiohttp.ClientSession, base_url: str, result: dict) -> None:
        db_paths = [
            ("/database.sql", "SQL database dump"),
            ("/dump.sql", "SQL dump"),
            ("/backup.sql", "SQL backup"),
            ("/db.sql", "SQL database"),
            ("/data.sql", "SQL data"),
            ("/export.sql", "SQL export"),
            ("/mysql.sql", "MySQL dump"),
            ("/db_backup.sql", "Database backup"),
            ("/database.sqlite", "SQLite database"),
            ("/database.db", "Database file"),
            ("/app.db", "Application database"),
            ("/data.db", "Data database"),
            ("/db.sqlite3", "SQLite3 database"),
            ("/storage/database.sqlite", "Laravel SQLite"),
            ("/var/database.sqlite", "SQLite database"),
        ]

        semaphore = asyncio.Semaphore(10)

        async def check_one(entry):
            path, description = entry
            async with semaphore:
                try:
                    test_url = urljoin(base_url, path)
                    timeout = aiohttp.ClientTimeout(total=8)
                    async with session.get(
                        test_url, proxy=self.proxy, ssl=False,
                        allow_redirects=False, timeout=timeout,
                        headers={"User-Agent": USER_AGENT},
                    ) as resp:
                        if resp.status == 200:
                            body = ""
                            try:
                                body = (await resp.text())[:300]
                            except Exception:
                                pass
                            is_db = False
                            body_lower = body.lower()
                            for indicator in ["create table", "insert into", "drop table",
                                              "sql", "database", "mysql", "postgresql"]:
                                if indicator in body_lower:
                                    is_db = True
                                    break
                            result["database_exposure"].append({
                                "path": path,
                                "status": resp.status,
                                "severity": "critical",
                                "description": description,
                                "is_confirmed": is_db,
                                "content_preview": body[:150],
                            })
                except Exception:
                    pass

        await asyncio.gather(*[check_one(e) for e in db_paths])

    async def _exhaustive_path_check(self, session: aiohttp.ClientSession, base_url: str, result: dict) -> None:
        extra_paths = [
            ("/cgi-bin/", "CGI directory"),
            ("/.bashrc", "Bash config"),
            ("/.profile", "User profile"),
            ("/.bash_history", "Bash history"),
            ("/etc/passwd", "System users (LFI)"),
            ("/proc/self/environ", "Process environment (LFI)"),
            ("/.idea/workspace.xml", "JetBrains IDE workspace"),
            ("/.vscode/settings.json", "VS Code settings"),
            ("/wp-config.php~", "WordPress config tilde backup"),
            ("/wp-config.php.save", "WordPress config save backup"),
            ("/wp-config.php.swp", "WordPress config swap file"),
            ("/config.php.save", "Config save backup"),
            ("/config.php.swp", "Config swap file"),
            ("/.user.ini", "PHP user ini"),
            ("/php.ini", "PHP config"),
            ("/.php.ini", "PHP hidden config"),
            ("/server.php", "Server info script"),
            ("/debug.php", "Debug script"),
            ("/test/", "Test directory"),
            ("/phpunit.xml", "PHPUnit config"),
            ("/.phpunit.result.cache", "PHPUnit cache"),
            ("/webpack.config.js", "Webpack config"),
            ("/.babelrc", "Babel config"),
            ("/tsconfig.json", "TypeScript config"),
            ("/Gruntfile.js", "Grunt config"),
            ("/gulpfile.js", "Gulp config"),
            ("/.editorconfig", "Editor config"),
            ("/.prettierrc", "Prettier config"),
            ("/.eslintrc", "ESLint config"),
            ("/Makefile", "Makefile"),
            ("/Vagrantfile", "Vagrant config"),
            ("/ansible.yml", "Ansible playbook"),
            ("/terraform.tf", "Terraform config"),
            ("/.circleci/config.yml", "CircleCI config"),
            ("/.github/workflows/", "GitHub Actions"),
            ("/.gitlab-ci.yml", "GitLab CI config"),
            ("/Jenkinsfile", "Jenkins pipeline"),
            ("/Vagrantfile", "Vagrant config"),
            ("/docker-compose.dev.yml", "Docker Compose dev"),
            ("/docker-compose.prod.yml", "Docker Compose prod"),
        ]

        semaphore = asyncio.Semaphore(10)

        async def check_one(entry):
            path, description = entry
            async with semaphore:
                try:
                    test_url = urljoin(base_url, path)
                    timeout = aiohttp.ClientTimeout(total=8)
                    async with session.get(
                        test_url, proxy=self.proxy, ssl=False,
                        allow_redirects=False, timeout=timeout,
                        headers={"User-Agent": USER_AGENT},
                    ) as resp:
                        if resp.status in (200, 403):
                            severity = "critical" if any(x in path for x in [
                                "passwd", "environ", "history", "ssh", "bash",
                                "config", "backup", "credentials", "secret",
                            ]) else "high" if resp.status == 200 else "medium"
                            result["sensitive_files"].append({
                                "path": path,
                                "status": resp.status,
                                "severity": severity,
                                "description": description,
                            })
                except Exception:
                    pass

        await asyncio.gather(*[check_one(e) for e in extra_paths])
