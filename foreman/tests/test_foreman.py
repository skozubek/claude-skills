"""Testy kontraktu stanu foreman: create → kryteria → graf → front → dowody → decyzje →
hooki (stop-check, straz, bramka-floty.sh) → close/resume. Każdy strażnik ma kontrolę
czułości: znana zła komenda musi go zapalić. Uruchom: python3 -I -m unittest discover -s foreman/tests."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "foreman")
BRAMKA = os.path.join(os.path.dirname(BIN), "bramka-floty.sh")
SKROT = ("--force", "--note", "skrót testu: stan bez odbioru")

PLAN_OK = """# Eksport listy do CSV

Ścieżka użytkownika: handlowiec na liście rekordów klika „Eksport” i dostaje plik CSV z kolumnami jak na ekranie.

## Kryteria odbioru
- ekran listy po kliknięciu „Eksport” → pobrany plik `lista-<data>.csv`, nagłówek = kolumny widoczne na ekranie
- wiersz w tabeli `eksporty` po pobraniu → 1 nowy wiersz z liczbą rekordów równą licznikowi na ekranie
- czas od kliknięcia do pobrania, mierzony tym samym narzędziem i kontem → poniżej 3 s dla 500 rekordów

## Poza zakresem
- eksport XLSX, harmonogram eksportów

## Pojęcia
- brak nowych pojęć

## Granice
- Zakres: zadania i pliki z grafu; poza grafem nic.
- Dane: czytasz projekt dev, piszesz tylko na koncie testowym; po przelocie usuwasz wiersze `eksporty` konta testowego.
- Tożsamość obiektów po nazwie i miejscu, nie po ID; odbiór zastępczy, gdy brak.
- Koszt: budżet 20 USD, bez wywołań płatnych per obiekt.
- Kroki tylko-ludzkie: żadne.
"""


class Baza(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="f2test-")
        self.home = os.path.join(self.tmp, "home")
        self.repo = self.git_repo("repo")
        self.head = self.g("rev-parse", "HEAD")
        self.env = dict(os.environ, FOREMAN_HOME=self.home, CLAUDE_CONFIG_DIR=os.path.join(self.tmp, "claude"))
        self.env.pop("CLAUDE_SESSION_ID", None)
        self.env.pop("CLAUDE_CODE_SESSION_ID", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git_repo(self, nazwa):
        repo = os.path.join(self.tmp, nazwa)
        os.makedirs(repo)
        for a in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
            subprocess.run(["git", "-C", repo, *a], check=True, capture_output=True)
        with open(os.path.join(repo, "package.json"), "w") as f:
            json.dump({"name": nazwa, "scripts": {"test": "node --test", "lint": "eslint ."}}, f)
        subprocess.run(["git", "-C", repo, "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo, "commit", "-qm", "init"], check=True, capture_output=True)
        return repo

    def g(self, *a, repo=None):
        return subprocess.run(["git", "-C", repo or self.repo, *a], capture_output=True, text=True, check=True).stdout.strip()

    def f2(self, *a, stdin=None, ok=True, cwd=None, sesja=None):
        env = dict(self.env, CLAUDE_CODE_SESSION_ID=sesja) if sesja else self.env
        r = subprocess.run([sys.executable, "-I", BIN, *a], capture_output=True, text=True, cwd=cwd or self.repo, env=env, input=stdin)
        if ok and r.returncode:
            self.fail(f"foreman {' '.join(a)} → {r.returncode}: {r.stderr}")
        return r

    def czytaj(self, p):
        with open(p) as f:
            return f.read()

    def run_json(self):
        return json.loads(self.f2("status", "--json").stdout)

    def aktywny(self):
        return json.loads(self.czytaj(os.path.join(self.home, "active.json"))).get(os.path.realpath(self.repo))

    def nowy(self, *extra):
        rid = self.f2("create", "--slug", "Test przelotu", "--repo", self.repo, *extra).stdout.strip()
        self.f2("criteria", "add", "--text", "licznik rośnie", "--read", "GET /n", "--expected", "2")
        self.f2("task", "add", "--id", "T1", "--name", "typy", "--files", "a.ts", "--variant", "sonnet", "--verify", "npm test")
        self.f2("task", "add", "--id", "T2", "--name", "logika", "--files", "b.ts", "--deps", "T1")
        self.f2("task", "add", "--id", "T3", "--name", "ekran", "--files", "c.tsx", "--deps", "T1")
        self.f2("task", "add", "--id", "T4", "--name", "pomoc", "--files", "d.md", "--deps", "T2,T3")
        return rid

    def hook(self, tool, command=None, cwd=None, sesja=None, **extra):
        wej = {"tool_name": tool, "cwd": cwd or self.repo, "tool_input": {**({"command": command} if command is not None else {}), **extra}}
        if sesja:
            wej["session_id"] = sesja
        return self.f2("straz", stdin=json.dumps(wej)).stdout.strip()

    def integracja(self, sha=None):
        """Gałąź integracji przelotu z testów (`nowy()`) na wskazanym commicie."""
        self.g("branch", "-f", "integracja/test-przelotu", sha or self.head)


class TestPrzelot(Baza):
    def test_create_idempotentny_i_aktywny(self):
        a = self.f2("create", "--slug", "Mój przelot!", "--repo", self.repo).stdout.strip()
        b = self.f2("create", "--slug", "Mój przelot!", "--repo", self.repo).stdout.strip()
        self.assertEqual(a, b)
        self.assertTrue(a.endswith("-m-j-przelot"))
        self.assertEqual(self.aktywny(), a)
        d = self.run_json()
        self.assertEqual(d["base_sha"], self.head)
        self.assertEqual(d["state"], "planning")
        self.assertIn("foreman", d["sources"])

    def test_ten_sam_slug_inne_repo_dostaje_osobny_przelot(self):
        a = self.f2("create", "--slug", "x", "--repo", self.repo).stdout.strip()
        repo2 = self.git_repo("repo2")
        b = self.f2("create", "--slug", "x", "--repo", repo2, cwd=repo2).stdout.strip()
        self.assertNotEqual(a, b)
        self.assertTrue(b.startswith(a + "-"))
        self.assertEqual(json.loads(self.f2("status", "--json", cwd=repo2).stdout)["repo"], os.path.realpath(repo2))

    def test_worktree_wskazuje_glowny_klon(self):
        rid = self.nowy()
        wt = os.path.join(self.tmp, "wt")
        self.g("worktree", "add", "-q", "-b", "gal", wt)
        self.assertEqual(json.loads(self.f2("status", "--json", cwd=wt).stdout)["id"], rid, "cwd w worktree trafia w przelot głównego klonu")

    def test_front_zalezy_od_merge_i_miejsc(self):
        self.nowy()
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["ready"], ["T1"])
        self.f2("task", "set", "T1", "--status", "merged", "--spawn-sha", self.head, *SKROT)
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["ready"], ["T2", "T3"])
        r = self.f2("task", "set", "T2", "--status", "running", ok=False)
        self.assertIn("spawn-sha", r.stderr, "spawn bez SHA integracji odrzucony")
        self.f2("task", "set", "T2", "--status", "running", "--agent", "a1", "--spawn-sha", self.head)
        self.f2("task", "set", "T3", "--status", "running", "--agent", "a2", "--spawn-sha", self.head)
        self.f2("task", "add", "--id", "T5", "--name", "x", "--files", "e.ts")
        self.f2("task", "add", "--id", "T6", "--name", "y", "--files", "f.ts")
        self.f2("task", "set", "T5", "--status", "running", "--spawn-sha", self.head)
        r = self.f2("task", "set", "T6", "--status", "running", "--spawn-sha", self.head, ok=False)
        self.assertNotEqual(r.returncode, 0, "czwarty żywy agent przy max_live=3 ma zostać odrzucony")
        self.assertIn("brak wolnego miejsca", r.stderr)
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["free_slots"], 0)
        self.assertEqual(fr["spawn_now"], [])

    def test_zaleznosc_nieistniejaca_i_drugi_wlasciciel_odrzucone(self):
        self.nowy()
        r = self.f2("task", "add", "--name", "z", "--deps", "T99", ok=False)
        self.assertNotEqual(r.returncode, 0)
        r = self.f2("task", "add", "--name", "z", "--files", "a.ts", ok=False)
        self.assertIn("właściciela", r.stderr)
        self.f2("task", "set", "T1", "--status", "merged", *SKROT)
        self.assertEqual(self.f2("task", "add", "--name", "poprawki recenzji", "--files", "a.ts").stdout.strip(), "T5",
                         "plik zadania scalonego wolno dać nowemu zadaniu (runda poprawek)")

    def test_skrocony_sha_liczy_sie_jak_pelny(self):
        rid = self.nowy()
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged", *SKROT)
        e = self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head[:7], "--result", "2", "--verdict", "pass").stdout.strip()
        self.assertEqual(json.loads(self.f2("evidence", "show", e).stdout)["sha"], self.head, "skrócony SHA rozwinięty do pełnego")
        self.assertEqual(self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass").stdout.strip(), e, "ten sam pomiar bez powtórki")
        self.assertIn("każde kryterium", self.f2("evidence", "check", "--head", self.head[:8]).stdout)
        self.integracja()
        self.assertEqual(self.f2("--run", rid, "close", "--head", self.head[:7]).stdout.splitlines()[0], "done")

    def test_dowod_ustawia_kryterium_z_najnowszego_pomiaru(self):
        self.nowy()
        e = self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass").stdout.strip()
        self.assertEqual(e, "E1")
        d = self.run_json()
        self.assertEqual(d["criteria"][0]["status"], "pass")
        self.assertEqual(d["criteria"][0]["evidence"], ["E1"])
        e2 = self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass").stdout.strip()
        self.assertEqual(e2, "E1", "ten sam pomiar na tym samym SHA nie mnoży wpisów")
        self.assertEqual(self.f2("evidence", "check", "--head", self.head, ok=False).returncode, 0)
        r = self.f2("evidence", "check", "--head", "0" * 40, ok=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("E1 na", r.stdout)
        self.f2("evidence", "add", "--for", "C1", "--cmd", "oko", "--sha", self.head, "--verdict", "unverified")
        self.assertEqual(self.run_json()["criteria"][0]["status"], "pass", "unverified nie cofa pomiaru")
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "3", "--verdict", "fail")
        self.assertEqual(self.run_json()["criteria"][0]["status"], "fail", "najnowszy pomiar wygrywa")
        self.assertEqual(self.f2("evidence", "check", "--head", self.head, ok=False).returncode, 1)
        r = self.f2("criteria", "set", "C1", "--status", "pass", ok=False)
        self.assertNotEqual(r.returncode, 0, "status kryterium bez dowodu zakazany")

    def test_decyzja_approval_tylko_czlowiek_i_odmowa_blokuje(self):
        self.nowy()
        r = self.f2("decide", "ask", "--kind", "approval", "--question", "q", "--options", "tak | nie", "--rec", "nie", "--blocks", "T1", ok=False)
        self.assertIn("unblock-on", r.stderr, "blokada bez listy odblokowujących odpowiedzi odrzucona")
        did = self.f2("decide", "ask", "--kind", "approval", "--question", "Zapis do prod?", "--options", "tak | nie", "--rec", "nie", "--blocks", "T1", "--unblock-on", "tak").stdout.strip()
        self.assertEqual(did, "D1")
        self.assertEqual(json.loads(self.f2("frontier", "--json").stdout)["ready"], [], "decyzja pending blokuje zadanie na froncie")
        r = self.f2("decide", "answer", "D1", "rec", "--by", "agent:codex", ok=False)
        self.assertNotEqual(r.returncode, 0, "agent nie autoryzuje approval")
        r = self.f2("decide", "answer", "D1", "rec", "--by", "humanoid", ok=False)
        self.assertNotEqual(r.returncode, 0, "`human` to wzór, nie prefiks")
        r = self.f2("decide", "answer", "D1", "zupa", "--by", "human", ok=False)
        self.assertNotEqual(r.returncode, 0, "odpowiedź spoza opcji odrzucona")
        out = self.f2("decide", "answer", "D1", "rec", "--by", "human").stdout
        self.assertIn("zablokowane: T1", out)
        dec = [json.loads(l) for l in self.f2("decisions", "--json").stdout.splitlines()]
        self.assertEqual((dec[0]["status"], dec[0]["reply"]), ("approved", "nie"))
        t1 = next(t for t in self.run_json()["tasks"] if t["id"] == "T1")
        self.assertEqual(t1["status"], "blocked")
        self.assertIn("D1", t1["note"])
        r = self.f2("decide", "answer", "D1", "tak", "--by", "human")
        self.assertIn("już approved", r.stdout, "druga odpowiedź jest no-op")
        self.assertTrue(self.f2("close").stdout.startswith("blocked"))
        # zgoda odblokowuje, override zapisany
        self.f2("task", "add", "--id", "T7", "--name", "n", "--files", "g.ts")
        self.f2("decide", "ask", "--kind", "approval", "--question", "q2", "--options", "a | b", "--rec", "b", "--blocks", "T7", "--unblock-on", "a")
        self.f2("decide", "answer", "D2", "a", "--by", "human:serge")
        dec = [json.loads(l) for l in self.f2("decisions", "--json").stdout.splitlines()]
        self.assertEqual(dec[1]["status"], "overridden")
        self.assertIn("T7", json.loads(self.f2("frontier", "--json").stdout)["ready"])
        # auto: od razu auto_kept, agent może
        self.f2("decide", "ask", "--kind", "auto", "--question", "nazwa pola", "--options", "x | y", "--rec", "x")
        dec = [json.loads(l) for l in self.f2("decisions", "--json").stdout.splitlines()]
        self.assertEqual((dec[2]["status"], dec[2]["reply"]), ("auto_kept", "x"))

    def test_stop_check_blokuje_tylko_gdy_jest_robota(self):
        rid = self.nowy()
        wej = json.dumps({"cwd": self.repo, "background_tasks": [], "stop_hook_active": False})
        self.assertEqual(self.f2("stop-check", stdin=wej).stdout.strip(), "", "planning przepuszcza")
        self.f2("state", "running")
        out = json.loads(self.f2("stop-check", stdin=wej).stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("T1", out["reason"])
        r = self.f2("stop-check", stdin=json.dumps({"cwd": self.repo, "background_tasks": [{"id": "x"}], "stop_hook_active": True}))
        self.assertEqual(r.stdout.strip(), "", "tło pracuje: przepuszcza")
        self.assertEqual(json.loads(self.f2("stop-check", stdin=wej).stdout)["decision"], "block")
        self.assertEqual(self.f2("stop-check", stdin=wej).stdout.strip(), "", "po dwóch blokadach tego samego frontu przepuszcza")
        # zadania running bez agentów w tle → blokada (wznów albo odbierz)
        self.f2("task", "set", "T1", "--status", "running", "--agent", "a1", "--spawn-sha", self.head)
        out = json.loads(self.f2("stop-check", stdin=wej).stdout)
        self.assertIn("running/fixing", out["reason"])
        # wszystko merged, etap running bez close → blokada
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged", *SKROT)
        out = json.loads(self.f2("stop-check", stdin=wej).stdout)
        self.assertIn("close", out["reason"])
        self.f2("close")
        self.assertEqual(self.f2("stop-check", stdin=wej).stdout.strip(), "", "po close przepuszcza")
        # pending approval blokujące gotowe zadanie → nic do ruszenia bez człowieka → przepuszcza
        self.f2("--run", rid, "state", "running")
        self.f2("task", "add", "--id", "T7", "--name", "n", "--files", "g.ts")
        self.f2("decide", "ask", "--kind", "approval", "--question", "q", "--options", "a | b", "--rec", "a", "--blocks", "T7", "--unblock-on", "a")
        self.assertEqual(self.f2("stop-check", stdin=wej).stdout.strip(), "")
        self.assertEqual(self.f2("stop-check", stdin="nie json").returncode, 0, "śmieciowe stdin przepuszcza: strażnicy ruchu są w PreToolUse")
        log = self.czytaj(os.path.join(self.home, "runs", rid, "log.tsv"))
        self.assertIn("\tstop\tprzepuszczam\t", log, "każde wywołanie hooka zostawia ślad")

    def test_close_odmawia_done_bez_dowodu_i_trzyma_aktywny(self):
        rid = self.nowy()
        r = self.f2("close", "--state", "done", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("C1 bez dowodu", r.stderr)
        self.assertTrue(self.f2("close").stdout.startswith("partial"))
        self.assertEqual(self.aktywny(), rid, "zamknięty przelot zostaje aktywny: hooki widzą jego stan")
        nowy = self.f2("create", "--slug", "nastepny", "--repo", self.repo).stdout.strip()
        self.assertEqual(self.aktywny(), nowy)

    def test_close_done_tylko_z_dowodem_na_head(self):
        rid = self.nowy()
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged", *SKROT)
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass")
        self.f2("human", "add", "opublikuj front")
        self.integracja()
        self.assertTrue(self.f2("close", "--head", self.head).stdout.startswith("partial"), "otwarty krok ludzki = PARTIAL")
        self.f2("--run", rid, "human", "done", "H1")
        r = self.f2("--run", rid, "close", "--head", "1" * 40, ok=False)
        self.assertNotEqual(r.returncode, 0, "--head inny niż HEAD integracji odrzucony")
        self.assertIn("HEAD integracji", r.stderr)
        self.assertEqual(self.f2("--run", rid, "close", "--head", self.head).stdout.splitlines()[0], "done")
        self.assertEqual(json.loads(self.f2("--run", rid, "status", "--json").stdout)["verdict"]["state"], "done")

    def test_blokada_zadania_daje_blocked(self):
        self.nowy()
        self.f2("task", "set", "T1", "--status", "blocked", "--note", "brak klucza API")
        self.assertTrue(self.f2("close").stdout.startswith("blocked"))

    def test_own_i_resume_i_report(self):
        rid = self.nowy()
        self.f2("own", "add", "worktree", "/tmp/wt1")
        self.f2("own", "add", "cron", "cron-7")
        self.f2("own", "done", "/tmp/wt1")
        lst = self.f2("own", "list", "--open").stdout
        self.assertIn("cron-7", lst)
        self.assertNotIn("/tmp/wt1", lst)
        self.f2("task", "set", "T1", "--status", "running", "--agent", "ag-1", "--worktree", "/tmp/wt1", "--spawn-sha", self.head)
        r = self.f2("resume").stdout
        self.assertIn("ag-1", r)
        self.assertIn("front:", r)
        html = os.path.join(self.tmp, "r.html")
        self.f2("report", "--html", html)
        txt = self.czytaj(html)
        self.assertIn("licznik rośnie", txt)
        self.assertNotIn("<script", txt)
        self.assertIn("viewport", txt)
        log = self.czytaj(os.path.join(self.home, "runs", rid, "log.tsv")).splitlines()
        self.assertTrue(all(len(l.split("\t")) == 6 for l in log), "log.tsv ma 6 kolumn: ts faza decyzja powód dowód wynik")

    def test_cancel_zatrzymuje_robote(self):
        rid = self.nowy()
        self.f2("cancel", "--note", "zmiana zakresu")
        self.assertEqual(self.aktywny(), rid)
        self.assertEqual(self.run_json()["state"], "cancelled")
        self.assertNotEqual(self.f2("state", "running", ok=False).returncode, 0)
        r = self.f2("task", "set", "T1", "--status", "running", "--spawn-sha", self.head, ok=False)
        self.assertIn("anulowany", r.stderr)
        self.assertIn("anulowany", self.hook("Agent"), "spawn po cancel odmówiony")
        self.assertIn("deny", self.hook("Bash", "git push origin x"), "push po cancel odmówiony przez bramkę floty")
        self.assertEqual(self.hook("Bash", "git status"), "", "odczyt po cancel wolny")

    ODPOWIEDZI_CZLOWIEKA = ("foreman decide answer D1 rec --by human", "python3 -I /x/bin/foreman --run r decide answer D1 tak --by=human:serge",
                            "cd /tmp && $FM decide answer D1 rec --by 'human'")

    def test_straz_odmawia_odpowiedzi_jako_czlowiek_bez_nadzoru_i_zapisu_stanu(self):
        self.nowy("--unattended")
        self.f2("state", "running")
        for cmd in self.ODPOWIEDZI_CZLOWIEKA + ("echo '{}' >> ~/.foreman/runs/r/decisions.jsonl",
                    "sed -i '' 's/pending/approved/' /h/runs/r/decisions.jsonl", "python3 -c 'open(\"run.json\",\"w\")'"):
            self.assertIn('"deny"', self.hook("Bash", cmd), cmd)
        for cmd in ("foreman decide answer D1 rec --by codex", "foreman decide ask --kind approval --question q --options 'a | b' --rec a",
                    "cat ~/.foreman/runs/r/decisions.jsonl", "jq . run.json", "git push origin integracja", "npm test"):
            self.assertEqual(self.hook("Bash", cmd), "", cmd)
        self.assertEqual(self.hook("Agent"), "", "spawn w żywym przelocie wolny")
        self.assertIn('"deny"', self.hook("Bash", None), "komenda nieczytelna = odmowa")
        self.assertEqual(self.f2("straz", stdin="nie json").stdout.strip(), "", "śmieciowe stdin bez narzędzia przepuszcza")

    def test_straz_bez_nadzoru_nie_da_sie_obejsc_innym_przelotem_ani_edytorem(self):
        u = self.nowy("--unattended")
        self.f2("state", "running")
        for cmd in ("foreman create --slug inny --repo .", "$FM create --slug 'Test przelotu' --repo . --force"):
            self.assertIn('"deny"', self.hook("Bash", cmd), cmd)
        self.assertIn('"deny"', self.hook("Write", file_path=os.path.join(self.home, "runs", u, "run.json")), "Write w run.json odmówiony")
        self.assertIn('"deny"', self.hook("Edit", file_path=os.path.join(self.home, "profiles", "x.json")), "Edit profilu odmówiony")
        self.assertEqual(self.hook("Write", file_path=os.path.join(self.repo, "a.ts")), "", "Write w repo wolny")
        drugi = self.git_repo("drugi")
        s = self.f2("create", "--slug", "Nadzorowany", "--repo", drugi, cwd=drugi).stdout.strip()
        self.assertIn('"deny"', self.hook("Bash", f"foreman --run {u} decide answer D1 rec --by human:serge", cwd=drugi), "cel --run bez nadzoru odmówiony mimo nadzorowanego aktywnego")
        self.assertEqual(self.hook("Bash", f"foreman --run {s} decide answer D1 rec --by human:serge", cwd=drugi), "", "nadzorowany cel z nadzorowanego cwd wolny")
        self.f2("close", "--note", "koniec", ok=False)
        self.f2("cancel", "--note", "stop")
        self.assertEqual(self.hook("Bash", "foreman create --slug nowy --repo ."), "", "po zakończeniu przelotu bez nadzoru create wolny")

    def test_straz_pod_nadzorem_przepuszcza_odpowiedz_z_czatu(self):
        self.nowy()
        self.f2("state", "running")
        for cmd in self.ODPOWIEDZI_CZLOWIEKA + ("foreman create --slug inny --repo .",):
            self.assertEqual(self.hook("Bash", cmd), "", cmd)
        self.assertIn('"deny"', self.hook("Bash", "echo '{}' >> ~/.foreman/runs/r/decisions.jsonl"), "zapis stanu nadal odmówiony")
        did = self.f2("decide", "ask", "--kind", "approval", "--question", "czytać prod?", "--options", "tak | nie", "--rec", "nie").stdout.strip()
        self.assertIn("approval", self.f2("decide", "answer", did, "rec", "--by", "codex", ok=False).stderr, "agent nie autoryzuje także pod nadzorem")
        self.f2("decide", "answer", did, "rec", "--by", "human:serge")
        self.assertEqual([x for x in self.f2("decisions", "--json").stdout.splitlines() if did in x and "approved" in x] != [], True)

    @unittest.skipUnless(shutil.which("jq"), "bramka-floty.sh wymaga jq")
    def test_bramka_floty_czulosc(self):
        def bramka(cmd):
            wej = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
            return subprocess.run(["bash", BRAMKA], input=wej, capture_output=True, text=True).stdout
        zle = ["git push origin x", "git --no-pager push", "git -C /r push --force", "cd x && git push", "gh pr create --fill",
               "gh pr merge 5", "gh pr review --approve", "gh api -X POST repos/o/r/issues", "gh workflow run ci.yml",
               "npm run deploy", "pnpm publish", "bun run release:prod", "npx supabase db push", "npx -y supabase functions deploy f",
               "vercel --prod", "vercel", "netlify deploy", "kill -9 123", "pkill -f node", "claude -p 'x'", "codex exec 'x'",
               "psql postgresql://u:p@db.abc.supabase.co:5432/postgres -c 'delete from x'", "psql -h db.example.com -U u",
               "curl -X POST https://api.example.com/send -d '{}'", "curl https://hooks.example.com/x --json '{}'",
               "FOO=1 sudo git push", "/usr/bin/git push"]
        for cmd in zle:
            self.assertIn('"deny"', bramka(cmd), cmd)
        dobre = ["git status", "git log --oneline -3", "git fetch origin", "git merge --ff-only abc", "gh pr view 5", "gh api repos/o/r/pulls/5",
                 "gh run list --commit abc", "npm test", "npm run verify", "npm run build", "npx supabase gen types", "vercel env ls",
                 "psql postgresql://localhost/db -c 'select 1'", "psql -h localhost -U u db", "curl -X POST http://localhost:3000/api -d '{}'",
                 "curl -s https://example.com/docs", "curl -X POST http://127.0.0.1:54321/rest/v1/x -d '{}'", "node --test", "ls -la"]
        for cmd in dobre:
            self.assertEqual(bramka(cmd), "", cmd)
        self.assertIn('"deny"', subprocess.run(["bash", BRAMKA], input="nie json", capture_output=True, text=True).stdout, "nieczytelne wejście = odmowa")

    def test_profile_czyta_repo(self):
        p = json.loads(self.f2("profile", "--repo", self.repo).stdout)
        self.assertEqual(p["package_manager"], "npm")
        self.assertIn("npm run test", p["verify"])
        self.assertIn("npm run lint", p["verify"])
        self.assertTrue(any("baseRef" in n for n in p["notes"]))
        self.assertIn("user_profile_path", p)
        os.makedirs(os.path.dirname(p["user_profile_path"]))
        with open(p["user_profile_path"], "w") as f:
            json.dump({"live_verify_skill": "verify-admotiv", "notes": ["dev czyta prod"]}, f)
        p2 = json.loads(self.f2("profile", "--repo", self.repo).stdout)
        self.assertEqual(p2["live_verify_skill"], "verify-admotiv")
        self.assertIn("dev czyta prod", p2["notes"])


if __name__ == "__main__":
    unittest.main()


class Plan(Baza):
    """`plan check` i `create --plan`: wzór przechodzi, każdy znany brak zapala."""

    def plan(self, tekst, nazwa="plan.md"):
        p = os.path.join(self.tmp, nazwa)
        with open(p, "w") as f:
            f.write(tekst)
        return p

    def check(self, tekst, *extra):
        return self.f2("plan", "check", self.plan(tekst), *extra, ok=False)

    def test_wzor_przechodzi_takze_bez_nadzoru(self):
        r = self.check(PLAN_OK)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("plan OK: kryteria 3 (komenda: 0, słowo modelu: 3), Granice", r.stdout)
        self.assertEqual(self.check(PLAN_OK, "--unattended").returncode, 0)

    def test_znane_braki_zapalaja(self):
        bez_granic = PLAN_OK.split("## Granice")[0]
        przypadki = [
            (PLAN_OK.replace("Ścieżka użytkownika: handlowiec na liście rekordów klika „Eksport” i dostaje plik CSV z kolumnami jak na ekranie.", ""), "ścieżki użytkownika", ()),
            (PLAN_OK.replace("## Poza zakresem\n- eksport XLSX, harmonogram eksportów\n", ""), "Poza zakresem", ()),
            (PLAN_OK.replace("- wiersz w tabeli `eksporty` po pobraniu → 1 nowy wiersz z liczbą rekordów równą licznikowi na ekranie\n", "")
                    .replace("- czas od kliknięcia do pobrania, mierzony tym samym narzędziem i kontem → poniżej 3 s dla 500 rekordów\n", ""), "kryteriów 1", ()),
            (PLAN_OK.replace("## Poza zakresem", "- a → b\n- c → d\n- e → f\n\n## Poza zakresem"), "kryteriów 6", ()),
            (PLAN_OK.replace("## Poza zakresem", "- testy zielone → CI zielone\n\n## Poza zakresem"), "nie jest kryterium", ()),
            (PLAN_OK.replace("→ pobrany plik", "pobrany plik"), "bez „→”", ()),
            (bez_granic, "brak sekcji „## Granice”", ("--unattended",)),
            (PLAN_OK.replace("- Koszt: budżet 20 USD, bez wywołań płatnych per obiekt.\n", ""), "Granice bez: koszt/budżet", ("--unattended",)),
        ]
        for tekst, oczekiwane, extra in przypadki:
            r = self.check(tekst, *extra)
            self.assertNotEqual(r.returncode, 0, f"brak nie zapalił: {oczekiwane}")
            self.assertIn(oczekiwane, r.stderr)
        self.assertEqual(self.check(bez_granic).returncode, 0, "bez --unattended Granice nie są wymagane")

    def test_create_odmawia_planu_z_brakami_i_przyjmuje_wzor(self):
        zly = self.plan("# plan\n", "zly.md")
        r = self.f2("create", "--slug", "Zly plan", "--repo", self.repo, "--plan", zly, ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("plan check", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.home, "active.json")), "odmowa nie tworzy przelotu")
        dobry = self.plan(PLAN_OK, "dobry.md")
        rid = self.f2("create", "--slug", "Dobry plan", "--repo", self.repo, "--plan", dobry).stdout.strip()
        self.assertEqual(self.run_json()["plan"], dobry)
        self.assertTrue(rid)
        r = self.f2("create", "--slug", "Bez granic", "--repo", self.repo, "--plan", self.plan(PLAN_OK.split("## Granice")[0], "bg.md"), "--unattended", ok=False)
        self.assertNotEqual(r.returncode, 0, "bez nadzoru bez Granic nie startuje")


class Bledy(Baza):
    """Scenariusze z recenzji: każdy odtwarza wejście → zły wynik na kodzie sprzed poprawki."""

    def scalone(self):
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged", *SKROT)

    def test_close_bez_head_integracji_nie_daje_done(self):
        self.nowy()
        self.scalone()
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass")
        r = self.f2("close")
        self.assertTrue(r.stdout.startswith("partial"), r.stdout)
        self.assertIn("HEAD integracji nieznany", r.stdout)

    def test_close_head_tylko_asercja(self):
        self.nowy()
        self.scalone()
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass")
        with open(os.path.join(self.repo, "x.ts"), "w") as f:
            f.write("x")
        self.g("add", "x.ts")
        self.g("commit", "-qm", "x")
        self.integracja(self.g("rev-parse", "HEAD"))
        r = self.f2("close", "--head", self.head, ok=False)
        self.assertNotEqual(r.returncode, 0, "--head starszy niż integracja nie zastępuje HEAD")
        self.assertNotEqual(self.run_json()["state"], "done")
        self.assertTrue(self.f2("close").stdout.startswith("partial"), "dowód na A, integracja na B")

    def test_state_konczacy_tylko_przez_close(self):
        self.nowy()
        for s in ("done", "partial", "blocked", "cancelled"):
            r = self.f2("state", s, ok=False)
            self.assertNotEqual(r.returncode, 0, s)
            self.assertIn("close", r.stderr)
        self.assertEqual(self.run_json()["state"], "planning")

    def test_dowody_po_numerze_nie_po_sekundzie(self):
        rid = self.nowy()
        for i in range(9):
            self.f2("evidence", "add", "--for", "C1", "--cmd", f"curl /n {i}", "--sha", self.head, "--result", "2", "--verdict", "pass")
        self.assertEqual(self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "3", "--verdict", "fail").stdout.strip(), "E10")
        kat = os.path.join(self.home, "runs", rid, "evidence")
        for n in os.listdir(kat):
            p = os.path.join(kat, n)
            e = json.loads(self.czytaj(p))
            e["ts"] = "2026-01-01T00:00:00Z"
            with open(p, "w") as f:
                json.dump(e, f)
        self.integracja()
        self.assertEqual(self.f2("evidence", "check", ok=False).returncode, 1, "E10 fail jest najnowszy mimo tej samej sekundy")

    def test_dowod_pass_fail_pass_to_nowy_wpis(self):
        self.nowy()
        args = ("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2")
        self.assertEqual(self.f2(*args, "--verdict", "pass").stdout.strip(), "E1")
        self.assertEqual(self.f2(*args, "--verdict", "fail").stdout.strip(), "E2")
        self.assertEqual(self.f2(*args, "--verdict", "pass").stdout.strip(), "E3", "pass po fail to nowy pomiar")
        self.assertEqual(self.run_json()["criteria"][0]["status"], "pass")
        self.assertEqual(self.f2(*args, "--verdict", "pass").stdout.strip(), "E3", "powtórka najnowszego bez nowego wpisu")

    def test_running_tylko_z_frontu(self):
        rid = self.nowy()
        r = self.f2("task", "set", "T2", "--status", "running", "--spawn-sha", self.head, ok=False)
        self.assertIn("front", r.stderr, "zależność T1 niescalona")
        self.f2("task", "add", "--id", "T7", "--name", "n", "--files", "g.ts")
        self.f2("decide", "ask", "--kind", "approval", "--question", "q", "--options", "a | b", "--rec", "a", "--blocks", "T7", "--unblock-on", "a")
        r = self.f2("task", "set", "T7", "--status", "running", "--spawn-sha", self.head, ok=False)
        self.assertIn("front", r.stderr, "decyzja pending blokuje spawn")
        r = self.f2("task", "set", "T7", "--status", "running", "--spawn-sha", self.head, "--force", ok=False)
        self.assertIn("--note", r.stderr, "--force bez powodu odrzucony")
        self.f2("task", "set", "T7", "--status", "running", "--spawn-sha", self.head, "--force", "--note", "człowiek zgodził się w czacie")
        self.assertIn("--force", self.czytaj(os.path.join(self.home, "runs", rid, "log.tsv")))

    def test_rezerwacja_frontu_jednym_wywolaniem(self):
        self.nowy()
        self.f2("task", "set", "T1", "--status", "merged", *SKROT)
        self.f2("task", "add", "--id", "T5", "--name", "x", "--files", "e.ts")
        self.f2("task", "add", "--id", "T6", "--name", "y", "--files", "f.ts")
        r = self.f2("task", "set", "T2,T3,T5,T6", "--status", "running", "--spawn-sha", self.head, ok=False)
        self.assertIn("brak wolnego miejsca", r.stderr)
        self.assertEqual({t["id"]: t["status"] for t in self.run_json()["tasks"]}["T2"], "ready", "odmowa nie rezerwuje części")
        self.f2("task", "set", "T2,T3,T5", "--status", "running", "--spawn-sha", self.head)
        st = {t["id"]: (t["status"], t["spawn_sha"]) for t in self.run_json()["tasks"]}
        for t in ("T2", "T3", "T5"):
            self.assertEqual(st[t], ("running", self.head))
        self.assertNotEqual(self.f2("task", "set", "T2,T3", "--agent", "a1", ok=False).returncode, 0, "jeden agent na kilka zadań odrzucony")
        self.f2("task", "set", "T2", "--agent", "a1")

    def test_wlasciciel_pliku_po_sciezce_kanonicznej(self):
        self.nowy()
        r = self.f2("task", "add", "--name", "z", "--files", "./a.ts", ok=False)
        self.assertIn("właściciela", r.stderr)
        r = self.f2("task", "add", "--name", "z", "--files", "src//../b.ts", ok=False)
        self.assertIn("właściciela", r.stderr)
        self.f2("task", "add", "--id", "T9", "--name", "z", "--files", "./src/x.ts")
        self.assertEqual(next(t for t in self.run_json()["tasks"] if t["id"] == "T9")["files"], ["src/x.ts"])

    def test_create_ponowny_ze_zmienionym_planem_ostrzega(self):
        plan = os.path.join(self.tmp, "plan.md")
        with open(plan, "w") as f:
            f.write(PLAN_OK)
        a = self.f2("create", "--slug", "p", "--repo", self.repo, "--plan", plan).stdout.strip()
        r = self.f2("create", "--slug", "p", "--repo", self.repo, "--plan", plan)
        self.assertEqual((r.stdout.strip(), r.stderr), (a, ""))
        with open(plan, "a") as f:
            f.write("\n- nowe kryterium → wynik\n")
        r = self.f2("create", "--slug", "p", "--repo", self.repo, "--plan", plan)
        self.assertEqual(r.stdout.strip(), a, "stdout to nadal samo id (skrypt czyta je wprost)")
        self.assertIn("plan zmieniony po starcie", r.stderr)
        self.assertIn("plan zmieniony", self.czytaj(os.path.join(self.home, "runs", a, "log.tsv")))

    def test_fixing_podbija_resumes(self):
        self.nowy()
        self.f2("task", "set", "T1", "--status", "running", "--spawn-sha", self.head)
        self.assertEqual(next(t for t in self.run_json()["tasks"] if t["id"] == "T1")["resumes"], 0, "running nie jest wznowieniem")
        self.f2("task", "set", "T1", "--status", "fixing")
        self.f2("task", "set", "T1", "--status", "fixing", "--note", "ta sama runda")
        self.assertEqual(next(t for t in self.run_json()["tasks"] if t["id"] == "T1")["resumes"], 1)

    def test_zmiana_wariantu_zeruje_rundy(self):
        self.nowy()
        self.f2("task", "bump", "T1", "--field", "rounds", "--by", "2")
        self.f2("task", "set", "T1", "--agent", "nowy-wykonawca")
        self.assertEqual(self.run_json()["tasks"][0]["rounds"], 2, "nowy wykonawca na tym samym wariancie liczy dalej")
        self.f2("task", "set", "T1", "--variant", "sonnet")
        self.assertEqual(self.run_json()["tasks"][0]["rounds"], 2, "ten sam wariant: bez zmiany")
        self.f2("task", "set", "T1", "--variant", "opus-high")
        self.assertEqual(self.run_json()["tasks"][0]["rounds"], 0, "nowy wariant liczy nieprzyjęte od zera")

    def test_plan_brak_tozsamosci_nazwany_poswiadczeniami(self):
        p = os.path.join(self.tmp, "plan.md")
        with open(p, "w") as f:
            f.write(PLAN_OK.replace("- Tożsamość obiektów po nazwie i miejscu, nie po ID; odbiór zastępczy, gdy brak.\n", ""))
        r = self.f2("plan", "check", p, "--unattended", ok=False)
        self.assertIn("Granice bez: tożsamość (poświadczenia)", r.stderr)

    def test_pojecia_wymagane_zawsze(self):
        p = os.path.join(self.tmp, "plan.md")
        with open(p, "w") as f:
            f.write(PLAN_OK.replace("## Pojęcia\n- brak nowych pojęć\n\n", ""))
        brak = ("Pojęcia: nowe nazwy widoczne dla użytkownika z definicją, wskaźnik do słownika modułu albo „brak nowych pojęć”; "
                "pojęcia, które się nakładają, dowozi słownik skillem /mattpocock-skills:domain-modeling przed startem")
        for extra in ((), ("--unattended",)):
            r = self.f2("plan", "check", p, *extra, ok=False)
            self.assertNotEqual(r.returncode, 0, extra)
            self.assertIn(brak, r.stderr)
        r = self.f2("create", "--slug", "bez pojec", "--repo", self.repo, "--plan", p, ok=False)
        self.assertNotEqual(r.returncode, 0, "create --plan bez Pojęć nie startuje")
        self.assertIn("Pojęcia", r.stderr)


class Sesje(Baza):
    """Dwa okna, dwa przeloty w jednym repo: zapisy i hooki trafiają do przelotu swojej sesji."""

    def stop(self, sesja=None):
        wej = {"cwd": self.repo, "background_tasks": []}
        if sesja:
            wej["session_id"] = sesja
        return self.f2("stop-check", stdin=json.dumps(wej)).stdout.strip()

    def test_dwie_sesje_dwa_przeloty(self):
        a = self.f2("create", "--slug", "a", "--repo", self.repo, "--unattended", sesja="S1").stdout.strip()
        b = self.f2("create", "--slug", "b", "--repo", self.repo, sesja="S2").stdout.strip()
        self.f2("criteria", "add", "--text", "z S1", sesja="S1")
        self.f2("criteria", "add", "--text", "z S2", sesja="S2")
        self.assertEqual([c["text"] for c in json.loads(self.f2("--run", a, "status", "--json").stdout)["criteria"]], ["z S1"])
        self.assertEqual([c["text"] for c in json.loads(self.f2("--run", b, "status", "--json").stdout)["criteria"]], ["z S2"])
        r = self.f2("status", ok=False)
        self.assertIn("kilka przelotów w repo", r.stderr, "terminal bez sesji nie zgaduje")
        odp = "foreman decide answer D1 rec --by human"
        self.assertIn('"deny"', self.hook("Bash", odp, sesja="S1"), "S1 prowadzi przelot bez nadzoru")
        self.assertEqual(self.hook("Bash", odp, sesja="S2"), "", "S2 prowadzi nadzorowany")
        self.assertIn('"deny"', self.hook("Bash", odp), "bez sesji: reguły każdego niezakończonego przelotu")
        self.f2("state", "running", sesja="S1")
        self.f2("task", "add", "--id", "T1", "--name", "x", "--files", "a.ts", sesja="S1")
        self.assertIn(a, json.loads(self.stop("S1"))["reason"])
        self.assertEqual(self.stop("S2"), "", "przelot S2 w planning")
        self.assertEqual(self.stop(), "", "bez sesji i bez jednoznacznego przelotu przepuszcza")

    def test_nie_wlasciciel_dostaje_odmowe_a_resume_przejmuje(self):
        a = self.f2("create", "--slug", "a", "--repo", self.repo, sesja="S1").stdout.strip()
        r = self.f2("--run", a, "criteria", "add", "--text", "x", sesja="S2", ok=False)
        self.assertIn("prowadzi inna sesja", r.stderr)
        self.assertIn(f"--run {a} resume", r.stderr)
        self.f2("--run", a, "status", sesja="S2")
        self.f2("--run", a, "evidence", "check", "--head", self.head, sesja="S2", ok=False)
        self.f2("--run", a, "human", "add", "krok", sesja=None)
        out = self.f2("--run", a, "resume", sesja="S2").stdout
        self.assertIn("nie są osiągalni z tej sesji", out)
        self.assertNotIn("nie żyją", out)
        self.assertEqual(self.run_json()["owner"], "S2")
        self.assertIn("przejęcie przez S2", self.czytaj(os.path.join(self.home, "runs", a, "log.tsv")))
        self.f2("criteria", "add", "--text", "x", sesja="S2")
        r = self.f2("criteria", "add", "--text", "y", sesja="S1", ok=False)
        self.assertIn("prowadzi inna sesja", r.stderr, "stary właściciel traci zapis")

    def test_create_idempotentny_ustawia_mapowanie_sesji(self):
        a = self.f2("create", "--slug", "a", "--repo", self.repo).stdout.strip()
        self.f2("create", "--slug", "b", "--repo", self.repo)
        self.assertEqual(self.f2("create", "--slug", "a", "--repo", self.repo, sesja="S3").stdout.strip(), a)
        akt = json.loads(self.czytaj(os.path.join(self.home, "active.json")))
        self.assertEqual(akt[f"{os.path.realpath(self.repo)}|S3"], a)
        self.assertEqual(json.loads(self.f2("status", "--json", sesja="S3").stdout)["id"], a)

    def test_create_z_obcej_sesji_nie_przejmuje_ani_nie_kasuje(self):
        a = self.f2("create", "--slug", "a", "--repo", self.repo, sesja="S1").stdout.strip()
        self.f2("criteria", "add", "--text", "z S1", sesja="S1")
        for extra in ((), ("--force",)):
            r = self.f2("create", "--slug", "a", "--repo", self.repo, *extra, sesja="S2", ok=False)
            self.assertNotEqual(r.returncode, 0, f"create {extra} z S2")
            self.assertIn("prowadzi inna sesja", r.stderr)
            self.assertIn(f"--run {a} resume", r.stderr)
        d = json.loads(self.f2("--run", a, "status", "--json").stdout)
        self.assertEqual(d["owner"], "S1")
        self.assertEqual([c["text"] for c in d["criteria"]], ["z S1"], "--force z obcej sesji nie kasuje przelotu")
        self.assertNotIn(f"{os.path.realpath(self.repo)}|S2", json.loads(self.czytaj(os.path.join(self.home, "active.json"))))
        self.f2("criteria", "add", "--text", "dalej S1", sesja="S1")

    def test_przelot_z_terminala_dostaje_wlasciciela_przy_pierwszym_zapisie(self):
        a = self.f2("create", "--slug", "a", "--repo", self.repo).stdout.strip()
        self.f2("--run", a, "criteria", "add", "--text", "z S1", sesja="S1")
        self.assertEqual(json.loads(self.f2("--run", a, "status", "--json").stdout)["owner"], "S1")
        self.assertIn("właściciel: S1 (pierwszy zapis)", self.czytaj(os.path.join(self.home, "runs", a, "log.tsv")))
        self.assertEqual(json.loads(self.czytaj(os.path.join(self.home, "active.json")))[f"{os.path.realpath(self.repo)}|S1"], a)
        r = self.f2("--run", a, "criteria", "add", "--text", "z S2", sesja="S2", ok=False)
        self.assertIn("prowadzi inna sesja", r.stderr)
        self.f2("--run", a, "criteria", "add", "--text", "z terminala")
        self.assertEqual([c["text"] for c in json.loads(self.f2("--run", a, "status", "--json").stdout)["criteria"]], ["z S1", "z terminala"])

    def test_stop_check_starej_sesji_nie_pisze_stanu(self):
        a = self.f2("create", "--slug", "a", "--repo", self.repo, sesja="S1").stdout.strip()
        self.f2("state", "running", sesja="S1")
        self.f2("task", "add", "--id", "T1", "--name", "x", "--files", "a.ts", sesja="S1")
        self.f2("--run", a, "resume", sesja="S2")
        kat = os.path.join(self.home, "runs", a)
        przed = (self.czytaj(os.path.join(kat, "run.json")), self.czytaj(os.path.join(kat, "log.tsv")))
        self.assertEqual(self.stop("S1"), "", "stara sesja nie prowadzi przelotu")
        self.assertEqual((self.czytaj(os.path.join(kat, "run.json")), self.czytaj(os.path.join(kat, "log.tsv"))), przed, "bez zapisu stanu")
        self.assertEqual(json.loads(self.stop("S2"))["decision"], "block", "nowy właściciel dostaje pełny limit")


class Integracja(Baza):
    """Gałąź integracji i SHA spawnu rozwiązane do commitów, nie do ruchomych nazw."""

    def test_close_liczy_head_galezi_nie_tagu_o_tej_nazwie(self):
        self.nowy()
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged", *SKROT)
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass")
        self.g("commit", "-q", "--allow-empty", "-m", "B")
        b = self.g("rev-parse", "HEAD")
        self.integracja(b)
        self.g("tag", "integracja/test-przelotu", self.head)
        out = self.f2("close").stdout
        self.assertTrue(out.startswith("partial"), out)
        self.assertEqual(self.run_json()["verdict"]["head"], b)

    def test_runda_poprawek_po_scaleniu_liczy_od_integracji(self):
        """Scalone T1 wraca do poprawek po recenzji; agent dociąga integrację z cudzym T2 i poprawia
        swój plik: odbiór widzi tylko jego zmianę, nie scaloną integrację."""
        self.nowy()
        self.f2("task", "set", "T1", "--status", "running", "--spawn-sha", self.head, "--verify", "true")
        self.f2("task", "set", "T1", "--status", "merged", *SKROT)
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        with open(os.path.join(self.repo, "b.ts"), "w") as f:
            f.write("T2")
        self.g("add", "b.ts")
        self.g("commit", "-qm", "scal T2")
        integ = self.g("rev-parse", "HEAD")
        self.g("checkout", "-q", "-")
        self.f2("task", "set", "T1", "--status", "fixing")
        self.assertEqual(next(t for t in self.run_json()["tasks"] if t["id"] == "T1")["spawn_sha"], integ)
        wt = os.path.join(self.tmp, "wt")
        self.g("worktree", "add", "-q", "-b", "poprawka", wt, integ)
        with open(os.path.join(wt, "a.ts"), "w") as f:
            f.write("poprawka")
        self.g("add", "a.ts", repo=wt)
        self.g("commit", "-qm", "poprawka T1", repo=wt)
        r = self.f2("accept", "T1", "--worktree", wt, ok=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    def test_close_z_pelna_nazwa_galezi(self):
        self.nowy("--branch", "refs/heads/integracja/test-przelotu")
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged", *SKROT)
        self.integracja()
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass")
        out = self.f2("close").stdout
        self.assertTrue(out.startswith("done"), out)
    def test_spawn_sha_przypiety_do_commita(self):
        self.nowy()
        self.assertNotEqual(self.f2("task", "set", "T2", "--spawn-sha", "nie-ma-takiego", ok=False).returncode, 0, "nierozwiązywalny SHA odrzucony")
        self.f2("task", "set", "T1", "--status", "running", "--agent", "a1", "--spawn-sha", "HEAD", "--verify", "true")
        self.assertEqual(next(t for t in self.run_json()["tasks"] if t["id"] == "T1")["spawn_sha"], self.head)
        wt = os.path.join(self.tmp, "wt")
        self.g("worktree", "add", "-q", "-b", "agent", wt, self.head)
        for p in ("a.ts", "z.ts"):
            with open(os.path.join(wt, p), "w") as f:
                f.write(p)
        self.g("add", "-A", repo=wt)
        self.g("commit", "-qm", "robota", repo=wt)
        r = self.f2("accept", "T1", "--worktree", wt, ok=False)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("poza zakresem zadania: z.ts", r.stdout)


class PlikiZadania(Baza):
    def test_task_add_odrzuca_katalog(self):
        self.nowy()
        os.makedirs(os.path.join(self.repo, "src", "crm"))
        for f in ("src/crm", "lib/"):
            r = self.f2("task", "add", "--id", "T9", "--name", "x", "--files", f"z.ts,{f}", "--verify", "true", ok=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("nie katalogi", r.stderr)
        self.assertFalse(any(t["id"] == "T9" for t in self.run_json()["tasks"]))
        r = self.f2("task", "set", "T1", "--files", "src/crm", ok=False)
        self.assertIn("nie katalogi", r.stderr)


class Odbior(Baza):
    """`accept`: dowód na przypiętym SHA worktree agenta, pełny zakres, pomiar poza blokadą."""

    def setUp(self):
        super().setUp()
        with open(os.path.join(self.repo, "x.ts"), "w") as f:
            f.write("export const x = 1\n" * 20)
        self.g("add", "x.ts")
        self.g("commit", "-qm", "x")
        self.head = self.g("rev-parse", "HEAD")
        self.rid = self.nowy()
        self.f2("task", "set", "T1", "--status", "running", "--agent", "ag1", "--spawn-sha", self.head, "--verify", "test -f a.ts")
        self.wt = os.path.join(self.tmp, "wt")
        self.g("worktree", "add", "-q", "-b", "agent", self.wt, self.head)

    def commit(self, *pliki):
        for p in pliki:
            with open(os.path.join(self.wt, p), "w") as f:
                f.write(p)
        self.g("add", "-A", repo=self.wt)
        self.g("commit", "-qm", "robota", repo=self.wt)
        return self.g("rev-parse", "HEAD", repo=self.wt)

    def accept(self, *extra, sesja=None):
        return self.f2("accept", "T1", "--worktree", self.wt, *extra, ok=False, sesja=sesja)

    def t1(self):
        return next(t for t in self.run_json()["tasks"] if t["id"] == "T1")

    def dowody_t1(self):
        return [json.loads(l) for l in [json.dumps(e) for e in self.run_json()["evidence"] if e["for"] == "T1"]]

    def test_accept_merge_scala_i_pokazuje_front(self):
        sha = self.commit("a.ts")
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        r = self.accept("--merge")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.t1()["status"], "merged")
        self.assertEqual(self.g("rev-parse", "HEAD^2"), sha, "merge --no-ff przypiętego SHA")
        self.assertIn("gotowe: T2, T3", r.stdout)
    def test_accept_agent_wciagnal_nowsza_integracje(self):
        """Agent na polecenie scala nowszą integrację: pliki innych zadań nie są „poza zakresem”."""
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        with open(os.path.join(self.repo, "inny.ts"), "w") as f:
            f.write("inne zadanie")
        self.g("add", "inny.ts")
        self.g("commit", "-qm", "inne zadanie scalone")
        self.g("merge", "-q", "--no-edit", "integracja/test-przelotu", repo=self.wt)
        self.commit("a.ts")
        r = self.accept()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.commit("poza.ts")
        self.assertIn("poza zakresem zadania: poza.ts", self.accept().stdout, "kontrola zakresu zostaje")
    def test_reczne_merged_po_nieudanym_odbiorze_odrzucone(self):
        """`accept … | tail && git merge && task set --status merged`: pipe zjada kod wyjścia,
        zadanie z odbiorem fail nie może wejść jako merged bez --force --note."""
        self.commit("a.ts", "poza.ts")
        self.assertNotEqual(self.accept().returncode, 0)
        r = self.f2("task", "set", "T1", "--status", "merged", ok=False)
        self.assertNotEqual(r.returncode, 0, "merged mimo fail")
        self.assertIn("accept", r.stderr)
        self.assertEqual(self.t1()["status"], "running")
        self.f2("task", "set", "T1", "--status", "merged", "--force", "--note", "konflikt rozwiązany ręcznie")
        self.assertEqual(self.t1()["status"], "merged")
        self.assertIn("mimo odbioru", open(os.path.join(self.home, "runs", self.rid, "log.tsv")).read())

    def test_accept_merge_z_worktree_sesji(self):
        """Sesja w worktree repo przelotu (nie w głównym klonie) scala tak samo."""
        sha = self.commit("a.ts")
        sesja_wt = os.path.join(self.tmp, "sesja")
        self.g("worktree", "add", "-q", "-b", "integracja/test-przelotu", sesja_wt, self.head)
        r = self.f2("accept", "T1", "--worktree", self.wt, "--merge", ok=False, cwd=sesja_wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.t1()["status"], "merged")
        self.assertEqual(self.g("rev-parse", "HEAD^2", repo=sesja_wt), sha)
        self.assertEqual(self.g("rev-parse", "HEAD"), self.head, "główny klon nietknięty")

    def test_accept_merge_poza_galezia_integracji_odmawia_przed_pomiarem(self):
        self.commit("a.ts")
        r = self.accept("--merge")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("integracja/test-przelotu", r.stderr)
        self.assertEqual(self.dowody_t1(), [], "bez pomiaru")
        self.assertEqual(self.t1()["status"], "running")
    def test_accept_merge_konflikt_cofa_scalenie(self):
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        with open(os.path.join(self.repo, "a.ts"), "w") as f:
            f.write("inna treść")
        self.g("add", "a.ts")
        self.g("commit", "-qm", "konflikt")
        przed = self.g("rev-parse", "HEAD")
        self.commit("a.ts")
        r = self.accept("--merge")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("konflikt", r.stdout)
        self.assertEqual(self.g("rev-parse", "HEAD"), przed)
        self.assertEqual(self.g("status", "--porcelain"), "")
        self.assertEqual(self.t1()["status"], "running")
    def test_accept_merge_nie_przerywa_cudzego_scalenia(self):
        self.commit("a.ts")
        self.g("checkout", "-q", "-b", "inna")
        with open(os.path.join(self.repo, "x.ts"), "w") as f:
            f.write("inna\n")
        self.g("commit", "-qam", "inna")
        self.g("checkout", "-q", "-")
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        with open(os.path.join(self.repo, "x.ts"), "w") as f:
            f.write("integracja\n")
        self.g("commit", "-qam", "integracja")
        subprocess.run(["git", "-C", self.repo, "merge", "-q", "inna"], capture_output=True)
        with open(os.path.join(self.repo, "x.ts"), "w") as f:
            f.write("rozwiązane ręcznie\n")
        self.g("add", "x.ts")
        r = self.accept("--merge")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(subprocess.run(["git", "-C", self.repo, "rev-parse", "-q", "--verify", "MERGE_HEAD"], capture_output=True).returncode, 0, "cudze scalenie trwa")
        with open(os.path.join(self.repo, "x.ts")) as f:
            self.assertEqual(f.read(), "rozwiązane ręcznie\n")
    def test_accept_merge_galaz_zmieniona_w_trakcie_pomiaru(self):
        self.commit("a.ts")
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        self.g("branch", "inna")
        self.f2("task", "set", "T1", "--verify", f"git -C {self.repo} checkout -q inna")
        r = self.accept("--merge")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotEqual(self.t1()["status"], "merged")
        self.assertEqual(self.g("rev-parse", "inna"), self.head, "nic nie scalone na innej gałęzi")
    def test_accept_merge_nie_nadpisuje_ignorowanych(self):
        with open(os.path.join(self.repo, ".gitignore"), "w") as f:
            f.write("a.ts\n")
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        with open(os.path.join(self.repo, "a.ts"), "w") as f:
            f.write("cudza praca")
        with open(os.path.join(self.wt, "a.ts"), "w") as f:
            f.write("agent")
        self.g("add", "-f", "a.ts", repo=self.wt)
        self.g("commit", "-qm", "robota", repo=self.wt)
        r = self.accept("--merge")
        self.assertNotEqual(r.returncode, 0)
        with open(os.path.join(self.repo, "a.ts")) as f:
            self.assertEqual(f.read(), "cudza praca")
        self.assertNotEqual(self.t1()["status"], "merged")
    def test_accept_merge_bez_commita_z_konfiguracji(self):
        sha = self.commit("a.ts")
        self.g("checkout", "-q", "-b", "integracja/test-przelotu")
        self.g("config", "branch.integracja/test-przelotu.mergeOptions", "--no-commit")
        r = self.accept("--merge")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.g("rev-parse", "HEAD^2"), sha)
    def test_task_set_worktree_rejestruje_wlasnosc(self):
        self.f2("task", "set", "T1", "--worktree", self.wt)
        own = {o["ref"]: o["kind"] for o in self.run_json()["owned"]}
        self.assertEqual(own.get(os.path.realpath(self.wt)) or own.get(self.wt), "worktree")
        self.assertEqual(own.get("agent"), "branch")
    def test_pass_daje_sha_do_scalenia_i_log(self):
        sha = self.commit("a.ts")
        self.f2("task", "set", "T1", "--verify", f"{sys.executable} -I {BIN} status > /dev/null && test -f a.ts")
        r = self.accept("--timeout", "60")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"SHA do scalenia: {sha}", r.stdout)
        e = self.dowody_t1()[-1]
        self.assertEqual((e["verdict"], e["sha"]), ("pass", sha))
        self.assertTrue(os.path.exists(os.path.join(self.home, "runs", self.rid, "evidence", e["file"])))
        self.assertEqual(self.t1()["rounds"], 0)

    def test_brudne_drzewo_odmowa(self):
        self.commit("a.ts")
        with open(os.path.join(self.wt, "a.ts"), "a") as f:
            f.write("niezacommitowana poprawka")
        r = self.accept()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("niezacommitowane zmiany", r.stderr)
        self.assertEqual(self.dowody_t1(), [], "odmowa nie zapisuje dowodu")

    def test_plik_poza_zakresem(self):
        self.commit("a.ts", "z.ts")
        r = self.accept()
        self.assertEqual(r.returncode, 1)
        self.assertIn("poza zakresem zadania: z.ts", r.stdout)
        self.assertEqual(self.t1()["rounds"], 0, "porażka księgowa nie podbija rund")

    def test_rounds_liczy_tylko_fail_komendy(self):
        """Kontrola czułości: ta sama ścieżka z padającą komendą podbija rounds; zakres,
        przodek i drzewo zmienione w trakcie nie."""
        self.commit("a.ts")
        self.f2("task", "set", "T1", "--verify", "false")
        self.assertEqual(self.accept().returncode, 1)
        self.assertEqual(self.t1()["rounds"], 1, "fail komendy podbija")
        self.f2("task", "set", "T1", "--verify", "true")
        self.commit("z.ts")
        self.assertIn("poza zakresem", self.accept().stdout)
        self.assertEqual(self.t1()["rounds"], 1, "zakres nie podbija")
        self.f2("task", "set", "T1", "--spawn-sha", self.g("commit-tree", "HEAD^{tree}", "-m", "obok"))
        self.assertIn("nie jest przodkiem", self.accept().stdout)
        self.assertEqual(self.t1()["rounds"], 1, "przodek nie podbija")
        self.assertIn("rounds bez zmian", self.czytaj(os.path.join(self.home, "runs", self.rid, "log.tsv")))

    def test_fail_komendy_po_porazce_ksiegowej_na_tym_samym_sha(self):
        """Odbiór odrzucony za zakres, zakres poszerzony, komenda pada na tym samym SHA:
        to nowy pomiar (inny wynik), więc nowy dowód i rounds +1."""
        self.commit("a.ts", "z.ts")
        self.f2("task", "set", "T1", "--verify", "false")
        self.assertIn("poza zakresem", self.accept().stdout)
        self.f2("task", "set", "T1", "--files", "a.ts,z.ts")
        r = self.accept()
        self.assertIn("fail: T1 exit 1", r.stdout)
        self.assertEqual(self.t1()["rounds"], 1)
        self.assertEqual([e["result"][:13] for e in self.dowody_t1()], ["poza zakresem", "exit 1"])

    def test_plik_testu_obok_pliku_zadania(self):
        self.commit("a.ts", "a.test.ts")
        self.f2("task", "set", "T1", "--verify", "test -f a.test.ts")
        r = self.accept()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.t1()["files"], ["a.ts", "a.test.ts"], "test dopisany do zakresu po pass")
        self.assertIn("pliki testów obok plików zadania", self.czytaj(os.path.join(self.home, "runs", self.rid, "log.tsv")))
        # kontrola czułości: test pliku spoza zadania i test, który ma inne zadanie, zostają poza zakresem
        self.commit("b.test.ts")
        self.assertIn("poza zakresem zadania: b.test.ts", self.accept().stdout)
        self.f2("task", "add", "--id", "T9", "--name", "testy", "--files", "a.spec.ts")
        self.g("rm", "-q", "b.test.ts", repo=self.wt)
        self.commit("a.spec.ts")
        self.assertIn("poza zakresem zadania: a.spec.ts", self.accept().stdout, "plik wspólny ma jednego właściciela")
        self.f2("task", "set", "T9", "--status", "dropped")
        self.assertEqual(self.accept().returncode, 0, "zadanie dropped nie trzyma pliku")

    def test_towarzysz_testu(self):
        from importlib.machinery import SourceFileLoader
        t = SourceFileLoader("foreman_cli", BIN).load_module().towarzysz_testu
        pliki = {"src/x.ts", "lib/y.py"}
        for test, cel in (("src/x.test.ts", "src/x.ts"), ("src/x.spec.tsx", "src/x.ts"), ("src/__tests__/x.test.ts", "src/x.ts"),
                          ("lib/test_y.py", "lib/y.py"), ("x.test.ts", None), ("src/z.test.ts", None), ("src/x.ts.bak", None),
                          ("lib/tests/test_y.py", None), ("src/xtest.ts", None)):
            self.assertEqual(t(test, pliki), cel, test)

    def test_reported_sha(self):
        sha = self.commit("a.ts")
        self.f2("task", "set", "T1", "--verify", "false")
        r = self.accept("--reported-sha", sha)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("create --gate", r.stderr, "bez bramki repo słowo agenta nie ma siatki")
        self.assertEqual(self.dowody_t1(), [])
        self.f2("create", "--slug", "Test przelotu", "--repo", self.repo, "--gate", "true")
        r = self.accept("--reported-sha", self.head)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("raport nie dotyczy tego commita", r.stderr)
        self.assertEqual(self.dowody_t1(), [], "SHA inny niż HEAD worktree: bez dowodu")
        r = self.accept("--reported-sha", sha[:10])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        e = self.dowody_t1()[-1]
        self.assertEqual((e["verdict"], e["by"], e["sha"], e["file"]), ("pass", "model", sha, None), "komenda `false` niepuszczona")
        self.assertIn("raport agenta", e["result"])
        self.assertNotEqual(self.accept().returncode, 0, "kontrola czułości: bez --reported-sha komenda pada")
        self.f2("task", "set", "T1", "--verify", "true")
        self.commit("z.ts")
        r = self.accept("--reported-sha", self.g("rev-parse", "HEAD", repo=self.wt))
        self.assertIn("poza zakresem zadania: z.ts", r.stdout, "zakres sprawdzany także na słowo agenta")

    def test_rename_spoza_zakresu(self):
        self.g("mv", "x.ts", "a.ts", repo=self.wt)
        self.g("commit", "-qm", "rename", repo=self.wt)
        r = self.accept()
        self.assertEqual(r.returncode, 1)
        self.assertIn("x.ts", r.stdout, "źródło rename spoza zakresu widoczne")

    def test_plik_ze_spacja_w_nazwie_poza_zakresem(self):
        self.commit(" a.ts")
        self.f2("task", "set", "T1", "--verify", "true")
        r = self.accept()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("poza zakresem zadania:  a.ts", r.stdout)

    def test_zmiana_zakresu_w_trakcie_pomiaru(self):
        self.commit("a.ts")
        self.f2("task", "set", "T1", "--verify", f"{sys.executable} -I {BIN} task set T1 --files q.ts")
        r = self.accept()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("poza zakresem zadania: a.ts", r.stdout)
        self.assertEqual(self.dowody_t1()[-1]["verdict"], "fail")

    def test_commit_w_trakcie_pomiaru(self):
        sha = self.commit("a.ts")
        self.f2("task", "set", "T1", "--verify", "echo y >> a.ts && git commit -qam y")
        r = self.accept()
        self.assertEqual(r.returncode, 1)
        self.assertIn("drzewo zmieniło się w trakcie pomiaru", r.stdout)
        self.assertEqual(self.dowody_t1()[-1]["sha"], sha, "dowód na przypiętym SHA, nie na nowym commicie")

    def test_timeout(self):
        import time
        self.commit("a.ts")
        self.f2("task", "set", "T1", "--verify", "sleep 30")
        t0 = time.time()
        r = self.accept("--timeout", "1")
        self.assertLess(time.time() - t0, 15)
        self.assertEqual(r.returncode, 1)
        self.assertIn("timeout 1 s", r.stdout)

    def test_kontekst_agenta_prog_wykonawcy(self):
        def jsonl(p, tokeny):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(json.dumps({"type": "assistant", "message": {"model": "m", "usage": {"input_tokens": 10, "cache_read_input_tokens": tokeny, "cache_creation_input_tokens": 0}}}) + "\n")
        proj = os.path.join(self.tmp, "claude", "projects", "-repo")
        jsonl(os.path.join(proj, "S", "subagents", "agent-ag1.jsonl"), 210_000)
        self.commit("a.ts")
        out = self.accept(sesja="S").stdout
        self.assertIn("kontekst agenta ag1: 210k", out)
        self.assertIn("następna poprawka: nowy wykonawca (kontekst 210k)", out)
        self.assertNotIn("kontekst", self.f2("frontier").stdout, "bez sesji i transkryptu bez linii")


class Kontekst(unittest.TestCase):
    """Parser `kontekst()`: suma trzech pól, synthetic pominięty, urwana linia, kompakcja."""

    @classmethod
    def setUpClass(cls):
        from importlib.machinery import SourceFileLoader
        cls.m = SourceFileLoader("foreman_cli", BIN).load_module()

    def plik(self, *rekordy, ogon=""):
        fd, p = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write("".join(json.dumps(r) + "\n" for r in rekordy) + ogon)
        self.addCleanup(os.remove, p)
        return p

    def odp(self, model="claude-opus", i=100, cr=249_900, cc=1000):
        return {"type": "assistant", "message": {"model": model, "usage": {"input_tokens": i, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cc, "output_tokens": 5}}}

    def test_parser(self):
        k = self.m.kontekst
        self.assertEqual(k(self.plik(self.odp())), 251_000, "input + cache_read + cache_creation")
        self.assertEqual(k(self.plik(self.odp(), self.odp("<synthetic>", 0, 0, 0))), 251_000, "synthetic pominięty")
        self.assertEqual(k(self.plik(self.odp(), ogon='{"type":"assistant","message":{"usage":{"input_tokens":9')), 251_000, "urwana linia")
        komp = {"type": "system", "subtype": "compact_boundary", "compactMetadata": {"trigger": "auto", "preTokens": 251_000}}
        self.assertEqual(k(self.plik(self.odp(), komp)), "?", "kompakcja po pomiarze")
        self.assertEqual(k(self.plik(self.odp(), {"type": "user", "isCompactSummary": True})), "?")
        self.assertEqual(k(self.plik(self.odp(), komp, self.odp(cr=20_000))), 21_100, "pomiar po kompakcji liczy się")
        self.assertEqual(k(self.plik({"type": "user"})), "?", "brak pomiaru")
        self.assertIsNone(k("/nie/ma/takiego.jsonl"))


PLAN_CMD = PLAN_OK.replace(
    "- ekran listy po kliknięciu „Eksport” → pobrany plik `lista-<data>.csv`, nagłówek = kolumny widoczne na ekranie\n"
    "- wiersz w tabeli `eksporty` po pobraniu → 1 nowy wiersz z liczbą rekordów równą licznikowi na ekranie\n",
    "- `cat n.txt` → `2`\n- `test -f n.txt` → plik licznika istnieje\n")


class Dowod(Baza):
    """Kryteria z planu, plan zamrożony, dowód wykonany przez narzędzie, przelot bez zadań."""

    def setUp(self):
        super().setUp()
        self.head = self.plik("n.txt", "2\n")
        self.planp = os.path.join(self.tmp, "plan.md")
        with open(self.planp, "w") as f:
            f.write(PLAN_CMD)

    def plik(self, nazwa, tresc):
        with open(os.path.join(self.repo, nazwa), "w") as f:
            f.write(tresc)
        self.g("add", "-A"); self.g("commit", "-qm", nazwa)
        return self.g("rev-parse", "HEAD")

    def start(self, *extra):
        return self.f2("create", "--slug", "licznik", "--repo", self.repo, "--plan", self.planp, "--branch", "main", *extra).stdout.strip()

    def kryteria(self):
        return {c["id"]: c for c in self.run_json()["criteria"]}

    def test_rozklad_kryterium(self):
        from importlib.machinery import SourceFileLoader
        r = SourceFileLoader("foreman_cli", BIN).load_module().rozloz_kryterium
        self.assertEqual((r("`cat n.txt` → `2`")["cmd"], r("`cat n.txt` → `2`")["expect_out"]), ("cat n.txt", "2"))
        self.assertEqual((r("`npm test` → zielone")["cmd"], r("`npm test` → zielone")["expect_out"]), ("npm test", None))
        self.assertEqual(r("`printf 'a->b'` → `a->b`")["cmd"], "printf 'a->b'", "strzałka w komendzie nie rozcina kryterium")
        for proza in ("wiersz w tabeli `eksporty` po pobraniu → 1 nowy wiersz", "ekran listy → plik `lista.csv`", "po `npm test` ekran → zielony"):
            self.assertIsNone(r(proza)["cmd"], "grawisy w prozie to nie komenda")

    def test_create_wczytuje_kryteria_z_planu(self):
        self.start()
        k = self.kryteria()
        self.assertEqual([(c["id"], c["cmd"], c["expect_out"]) for c in k.values()],
                         [("C1", "cat n.txt", "2"), ("C2", "test -f n.txt", None), ("C3", None, None)])
        self.assertEqual(len(self.f2("criteria", "list").stdout.strip().splitlines()), 3, "bez ręcznego dopisywania")
        self.assertIn("pochodzą z planu", self.f2("criteria", "add", "--text", "x", ok=False).stderr)
        self.assertIn("pochodzą z planu", self.f2("criteria", "set", "C1", "--read", "true", ok=False).stderr)
        self.assertEqual(self.kryteria()["C1"]["cmd"], "cat n.txt")

    def test_zmiana_planu_zatrzymuje_odbior_i_zamkniecie(self):
        rid = self.start()
        self.f2("evidence", "run")
        self.f2("evidence", "add", "--for", "C3", "--cmd", "weryfikator: czas eksportu", "--sha", self.head, "--result", "1,2 s", "--verdict", "pass")
        with open(self.planp, "a") as f:
            f.write("- Koszt dodatkowy: brak.\n")
        for komenda in (("evidence", "run"), ("evidence", "add", "--for", "C3", "--cmd", "x", "--sha", self.head, "--verdict", "pass")):
            r = self.f2(*komenda, ok=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("plan zmieniony po starcie", r.stderr)
            self.assertIn("diff ", r.stderr, "komunikat mówi, jak zobaczyć zmianę")
        self.assertIn("DONE niedozwolone", self.f2("close", "--state", "done", ok=False).stderr)
        out = self.f2("close").stdout
        self.assertTrue(out.startswith("partial"), out)
        self.assertIn("plan zmieniony po starcie", out)
        self.assertIn("PLAN ZMIENIONY", self.f2("status").stdout)
        with open(self.planp, "w") as f:
            f.write(PLAN_CMD)
        self.assertEqual(self.f2("close").stdout.splitlines()[0], "done", "plik przywrócony = plan ten sam")

    def test_zmiana_planu_zatrzymuje_accept(self):
        self.start()
        self.g("branch", "f2/T1")
        wt = os.path.join(self.tmp, "wt")
        self.g("worktree", "add", "-q", wt, "f2/T1")
        self.f2("task", "add", "--id", "T1", "--name", "a", "--files", "a.ts", "--verify", "true")
        self.f2("task", "set", "T1", "--status", "running", "--spawn-sha", self.g("rev-parse", "HEAD"), "--worktree", wt)
        with open(self.planp, "a") as f:
            f.write("\n")
        r = self.f2("accept", "T1", "--worktree", wt, ok=False)
        self.assertIn("plan zmieniony po starcie", r.stderr)

    def test_replan_zatwierdza_czlowiek_i_nie_wraca_id(self):
        self.start()
        self.f2("evidence", "run")
        with open(self.planp, "w") as f:
            f.write(PLAN_CMD.replace("- `test -f n.txt` → plik licznika istnieje\n", "- `test -s n.txt` → plik licznika niepusty\n"))
        rid = self.run_json()["id"]
        r = self.f2("create", "--repo", self.repo, "--plan", self.planp, "--replan", ok=False)
        self.assertIn("--by human:<imię>", r.stderr)
        # cel wybiera przelot, nie slug: id niesie datę startu, więc replan innego dnia nie zakłada nowego
        r = self.f2("--run", rid, "create", "--slug", "inna nazwa", "--repo", self.repo, "--plan", self.planp, "--replan", "--by", "human:tester")
        self.assertEqual((r.stdout.strip(), os.listdir(os.path.join(self.home, "runs"))), (rid, [rid]))
        k = self.kryteria()
        self.assertEqual(sorted(k), ["C1", "C3", "C4"], "usunięte C2 nie wraca jako id nowego kryterium")
        self.assertEqual((k["C1"]["status"], k["C4"]["status"], k["C4"]["cmd"]), ("pass", "open", "test -s n.txt"), "ten sam tekst zachowuje dowody")
        self.assertIn("C4 bez dowodu", self.f2("close").stdout, "dowód starego C2 nie przechodzi na nowe kryterium")
        self.f2("evidence", "run")
        self.assertIn("zatwierdził human:tester", self.czytaj(os.path.join(self.home, "runs", self.run_json()["id"], "log.tsv")))

    def test_replan_bez_nadzoru_nie_z_sesji_modelu(self):
        self.start("--unattended")
        self.f2("close", "--state", "partial", sesja="S1")
        with open(self.planp, "w") as f:
            f.write(PLAN_CMD.replace("- `cat n.txt` → `2`\n", "- `true` → `2`\n".replace("`2`", "ok")))
        arg = ("create", "--slug", "licznik", "--repo", self.repo, "--plan", self.planp, "--replan", "--by", "human:model", "--unattended")
        r = self.f2(*arg, sesja="S1", ok=False)
        self.assertIn("bez nadzoru", r.stderr, "także po zamknięciu partial")
        r = self.f2("create", "--slug", "licznik", "--repo", self.repo, "--plan", self.planp, "--branch", "main", "--force", sesja="S1", ok=False)
        self.assertIn("bez nadzoru", r.stderr, "--force nie jest drugą drogą do zmiany planu")
        self.assertEqual(self.kryteria()["C1"]["cmd"], "cat n.txt")
        self.f2(*arg)  # terminal człowieka
        self.assertEqual(self.kryteria().get("C1"), None)

    def test_evidence_run_wykonuje_i_wykrywa_defekt(self):
        rid = self.start()
        kat = os.path.join(self.home, "runs", rid, "evidence")
        r = self.f2("evidence", "run")
        self.assertIn("pass: C1 exit 0, stdout „2”", r.stdout)
        self.assertIn("pass: C2 exit 0", r.stdout)
        self.assertIn("bez komendy (dowód weryfikatora, `evidence add`): C3", r.stdout)
        dow = self.run_json()["evidence"]
        self.assertEqual([(e["for"], e["by"], e["verdict"], e["sha"]) for e in dow], [("C1", "tool", "pass", self.head), ("C2", "tool", "pass", self.head)])
        self.assertEqual(self.czytaj(os.path.join(kat, dow[0]["file"])), "2\n", "stdout komendy drutem do pliku")
        r = self.f2("evidence", "run", "C1")
        self.assertIn("pass bez ponownego pomiaru: C1", r.stdout)
        self.assertEqual(len([e for e in self.run_json()["evidence"] if e["for"] == "C1"]), 1, "pass na tym samym SHA nie mierzy się drugi raz")
        self.f2("evidence", "run", "C1", "--again")
        dow = [e for e in self.run_json()["evidence"] if e["for"] == "C1"]
        self.assertEqual(len({e["file"] for e in dow}), 2, "--again: nowy wpis z własnym logiem")
        # wstrzyknięty defekt: licznik 3 zamiast 2
        sha = self.plik("n.txt", "3\n")
        self.assertIn("C1 dowód", self.f2("close").stdout, "dowód na starym SHA nie liczy się na nowym HEAD")
        r = self.f2("evidence", "run", ok=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("fail: C1 exit 0, stdout „3”, oczekiwane „2”", r.stdout)
        self.assertEqual(self.kryteria()["C1"]["status"], "fail")
        out = self.f2("close").stdout
        self.assertTrue(out.startswith("partial"), out)
        self.assertIn("C1 fail", out)
        # ręczny pass nie zastępuje pomiaru
        r = self.f2("evidence", "add", "--for", "C1", "--cmd", "cat n.txt", "--sha", sha, "--result", "2", "--verdict", "pass", ok=False)
        self.assertIn("evidence run C1", r.stderr)
        self.assertIn("kryterium bez komendy", self.f2("evidence", "run", "C3", ok=False).stderr)

    def test_bramka_repo(self):
        self.start()
        self.assertIn("bramka repo: brak", self.f2("status").stdout)
        self.f2("create", "--slug", "licznik", "--repo", self.repo, "--gate", "grep -q 2 n.txt")
        self.assertEqual(self.run_json()["gate"], "grep -q 2 n.txt", "idempotentny create ustawia bramkę")
        self.f2("evidence", "run", "C1", "C2")
        self.f2("evidence", "add", "--for", "C3", "--cmd", "weryfikator", "--sha", self.head, "--result", "ok", "--verdict", "pass")
        out = self.f2("close").stdout
        self.assertTrue(out.startswith("partial: G (bramka repo) bez dowodu"), out)
        self.assertIn("evidence run G", self.f2("evidence", "add", "--for", "G", "--cmd", "x", "--sha", self.head, "--verdict", "pass", ok=False).stderr)
        r = self.f2("evidence", "run")
        self.assertIn("pass bez ponownego pomiaru: C1", r.stdout)
        self.assertIn("pass: G exit 0", r.stdout)
        self.assertEqual(self.f2("evidence", "check").returncode, 0)
        self.assertEqual(self.f2("close").stdout.splitlines()[0], "done")
        # wstrzyknięty defekt łamie bramkę, a nowy HEAD unieważnia jej stary pass
        self.plik("n.txt", "3\n")
        self.assertIn("G (bramka repo) dowód", self.f2("evidence", "check", ok=False).stdout)
        r = self.f2("evidence", "run", "G", ok=False)
        self.assertIn("fail: G exit 1", r.stdout)
        self.assertIn("G (bramka repo) fail", self.f2("close").stdout)
        # bramkę raz ustawioną zmienia albo zdejmuje człowiek: inaczej model zdejmuje ją przed `close`
        for nowa in ("", "true"):
            r = self.f2("create", "--slug", "licznik", "--repo", self.repo, "--gate", nowa, ok=False)
            self.assertIn("--by human", r.stderr)
            self.assertEqual(self.run_json()["gate"], "grep -q 2 n.txt")
        self.f2("create", "--slug", "licznik", "--repo", self.repo, "--gate", "grep -q 3 n.txt", "--by", "human:tester")
        self.assertEqual(self.run_json()["gate"], "grep -q 3 n.txt")
        # replan niesie bramkę, nie gubi jej po cichu
        self.f2("create", "--repo", self.repo, "--plan", self.planp, "--replan", "--by", "human:tester", "--gate", "true")
        self.assertEqual(self.run_json()["gate"], "true")

    def test_dowod_komendy_tylko_od_narzedzia(self):
        rid = self.start()
        # dowód pass zapisany przed polem `by` (albo ręką): dla kryterium z komendą to słowo modelu
        with open(os.path.join(self.home, "runs", rid, "evidence", "E1.json"), "w") as f:
            json.dump({"id": "E1", "seq": 1, "ts": "2026-01-01T00:00:00Z", "for": "C1", "cmd": "cat n.txt", "sha": self.head, "result": "2", "file": None, "verdict": "pass"}, f)
        self.f2("evidence", "add", "--for", "C1", "--cmd", "notatka", "--sha", self.head, "--verdict", "unverified")
        self.assertEqual(self.kryteria()["C1"]["status"], "open")
        self.assertIn("C1 bez dowodu", self.f2("close").stdout)

    def test_stdout_kod_i_timeout(self):
        with open(self.planp, "w") as f:
            f.write(PLAN_CMD.replace("- `cat n.txt` → `2`\n- `test -f n.txt` → plik licznika istnieje\n",
                                     "- `echo 2; exit 3` → `2`\n- `echo zle >&2; echo 2` → `2`\n- `sleep 5` → koniec\n- `true` → `2`\n")
                    .replace("- czas od kliknięcia do pobrania, mierzony tym samym narzędziem i kontem → poniżej 3 s dla 500 rekordów\n", ""))
        rid = self.start()
        r = self.f2("evidence", "run", "--timeout", "1", ok=False)
        self.assertIn("fail: C1 exit 3", r.stdout, "zgodny stdout nie ratuje kodu wyjścia")
        self.assertIn("pass: C2 exit 0, stdout „2”", r.stdout, "stderr nie wchodzi do porównania")
        self.assertIn("fail: C3 timeout 1 s", r.stdout)
        self.assertIn("fail: C4 exit 0, stdout „”, oczekiwane „2”", r.stdout)
        self.assertEqual(self.czytaj(os.path.join(self.home, "runs", rid, "evidence", "C2-2.err")), "zle\n")

    def test_miejsce_pomiaru(self):
        self.start()
        os.remove(os.path.join(self.repo, "n.txt"))
        self.g("commit", "-qam", "licznik zniknął z commita")
        with open(os.path.join(self.repo, "n.txt"), "w") as f:
            f.write("2\n")  # plik bez `git add`: na commicie komenda zawodzi
        self.assertIn("pliki nieśledzone", self.f2("evidence", "run", ok=False).stderr)
        self.g("add", "-A"); self.g("commit", "-qm", "licznik wraca")
        self.f2("evidence", "run")
        wt = os.path.join(self.tmp, "wt")
        self.g("worktree", "add", "-q", "--detach", wt, "main")
        self.assertIn("pass: C1", self.f2("evidence", "run", "C1", "--again", cwd=wt).stdout, "worktree repo przelotu na HEAD integracji")
        with open(os.path.join(self.repo, "n.txt"), "w") as f:
            f.write("2\n\n")
        r = self.f2("evidence", "run", ok=False)
        self.assertIn("niezacommitowane zmiany", r.stderr)
        self.g("checkout", "--", "n.txt")
        self.g("commit", "-qm", "dalej", "--allow-empty", repo=wt)
        self.assertIn("pomiar liczy się na HEAD integracji", self.f2("evidence", "run", cwd=wt, ok=False).stderr)
        klon = os.path.join(self.tmp, "klon")
        subprocess.run(["git", "clone", "-q", self.repo, klon], check=True, capture_output=True)
        r = self.f2("--run", self.run_json()["id"], "evidence", "run", cwd=klon, ok=False)
        self.assertIn("nie należy do repo przelotu", r.stderr)

    def test_przelot_bez_zadan_od_planu_do_werdyktu(self):
        rid = self.start()
        self.f2("evidence", "run")
        out = self.f2("close").stdout
        self.assertTrue(out.startswith("partial: C3 bez dowodu"), out)
        self.f2("evidence", "add", "--for", "C3", "--cmd", "weryfikator: czas eksportu", "--sha", self.head, "--result", "1,2 s", "--verdict", "pass")
        out = self.f2("close").stdout.splitlines()
        self.assertEqual(out[0], "done")
        self.assertEqual(out[1], "dowód pass: wykonana komenda zakończyła się powodzeniem: C1, C2; słowo modelu (weryfikator albo wpis ręczny): C3")
        d = self.run_json()
        self.assertEqual((d["state"], d["tasks"], d["verdict"]["by_model"]), ("done", [], ["C3"]))
        rap = self.f2("report").stdout
        self.assertIn("Dowód (wykonana komenda): pass `cat n.txt`", rap)
        self.assertIn("Dowód (słowo modelu): pass `weryfikator: czas eksportu`", rap)

    def test_plan_bez_komend_nie_zatrzymuje_drogi(self):
        with open(self.planp, "w") as f:
            f.write(PLAN_OK)
        self.start()
        for c in ("C1", "C2", "C3"):
            self.f2("evidence", "add", "--for", c, "--cmd", "weryfikator", "--sha", self.head, "--result", "ok", "--verdict", "pass")
        r = self.f2("evidence", "run")
        self.assertIn("żadne kryterium nie ma komendy", r.stdout)
        self.assertEqual(self.f2("close").stdout.splitlines()[0], "done")

    def test_straznik_dopuszcza_tylko_kontrakt(self):
        rid = self.start()
        kat = os.path.join(self.home, "runs", rid)
        self.assertEqual(self.hook("Write", file_path=os.path.join(kat, "kontrakt.md")), "")
        for chroniony in ("run.json", "plan.md", "evidence/kontrakt.md"):
            self.assertIn("deny", self.hook("Write", file_path=os.path.join(kat, chroniony)), chroniony)


class Koszt(Baza):
    """`cost --scan`: reguła E zgodna z bin/koszty.py, agent przypięty do zadania."""

    def test_koszt_per_agent_zgodny_z_koszty_py(self):
        def odp(mid, model, i, cr, cc, o, ts="2026-01-01T10:00:00Z"):
            return {"type": "assistant", "timestamp": ts, "message": {"id": mid, "model": model, "usage": {
                "input_tokens": i, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cc, "output_tokens": o}}}
        def zapis(p, *rek):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write("".join(json.dumps(r) + "\n" for r in rek) + "{urwana")
        proj = os.path.join(self.tmp, "claude", "projects", "-repo")
        sesja = os.path.join(proj, "S.jsonl")
        zapis(sesja, odp("m1", "claude-opus", 1000, 400_000, 20_000, 10), odp("m1", "claude-opus", 1000, 400_000, 20_000, 3000),
              odp("m2", "claude-opus", 500, 900_000, 1000, 2000), odp("m3", "<synthetic>", 9, 9, 9, 9))
        zapis(os.path.join(proj, "S", "subagents", "agent-ag1.jsonl"), odp("a1", "claude-sonnet", 2000, 300_000, 50_000, 40_000))
        self.f2("create", "--slug", "k", "--repo", self.repo, sesja="S")
        self.f2("task", "add", "--id", "T1", "--name", "a", "--files", "a.ts", sesja="S")
        self.f2("task", "set", "T1", "--agent", "ag1", sesja="S")
        out = self.f2("cost", "--scan", sesja="S").stdout
        e = self.run_json()["cost"]["e"]
        self.assertEqual([(w["who"], w["task"], w["replies"]) for w in e["rows"]], [("brygadzista", None, 2), ("agent", "T1", 1)])
        self.assertIn("agent ag1 T1: E=0.29", out)
        import ast
        wzor = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(BIN), "koszty.py"), sesja],
                              capture_output=True, text=True, check=True).stdout
        wzor = ast.literal_eval(wzor.split("E per model:")[1].strip())
        self.assertEqual({k: round(v, 2) for k, v in e["per_model"].items()}, wzor, "ta sama reguła co koszty.py")
        # suma liczona z wartości niezaokrąglonych: 11 × 0,101499 = 1,116 → 1,12, nie 11 × 0,101 = 1,11
        for i in range(11):
            zapis(os.path.join(proj, f"R{i}.jsonl"), odp(f"r{i}", "claude-haiku", 101_499, 0, 0, 0))
            self.f2("session", f"R{i}", sesja="S")
        self.assertIn("claude-haiku 1.12", self.f2("cost", "--scan", sesja="S").stdout)

