"""Testy kontraktu stanu foreman2: create → kryteria → graf → front → dowody → decyzje →
hooki (stop-check, straz, bramka-floty.sh) → close/resume. Każdy strażnik ma kontrolę
czułości: znana zła komenda musi go zapalić. Uruchom: python3 -I -m unittest discover -s foreman2/tests."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "foreman2")
BRAMKA = os.path.join(os.path.dirname(BIN), "bramka-floty.sh")
RUN = os.path.join(os.path.dirname(BIN), "run")

PLAN_OK = """# Eksport listy do CSV

Ścieżka użytkownika: handlowiec na liście rekordów klika „Eksport” i dostaje plik CSV z kolumnami jak na ekranie.

## Kryteria odbioru
- ekran listy po kliknięciu „Eksport” → pobrany plik `lista-<data>.csv`, nagłówek = kolumny widoczne na ekranie
- wiersz w tabeli `eksporty` po pobraniu → 1 nowy wiersz z liczbą rekordów równą licznikowi na ekranie
- czas od kliknięcia do pobrania, mierzony tym samym narzędziem i kontem → poniżej 3 s dla 500 rekordów

## Poza zakresem
- eksport XLSX, harmonogram eksportów

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
        self.env = dict(os.environ, FOREMAN2_HOME=self.home)
        self.env.pop("CLAUDE_SESSION_ID", None)

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

    def f2(self, *a, stdin=None, ok=True, cwd=None):
        r = subprocess.run([sys.executable, "-I", BIN, *a], capture_output=True, text=True, cwd=cwd or self.repo, env=self.env, input=stdin)
        if ok and r.returncode:
            self.fail(f"foreman2 {' '.join(a)} → {r.returncode}: {r.stderr}")
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

    def hook(self, tool, command=None, cwd=None, **extra):
        wej = {"tool_name": tool, "cwd": cwd or self.repo, "tool_input": {**({"command": command} if command is not None else {}), **extra}}
        return self.f2("straz", stdin=json.dumps(wej)).stdout.strip()


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
        self.assertIn("foreman2", d["sources"])

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
        self.f2("task", "set", "T1", "--status", "merged", "--spawn-sha", self.head)
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
        self.f2("task", "set", "T1", "--status", "merged")
        self.assertEqual(self.f2("task", "add", "--name", "poprawki recenzji", "--files", "a.ts").stdout.strip(), "T5",
                         "plik zadania scalonego wolno dać nowemu zadaniu (runda poprawek)")

    def test_skrocony_sha_liczy_sie_jak_pelny(self):
        rid = self.nowy()
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged")
        e = self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head[:7], "--result", "2", "--verdict", "pass").stdout.strip()
        self.assertEqual(json.loads(self.f2("evidence", "show", e).stdout)["sha"], self.head, "skrócony SHA rozwinięty do pełnego")
        self.assertEqual(self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass").stdout.strip(), e, "ten sam pomiar bez powtórki")
        self.assertIn("każde kryterium", self.f2("evidence", "check", "--head", self.head[:8]).stdout)
        self.assertEqual(self.f2("--run", rid, "close", "--head", self.head[:7]).stdout.strip(), "done")

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
            self.f2("task", "set", t, "--status", "merged")
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
            self.f2("task", "set", t, "--status", "merged")
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass")
        self.f2("human", "add", "opublikuj front")
        self.assertTrue(self.f2("close", "--head", self.head).stdout.startswith("partial"), "otwarty krok ludzki = PARTIAL")
        self.f2("--run", rid, "human", "done", "H1")
        r = self.f2("--run", rid, "close", "--head", "1" * 40)
        self.assertTrue(r.stdout.startswith("partial"), "dowód na innym SHA niż HEAD nie daje DONE")
        self.assertIn("HEAD", r.stdout)
        self.assertEqual(self.f2("--run", rid, "close", "--head", self.head).stdout.strip(), "done")
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
        self.assertNotEqual(subprocess.run([sys.executable, "-I", RUN, "--resume", rid, "--dry"], capture_output=True, text=True, env=self.env).returncode, 0, "runner nie wznawia anulowanego")

    ODPOWIEDZI_CZLOWIEKA = ("foreman2 decide answer D1 rec --by human", "python3 -I /x/bin/foreman2 --run r decide answer D1 tak --by=human:serge",
                            "cd /tmp && $F2 decide answer D1 rec --by 'human'")

    def test_straz_odmawia_odpowiedzi_jako_czlowiek_bez_nadzoru_i_zapisu_stanu(self):
        self.nowy("--unattended")
        self.f2("state", "running")
        for cmd in self.ODPOWIEDZI_CZLOWIEKA + ("echo '{}' >> ~/.foreman2/runs/r/decisions.jsonl",
                    "sed -i '' 's/pending/approved/' /h/runs/r/decisions.jsonl", "python3 -c 'open(\"run.json\",\"w\")'"):
            self.assertIn('"deny"', self.hook("Bash", cmd), cmd)
        for cmd in ("foreman2 decide answer D1 rec --by codex", "foreman2 decide ask --kind approval --question q --options 'a | b' --rec a",
                    "cat ~/.foreman2/runs/r/decisions.jsonl", "jq . run.json", "git push origin integracja", "npm test"):
            self.assertEqual(self.hook("Bash", cmd), "", cmd)
        self.assertEqual(self.hook("Agent"), "", "spawn w żywym przelocie wolny")
        self.assertIn('"deny"', self.hook("Bash", None), "komenda nieczytelna = odmowa")
        self.assertEqual(self.f2("straz", stdin="nie json").stdout.strip(), "", "śmieciowe stdin bez narzędzia przepuszcza")

    def test_straz_bez_nadzoru_nie_da_sie_obejsc_innym_przelotem_ani_edytorem(self):
        u = self.nowy("--unattended")
        self.f2("state", "running")
        for cmd in ("foreman2 create --slug inny --repo .", "$F2 create --slug 'Test przelotu' --repo . --force"):
            self.assertIn('"deny"', self.hook("Bash", cmd), cmd)
        self.assertIn('"deny"', self.hook("Write", file_path=os.path.join(self.home, "runs", u, "run.json")), "Write w run.json odmówiony")
        self.assertIn('"deny"', self.hook("Edit", file_path=os.path.join(self.home, "profiles", "x.json")), "Edit profilu odmówiony")
        self.assertEqual(self.hook("Write", file_path=os.path.join(self.repo, "a.ts")), "", "Write w repo wolny")
        drugi = self.git_repo("drugi")
        s = self.f2("create", "--slug", "Nadzorowany", "--repo", drugi, cwd=drugi).stdout.strip()
        self.assertIn('"deny"', self.hook("Bash", f"foreman2 --run {u} decide answer D1 rec --by human:serge", cwd=drugi), "cel --run bez nadzoru odmówiony mimo nadzorowanego aktywnego")
        self.assertEqual(self.hook("Bash", f"foreman2 --run {s} decide answer D1 rec --by human:serge", cwd=drugi), "", "nadzorowany cel z nadzorowanego cwd wolny")
        self.f2("close", "--note", "koniec", ok=False)
        self.f2("cancel", "--note", "stop")
        self.assertEqual(self.hook("Bash", "foreman2 create --slug nowy --repo ."), "", "po zakończeniu przelotu bez nadzoru create wolny")

    def test_straz_pod_nadzorem_przepuszcza_odpowiedz_z_czatu(self):
        self.nowy()
        self.f2("state", "running")
        for cmd in self.ODPOWIEDZI_CZLOWIEKA + ("foreman2 create --slug inny --repo .",):
            self.assertEqual(self.hook("Bash", cmd), "", cmd)
        self.assertIn('"deny"', self.hook("Bash", "echo '{}' >> ~/.foreman2/runs/r/decisions.jsonl"), "zapis stanu nadal odmówiony")
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

    def test_runner_dry_i_reszta_budzetu(self):
        plan = os.path.join(self.tmp, "plan.md")
        with open(plan, "w") as f:
            f.write(PLAN_OK)
        r = subprocess.run([sys.executable, "-I", RUN, "--repo", self.repo, "--slug", "lab", "--plan", plan, "--budget", "10", "--dry"],
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertIn("--max-budget-usd", d["cmd"])
        self.assertEqual(d["cmd"][d["cmd"].index("--max-budget-usd") + 1], "10.0")
        settings = json.loads(self.czytaj(os.path.join(self.home, "runs", d["run"], "settings.json")))
        agents = json.loads(self.czytaj(os.path.join(self.home, "runs", d["run"], "agents.json")))
        self.assertIn("foreman2-wykonawca", agents)
        self.assertNotIn("$HOME/.claude/skills/foreman2", json.dumps(agents), "ścieżka strażnika wskazuje ten katalog")
        self.assertIn(os.path.dirname(BRAMKA), json.dumps(agents))
        if not os.path.isdir(os.path.expanduser("~/.claude/skills/foreman2")):
            self.assertIn("PreToolUse", settings["hooks"])
            self.assertIn("Stop", settings["hooks"])
        self.f2("--run", d["run"], "cost", json.dumps({"sessions": [{"usd": 7.5}], "usd_total": 7.5})).stdout
        r = subprocess.run([sys.executable, "-I", RUN, "--resume", d["run"], "--dry"], capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["budget"], 2.5, "wznowienie dostaje resztę budżetu")
        self.f2("--run", d["run"], "cost", json.dumps({"sessions": [{"usd": 10}], "usd_total": 10}))
        r = subprocess.run([sys.executable, "-I", RUN, "--resume", d["run"], "--dry"], capture_output=True, text=True, env=self.env)
        self.assertNotEqual(r.returncode, 0, "budżet wyczerpany bez --budget odmawia")

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
        self.assertIn("plan OK: kryteria 3, Granice", r.stdout)
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
