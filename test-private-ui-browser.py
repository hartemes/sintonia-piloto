#!/usr/bin/env python3
"""Real Chromium DOM regression with synthetic fixtures and fail-closed network routing.

No Supabase, credentials, or user data. Only the local HTTP fixture server is allowed;
all API calls are fulfilled from in-process synthetic data and every other request is aborted.
Requires: pip install playwright; playwright install chromium.
"""
from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from playwright.async_api import async_playwright, expect

HTML = Path(__file__).with_name("index.html").read_text()
PROJECT_HOST = "kttxqpbvzostizogbcba.supabase.co"


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        body = HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


async def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    discovery_started = asyncio.Event()
    release_discovery = asyncio.Event()
    visible = True
    blocked_requests: list[str] = []
    mocked_api_requests: list[str] = []
    revoked_tokens: list[str] = []
    fail_next_profile = False

    async def route_all(route):
        nonlocal visible, fail_next_profile
        request = route.request
        parsed = urlparse(request.url)
        if parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == server.server_port:
            await route.continue_()
            return
        if parsed.hostname != PROJECT_HOST:
            blocked_requests.append(request.url)
            await route.abort("blockedbyclient")
            return

        mocked_api_requests.append(request.url)
        cors = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-upsert",
        }
        if request.method == "OPTIONS":
            await route.fulfill(status=204, headers=cors, body="")
            return

        path = parsed.path
        if path == "/auth/v1/token" and request.method == "POST":
            body = {"access_token": "synthetic-issued-token", "user": {"id": "synthetic-login-user"}}
            await route.fulfill(status=200, headers=cors, content_type="application/json", body=json.dumps(body))
        elif path == "/auth/v1/logout" and request.method == "POST":
            revoked_tokens.append(request.headers.get("authorization", ""))
            await route.fulfill(status=204, headers=cors, body="")
        elif path.endswith("/rpc/sintonia_listar_descoberta"):
            discovery_started.set()
            await release_discovery.wait()
            body = [{"nome": "SYNTHETIC PRIVATE NAME", "idade": 33}]
            await route.fulfill(status=200, headers=cors, content_type="application/json", body=json.dumps(body))
        elif path.endswith("/rpc/sintonia_definir_visibilidade"):
            data = json.loads(request.post_data or "{}")
            visible = bool(data.get("p_aceito"))
            await route.fulfill(status=200, headers=cors, content_type="application/json", body="true")
        elif path.endswith("/rpc/sintonia_ler_minha_visibilidade"):
            await route.fulfill(status=200, headers=cors, content_type="application/json", body=json.dumps(visible))
        elif path.endswith("/rest/v1/sintonia_perfis"):
            if fail_next_profile and "select=nome_exibicao" in request.url:
                fail_next_profile = False
                await route.fulfill(status=500, headers=cors, content_type="application/json", body=json.dumps({"message": "synthetic profile failure"}))
            else:
                body = [{"usuario_id": "synthetic-user"}]
                await route.fulfill(status=200, headers=cors, content_type="application/json", body=json.dumps(body))
        elif path.startswith("/storage/v1/object/authenticated/"):
            await route.fulfill(status=404, headers=cors, body="synthetic missing photo")
        else:
            blocked_requests.append(request.url)
            await route.abort("blockedbyclient")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(service_workers="block")
            await context.route("**/*", route_all)
            page = await context.new_page()
            await page.goto(origin, wait_until="domcontentloaded")

            # Synthetic in-memory session only; no real auth request/account.
            await page.evaluate("async () => { session={user:'synthetic-user',token:'synthetic-token'}; view(); await refreshConsent(); }")
            await expect(page.get_by_role("button", name="Ver perfis disponíveis no piloto privado")).to_be_visible()
            await page.get_by_role("button", name="Ver perfis disponíveis no piloto privado").click()
            await asyncio.wait_for(discovery_started.wait(), timeout=5)
            await page.get_by_role("button", name="Retirar autorização e ocultar meu perfil").click()
            await expect(page.locator("#status")).to_contain_text("Autorização retirada", timeout=5000)
            async with page.expect_event("requestfinished", predicate=lambda req: "/rpc/sintonia_listar_descoberta" in req.url, timeout=5000):
                release_discovery.set()
            # Ensure the body and its application-level promise have settled before checking.
            await page.evaluate("() => new Promise(resolve => setTimeout(resolve, 0))")
            await expect(page.locator("#discoveryResults")).not_to_contain_text("SYNTHETIC PRIVATE NAME", timeout=5000)
            assert visible is False, "synthetic opt-out should update only the in-memory fixture"
            print("PASS — real Chromium DOM: deferred synthetic discovery response is discarded after opt-out")

            # A second, synthetic login: auth succeeds but profile setup fails. The UI must
            # discard private state and attempt to revoke the issued synthetic token.
            await page.locator("#consentState").evaluate("el => el.textContent='STALE PRIVATE CONSENT ON LOGOUT'")
            await page.locator("#logout").click()
            await expect(page.locator("#consentState")).to_have_text("")
            await expect(page.locator("#discoveryConsent")).to_be_hidden()
            print("PASS — real Chromium DOM: logout clears and hides private consent state")
            await page.locator("#email").fill("synthetic@example.test")
            await page.locator("#password").fill("synthetic-password")
            await page.locator("#name").evaluate("el => el.value = 'STALE PRIVATE NAME'")
            await page.locator("#consentState").evaluate("el => el.textContent='STALE PRIVATE CONSENT'")
            fail_next_profile = True
            await page.locator("#loginForm button[type=submit]").click()
            await expect(page.locator("#status")).to_contain_text("Não foi possível entrar", timeout=5000)
            await expect(page.locator("#profileSection")).to_be_hidden()
            assert await page.locator("#name").input_value() == "", "private form values must be cleared after post-auth profile failure"
            assert await page.locator("#consentState").text_content() == "", "private consent must be cleared"
            assert "Bearer synthetic-issued-token" in revoked_tokens, f"synthetic issued token was not revoked: {revoked_tokens}"
            print("PASS — real Chromium DOM: post-auth profile failure clears private UI and revokes synthetic token")

            assert not blocked_requests, f"unexpected/unknown network requests were blocked: {blocked_requests}"
            assert mocked_api_requests, "expected app API calls to be intercepted and synthetically fulfilled"
            print(f"PASS — all {len(mocked_api_requests)} app API request(s) were intercepted; zero outbound requests escaped")
            print("Scope: synthetic frontend regression only; no Supabase endpoint, database, credentials, or real account used.")
            await browser.close()
    finally:
        release_discovery.set()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    asyncio.run(main())
