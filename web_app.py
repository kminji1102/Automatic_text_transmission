import argparse
import html
import json
import os
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

from config import COHORT_SENDER_MAP, LOG_DIR, SMS_MESSAGE
from sms_service import ServiceError, build_preview, send_selected_phones
from usage_logger import normalize_user_name, read_usage_events, write_usage_event

SESSION_COOKIE = "interview_sms_user"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
STATIC_FILES = {
    "/static/app.css": ("text/css; charset=utf-8", "app.css"),
    "/static/app.js": ("application/javascript; charset=utf-8", "app.js"),
}


class InterviewSmsHandler(BaseHTTPRequestHandler):
    server_version = "InterviewSmsWeb/1.0"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_text("ok")
            return
        if path in STATIC_FILES:
            self._send_static(path)
            return
        if path == "/":
            if self._current_user():
                self._redirect("/send")
            else:
                self._send_html(self._render_login())
            return
        if path == "/send":
            self._require_user(self._handle_preview)
            return
        if path == "/usage":
            self._require_user(self._handle_usage)
            return
        self._send_html(self._render_page("페이지 없음", _render_empty_state("요청한 페이지를 찾을 수 없습니다.")), 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        form = self._read_form()
        if path == "/login":
            self._handle_login(form)
            return
        if path == "/logout":
            self._clear_user()
            return
        if path == "/send":
            self._require_user(lambda user: self._handle_send(user, form))
            return
        self._send_html(self._render_page("페이지 없음", _render_empty_state("요청한 페이지를 찾을 수 없습니다.")), 404)

    def log_message(self, format: str, *args) -> None:
        return

    def _handle_login(self, form: dict[str, list[str]]) -> None:
        user_name = normalize_user_name(_first(form, "user_name"))
        if not user_name:
            self._send_html(self._render_login("사용자 이름을 입력해 주세요."), 400)
            return
        self.send_response(303)
        self.send_header("Location", "/send")
        self.send_header(
            "Set-Cookie",
            f"{SESSION_COOKIE}={quote(user_name)}; Path=/; HttpOnly; SameSite=Lax",
        )
        self.end_headers()

    def _handle_preview(self, user_name: str) -> None:
        try:
            preview = build_preview()
            detail = json.dumps(
                {
                    "total": len(preview["candidates"]),
                    "sendable": len(preview["send_candidates"]),
                    "prechecked": len(preview["prechecked_results"]),
                },
                ensure_ascii=False,
            )
            write_usage_event(user_name, "preview", "success", detail, self._client_ip())
        except Exception as exc:
            write_usage_event(user_name, "preview", "failed", str(exc), self._client_ip())
            self._send_html(self._render_error("미리보기 실패", exc, user_name), 500)
            return

        self._send_html(self._render_preview(user_name, preview))

    def _handle_send(self, user_name: str, form: dict[str, list[str]]) -> None:
        selected_phones = form.get("phone", [])
        message_text = _normalize_message(_first(form, "message"))
        if not selected_phones:
            write_usage_event(user_name, "send", "cancelled", "no recipients selected", self._client_ip())
            body = _render_empty_state(
                "선택된 발송 대상이 없습니다.",
                '<a class="button" href="/send">미리보기로 돌아가기</a>',
            )
            self._send_html(self._render_page("발송 취소", body, user_name))
            return
        if not message_text:
            write_usage_event(user_name, "send", "cancelled", "empty message", self._client_ip())
            body = _render_empty_state(
                "문자 내용을 입력해 주세요.",
                '<a class="button" href="/send">미리보기로 돌아가기</a>',
            )
            self._send_html(self._render_page("발송 취소", body, user_name), 400)
            return

        try:
            result = send_selected_phones(selected_phones, message_text)
            detail = json.dumps(
                {
                    "requested": result["requested_count"],
                    "sent": result["sent_count"],
                    "skipped": result["skipped_count"],
                    "summary": result["summary"],
                    "message_length": len(message_text),
                },
                ensure_ascii=False,
            )
            write_usage_event(user_name, "send", "success", detail, self._client_ip())
        except ServiceError as exc:
            write_usage_event(user_name, "send", "failed", str(exc), self._client_ip())
            self._send_html(self._render_error("발송 실패", exc, user_name), 500)
            return
        except Exception as exc:
            write_usage_event(user_name, "send", "failed", str(exc), self._client_ip())
            self._send_html(self._render_error("발송 실패", exc, user_name), 500)
            return

        self._send_html(self._render_send_result(user_name, result))

    def _handle_usage(self, user_name: str) -> None:
        events = read_usage_events(LOG_DIR, limit=100)
        self._send_html(self._render_usage(user_name, events))

    def _require_user(self, handler) -> None:
        user_name = self._current_user()
        if not user_name:
            self._redirect("/")
            return
        handler(user_name)

    def _current_user(self) -> str:
        raw_cookie = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie()
        try:
            jar.load(raw_cookie)
        except cookies.CookieError:
            return ""
        if SESSION_COOKIE not in jar:
            return ""
        return normalize_user_name(unquote(jar[SESSION_COOKIE].value))

    def _clear_user(self) -> None:
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
        self.end_headers()

    def _read_form(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8")
        return parse_qs(raw, keep_blank_values=True)

    def _client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
        return self.client_address[0] if self.client_address else ""

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def _send_text(self, text: str, status: int = 200) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, request_path: str) -> None:
        content_type, filename = STATIC_FILES[request_path]
        file_path = os.path.join(STATIC_DIR, filename)
        try:
            with open(file_path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self._send_text("not found", 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, content: str, status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _render_login(self, error: str = "") -> str:
        error_html = f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ""
        body = f"""
        <section class="login-shell">
          <div class="login-panel">
            <p class="eyebrow">Interview SMS</p>
            <h1>면접 안내 문자 발송</h1>
            <p class="subtle">오늘 인터뷰 예정자를 확인하고 체크된 대상에게 LMS를 발송합니다.</p>
            <form class="stack" method="post" action="/login">
              <label for="user_name">사용자 이름</label>
              <input id="user_name" name="user_name" maxlength="80" autocomplete="name" autofocus>
              {error_html}
              <button type="submit">시작하기</button>
            </form>
          </div>
        </section>
        """
        return self._render_page("로그인", body)

    def _render_preview(self, user_name: str, preview: dict) -> str:
        send_candidates = preview["send_candidates"]
        prechecked_results = preview["prechecked_results"]
        total_count = len(preview["candidates"])
        metrics = _render_metrics(
            [
                ("전체 예정자", total_count),
                ("발송 가능", len(send_candidates)),
                ("자동 제외", len(prechecked_results)),
            ]
        )

        if not preview["candidates"]:
            body = f"""
            {_render_page_toolbar("발송 미리보기", "노션 조회 결과", '<a class="button secondary" href="/usage">사용 이력</a>')}
            {metrics}
            {_render_empty_state("오늘 인터뷰 예정자가 없습니다.", '<a class="button" href="/send">새로고침</a>')}
            """
            return self._render_page("발송 미리보기", body, user_name)

        if send_candidates:
            candidate_rows = "".join(_render_candidate_row(candidate) for candidate in send_candidates)
            message_value = html.escape(SMS_MESSAGE)
            sendable_html = f"""
            <form class="send-form" method="post" action="/send" data-send-form>
              <section class="message-editor">
                <div class="section-heading">
                  <label for="sms_message">문자 내용</label>
                  <span class="muted"><strong data-message-count>{len(SMS_MESSAGE)}</strong>자</span>
                </div>
                <textarea id="sms_message" name="message" rows="10" data-message-editor required>{message_value}</textarea>
              </section>
              <section class="control-strip" aria-label="발송 대상 제어">
                <label class="search-field" for="recipient_search">
                  <span>검색</span>
                  <input id="recipient_search" type="search" placeholder="이름, 연락처, 기수" data-recipient-search>
                </label>
                <div class="control-actions">
                  <button class="button secondary" type="button" data-select-all>전체 선택</button>
                  <button class="button secondary" type="button" data-clear-selection>선택 해제</button>
                  <span class="selection-count"><strong data-selected-count>{len(send_candidates)}</strong>명 선택</span>
                </div>
              </section>
              <div class="table-wrap">
                <table class="data-table recipient-table" data-recipient-table>
                  <thead>
                    <tr>
                      <th>선택</th><th>이름</th><th>연락처</th><th>기수</th><th>매핑</th><th>발신번호</th>
                    </tr>
                  </thead>
                  <tbody>{candidate_rows}</tbody>
                </table>
              </div>
              <p class="table-empty" data-filter-empty hidden>검색 결과가 없습니다.</p>
              <p class="form-message" data-form-message role="status"></p>
              <div class="sticky-actions">
                <div class="sticky-summary">
                  <span class="muted">발송 준비</span>
                  <strong><span data-selected-count>{len(send_candidates)}</span>명</strong>
                </div>
                <div class="actions">
                  <a class="button secondary" href="/send">새로고침</a>
                  <button type="submit" data-submit-send>선택 대상 발송</button>
                </div>
              </div>
              <dialog class="confirm-dialog" data-confirm-dialog>
                <div class="dialog-body">
                  <h2>발송 전 확인</h2>
                  <p><strong data-confirm-count>{len(send_candidates)}</strong>명에게 LMS를 발송합니다.</p>
                  <p class="muted">위 문자 내용 그대로 전송됩니다.</p>
                  <div class="actions">
                    <button class="button secondary" type="button" data-close-confirm>취소</button>
                    <button type="button" data-confirm-submit>발송하기</button>
                  </div>
                </div>
              </dialog>
            </form>
            """
        else:
            sendable_html = _render_empty_state(
                "오늘 발송 가능한 대상이 없습니다.",
                '<a class="button" href="/send">새로고침</a>',
            )

        prechecked_html = ""
        if prechecked_results:
            prechecked_html = f"""
            <section class="section-block">
              <div class="section-heading">
                <h2>발송 제외 기록</h2>
                <span class="muted">{len(prechecked_results)}건</span>
              </div>
              <div class="table-wrap">
                <table class="data-table">
                  <thead><tr><th>이름</th><th>연락처</th><th>결과</th><th>사유</th></tr></thead>
                  <tbody>{''.join(_render_result_row(row) for row in prechecked_results)}</tbody>
                </table>
              </div>
            </section>
            """

        body = f"""
        {_render_page_toolbar("발송 미리보기", "노션 조회 결과", '<a class="button secondary" href="/usage">사용 이력</a>')}
        {metrics}
        {sendable_html}
        {prechecked_html}
        """
        return self._render_page("발송 미리보기", body, user_name)

    def _render_send_result(self, user_name: str, result: dict) -> str:
        summary_items = "".join(
            f"<div><span>{html.escape(str(key))}</span><strong>{count}건</strong></div>"
            for key, count in result["summary"].items()
        )
        if not summary_items:
            summary_items = "<div><span>결과</span><strong>0건</strong></div>"
        rows = "".join(_render_result_row(row) for row in result["all_results"])
        log_path = html.escape(result["log_path"] or "기록 없음")
        body = f"""
        {_render_page_toolbar("발송 결과", f'요청 {result["requested_count"]}명, 처리 {result["sent_count"]}명', '<a class="button secondary" href="/send">다시 미리보기</a>')}
        <section class="summary-grid">{summary_items}</section>
        <p class="muted">결과 CSV: {log_path}</p>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>이름</th><th>연락처</th><th>결과</th><th>사유</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """
        return self._render_page("발송 결과", body, user_name)

    def _render_usage(self, user_name: str, events: list[dict]) -> str:
        rows = "".join(
            "<tr>"
            f"<td>{html.escape(row.get('executed_at', ''))}</td>"
            f"<td>{html.escape(row.get('user_name', ''))}</td>"
            f"<td>{html.escape(row.get('client_ip', ''))}</td>"
            f"<td>{html.escape(row.get('action', ''))}</td>"
            f"<td>{_render_status_badge(row.get('result', ''))}</td>"
            f"<td><code>{html.escape(row.get('detail', ''))}</code></td>"
            "</tr>"
            for row in reversed(events)
        )
        if not rows:
            rows = '<tr><td colspan="6">사용 이력이 없습니다.</td></tr>'
        body = f"""
        {_render_page_toolbar("사용 이력", f"최근 {len(events)}건", '<a class="button secondary" href="/send">발송 화면</a>')}
        <div class="table-wrap">
          <table class="data-table usage-table">
            <thead><tr><th>시간</th><th>사용자</th><th>IP</th><th>동작</th><th>결과</th><th>상세</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """
        return self._render_page("사용 이력", body, user_name)

    def _render_error(self, title: str, exc: Exception, user_name: str = "") -> str:
        body = f"""
        {_render_page_toolbar(title, "처리 중 오류가 발생했습니다.", '<a class="button secondary" href="/send">발송 화면</a>')}
        <div class="alert error" role="alert">{html.escape(str(exc))}</div>
        """
        return self._render_page(title, body, user_name)

    def _render_page(self, title: str, body: str, user_name: str = "") -> str:
        nav = ""
        if user_name:
            nav = f"""
            <nav class="app-nav">
              <span>{html.escape(user_name)}</span>
              <form method="post" action="/logout"><button class="link-button" type="submit">나가기</button></form>
            </nav>
            """
        return f"""<!doctype html>
        <html lang="ko">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>{html.escape(title)} - Interview SMS</title>
          <link rel="stylesheet" href="/static/app.css">
          <script src="/static/app.js" defer></script>
        </head>
        <body>
          <header class="app-header">
            <a class="brand" href="/send"><span class="brand-mark">SMS</span><span>Interview SMS</span></a>
            {nav}
          </header>
          <main>{body}</main>
        </body>
        </html>"""


def _render_page_toolbar(title: str, subtitle: str = "", actions: str = "") -> str:
    subtitle_html = f'<p class="subtle">{html.escape(subtitle)}</p>' if subtitle else ""
    return f"""
    <div class="toolbar">
      <div>
        <h1>{html.escape(title)}</h1>
        {subtitle_html}
      </div>
      <div class="actions">{actions}</div>
    </div>
    """


def _render_metrics(items: list[tuple[str, int]]) -> str:
    return (
        '<section class="metric-grid">'
        + "".join(
            f"<div><span>{html.escape(label)}</span><strong>{value}</strong></div>"
            for label, value in items
        )
        + "</section>"
    )


def _render_empty_state(message: str, actions: str = "") -> str:
    actions_html = f'<div class="actions">{actions}</div>' if actions else ""
    return f"""
    <section class="empty-state">
      <p>{html.escape(message)}</p>
      {actions_html}
    </section>
    """


def _render_candidate_row(candidate: dict) -> str:
    phone = candidate.get("phone") or ""
    name = candidate.get("name", "")
    cohort = candidate.get("cohort", "")
    resolved_cohort = candidate.get("resolved_cohort") or ""
    sender = COHORT_SENDER_MAP.get(candidate.get("resolved_cohort"), "")
    search_text = " ".join([name, phone, cohort, resolved_cohort, sender]).lower()
    return (
        f'<tr data-recipient-row data-search="{html.escape(search_text)}" class="is-selected">'
        '<td class="select-cell">'
        f'<input type="checkbox" name="phone" value="{html.escape(phone)}" checked data-recipient-check '
        f'aria-label="{html.escape(name or phone)} 선택">'
        "</td>"
        f"<td><strong>{html.escape(name)}</strong></td>"
        f"<td>{html.escape(phone)}</td>"
        f"<td>{html.escape(cohort)}</td>"
        f'<td><span class="cohort-pill">{html.escape(resolved_cohort)}</span></td>'
        f"<td>{html.escape(sender)}</td>"
        "</tr>"
    )


def _render_result_row(row: dict) -> str:
    return (
        "<tr>"
        f"<td>{html.escape(row.get('name', ''))}</td>"
        f"<td>{html.escape(row.get('phone', ''))}</td>"
        f"<td>{_render_status_badge(row.get('result', ''))}</td>"
        f"<td>{html.escape(row.get('error_msg', ''))}</td>"
        "</tr>"
    )


def _render_status_badge(result: str) -> str:
    label = result or "기록"
    status_class = "neutral"
    if result == "성공" or result == "success":
        status_class = "success"
    elif "중복" in result or "건너" in result or result == "cancelled":
        status_class = "skip"
    elif result == "매핑없음" or "형식" in result:
        status_class = "warning"
    elif "실패" in result or result == "failed":
        status_class = "danger"
    return f'<span class="status-badge {status_class}">{html.escape(label)}</span>'


def _first(form: dict[str, list[str]], key: str) -> str:
    values = form.get(key) or [""]
    return values[0]


def _normalize_message(raw: str | None) -> str:
    return (raw or "").replace("\r\n", "\n").strip()


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), InterviewSmsHandler)
    print(f"Interview SMS web server: http://{host}:{port}")
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interview SMS web service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.host, args.port)
