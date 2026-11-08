"""Testy kontraktu stanu foreman2: create → kryteria → graf → front → dowody → decyzje → stop-check → close/resume.
Uruchom: python3 -I -m unittest discover -s foreman2/tests  (z katalogu repo)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "foreman2")


class Baza(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="f2test-")
        self.home = os.path.join(self.tmp, "home")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.g("init", "-q", "-b", "main")
        self.g("config", "user.email", "t@t")
        self.g("config", "user.name", "t")
        with open(os.path.join(self.repo, "package.json"), "w") as f:
            json.dump({"name": "x", "scripts": {"test": "node --test", "lint": "eslint ."}}, f)
        self.g("add", "-A")
        self.g("commit", "-qm", "init")
        self.head = self.g("rev-parse", "HEAD")
        self.env = dict(os.environ, FOREMAN2_HOME=self.home)
        self.env.pop("CLAUDE_SESSION_ID", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def g(self, *a):
        return subprocess.run(["git", "-C", self.repo, *a], capture_output=True, text=True, check=True).stdout.strip()

    def f2(self, *a, stdin=None, ok=True):
        r = subprocess.run([sys.executable, "-I", BIN, *a], capture_output=True, text=True, cwd=self.repo, env=self.env, input=stdin)
        if ok and r.returncode:
            self.fail(f"foreman2 {' '.join(a)} → {r.returncode}: {r.stderr}")
        return r

    def czytaj(self, p):
        with open(p) as f:
            return f.read()

    def run_json(self):
        return json.loads(self.f2("status", "--json").stdout)

    def nowy(self, *extra):
        rid = self.f2("create", "--slug", "Test przelotu", "--repo", self.repo, *extra).stdout.strip()
        self.f2("criteria", "add", "--text", "licznik rośnie", "--read", "GET /n", "--expected", "2")
        self.f2("task", "add", "--id", "T1", "--name", "typy", "--files", "a.ts", "--variant", "sonnet", "--verify", "npm test")
        self.f2("task", "add", "--id", "T2", "--name", "logika", "--files", "b.ts", "--deps", "T1")
        self.f2("task", "add", "--id", "T3", "--name", "ekran", "--files", "c.tsx", "--deps", "T1")
        self.f2("task", "add", "--id", "T4", "--name", "pomoc", "--files", "d.md", "--deps", "T2,T3")
        return rid


class TestPrzelot(Baza):
    def test_create_idempotentny_i_aktywny(self):
        a = self.f2("create", "--slug", "Mój przelot!", "--repo", self.repo).stdout.strip()
        b = self.f2("create", "--slug", "Mój przelot!", "--repo", self.repo).stdout.strip()
        self.assertEqual(a, b)
        self.assertTrue(a.endswith("-m-j-przelot"))
        akt = json.loads(self.czytaj(os.path.join(self.home, "active.json")))
        self.assertEqual(akt[os.path.realpath(self.repo)], a)
        d = self.run_json()
        self.assertEqual(d["base_sha"], self.head)
        self.assertEqual(d["state"], "planning")
        self.assertIn("foreman2", d["sources"])

    def test_front_zalezy_od_merge_i_miejsc(self):
        self.nowy()
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["ready"], ["T1"])
        self.f2("task", "set", "T1", "--status", "merged", "--spawn-sha", self.head)
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["ready"], ["T2", "T3"])
        self.f2("task", "set", "T2", "--status", "running", "--agent", "a1")
        self.f2("task", "set", "T3", "--status", "running", "--agent", "a2")
        self.f2("task", "add", "--id", "T5", "--name", "x", "--files", "e.ts")
        self.f2("task", "add", "--id", "T6", "--name", "y", "--files", "f.ts")
        self.f2("task", "set", "T5", "--status", "running")
        r = self.f2("task", "set", "T6", "--status", "running", ok=False)
        self.assertNotEqual(r.returncode, 0, "czwarty żywy agent przy max_live=3 ma zostać odrzucony")
        self.assertIn("brak wolnego miejsca", r.stderr)
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["free_slots"], 0)
        self.assertEqual(fr["spawn_now"], [])

    def test_zaleznosc_nieistniejaca_odrzucona(self):
        self.nowy()
        r = self.f2("task", "add", "--name", "z", "--deps", "T99", ok=False)
        self.assertNotEqual(r.returncode, 0)

    def test_dowod_ustawia_kryterium_i_wykrywa_staly_sha(self):
        self.nowy()
        e = self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass").stdout.strip()
        self.assertEqual(e, "E1")
        d = self.run_json()
        self.assertEqual(d["criteria"][0]["status"], "pass")
        self.assertEqual(d["criteria"][0]["evidence"], ["E1"])
        # ten sam dowód na tym samym SHA nie mnoży wpisów
        e2 = self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass").stdout.strip()
        self.assertEqual(e2, "E1")
        r = self.f2("evidence", "check", "--head", self.head, ok=False)
        self.assertEqual(r.returncode, 0)
        r = self.f2("evidence", "check", "--head", "0" * 40, ok=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nieaktualny E1", r.stdout)
        # unverified nie zalicza
        self.f2("evidence", "add", "--for", "C1", "--cmd", "oko", "--sha", self.head, "--verdict", "unverified")
        self.assertEqual(self.run_json()["criteria"][0]["status"], "pass", "unverified nie cofa pass")

    def test_decyzja_approval_tylko_czlowiek(self):
        self.nowy()
        did = self.f2("decide", "ask", "--kind", "approval", "--question", "Zapis do prod?", "--options", "tak | nie", "--rec", "nie", "--blocks", "T1").stdout.strip()
        self.assertEqual(did, "D1")
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["ready"], [], "decyzja pending blokuje zadanie na froncie")
        r = self.f2("decide", "answer", "D1", "rec", "--by", "agent:codex", ok=False)
        self.assertNotEqual(r.returncode, 0, "agent nie autoryzuje approval")
        self.assertIn("approval", r.stderr)
        r = self.f2("decide", "answer", "D1", "zupa", "--by", "human", ok=False)
        self.assertNotEqual(r.returncode, 0, "odpowiedź spoza opcji odrzucona")
        self.f2("decide", "answer", "D1", "rec", "--by", "human")
        dec = [json.loads(l) for l in self.f2("decisions", "--json").stdout.splitlines()]
        self.assertEqual(dec[0]["status"], "approved")
        self.assertEqual(dec[0]["reply"], "nie")
        r = self.f2("decide", "answer", "D1", "tak", "--by", "human")
        self.assertIn("już approved", r.stdout, "druga odpowiedź jest no-op")
        fr = json.loads(self.f2("frontier", "--json").stdout)
        self.assertEqual(fr["ready"], ["T1"])
        # override
        self.f2("decide", "ask", "--kind", "approval", "--question", "q2", "--options", "a | b", "--rec", "a")
        self.f2("decide", "answer", "D2", "b", "--by", "human:serge")
        dec = [json.loads(l) for l in self.f2("decisions", "--json").stdout.splitlines()]
        self.assertEqual(dec[1]["status"], "overridden")
        # auto: od razu auto_kept, agent może
        self.f2("decide", "ask", "--kind", "auto", "--question", "nazwa pola", "--options", "x | y", "--rec", "x")
        dec = [json.loads(l) for l in self.f2("decisions", "--json").stdout.splitlines()]
        self.assertEqual(dec[2]["status"], "auto_kept")
        self.assertEqual(dec[2]["reply"], "x")

    def test_stop_check_blokuje_tylko_gdy_jest_robota(self):
        self.nowy()
        wej = json.dumps({"cwd": self.repo, "background_tasks": [], "stop_hook_active": False})
        # planning: przepuszcza
        r = self.f2("stop-check", stdin=wej)
        self.assertEqual(r.stdout.strip(), "")
        self.f2("state", "running")
        # kontrola czułości: front ma T1, brak tła → blokada
        r = self.f2("stop-check", stdin=wej)
        out = json.loads(r.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("T1", out["reason"])
        # tło pracuje → przepuszcza
        r = self.f2("stop-check", stdin=json.dumps({"cwd": self.repo, "background_tasks": [{"id": "x"}], "stop_hook_active": True}))
        self.assertEqual(r.stdout.strip(), "")
        # druga blokada na tym samym froncie, trzecia przepuszcza (bez pętli)
        r = self.f2("stop-check", stdin=json.dumps({"cwd": self.repo, "background_tasks": [], "stop_hook_active": True}))
        self.assertEqual(json.loads(r.stdout)["decision"], "block")
        r = self.f2("stop-check", stdin=json.dumps({"cwd": self.repo, "background_tasks": [], "stop_hook_active": True}))
        self.assertEqual(r.stdout.strip(), "", "po dwóch blokadach przepuszcza")
        # pending approval blokujące T1 → front pusty → przepuszcza
        self.f2("task", "add", "--id", "T7", "--name", "n", "--files", "g.ts")
        self.f2("decide", "ask", "--kind", "approval", "--question", "q", "--options", "a | b", "--rec", "a", "--blocks", "T1,T7")
        r = self.f2("stop-check", stdin=wej)
        self.assertEqual(r.stdout.strip(), "")
        # śmieciowe stdin → przepuszcza (fail-open dla hooka Stop; strażnicy ruchu są w PreToolUse)
        r = self.f2("stop-check", stdin="nie json")
        self.assertEqual(r.returncode, 0)

    def test_close_odmawia_done_bez_dowodu(self):
        self.nowy()
        r = self.f2("close", "--state", "done", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("C1 open", r.stderr)
        r = self.f2("close")
        self.assertTrue(r.stdout.startswith("partial"))
        self.assertNotIn(os.path.realpath(self.repo), json.loads(self.czytaj(os.path.join(self.home, "active.json"))))

    def test_close_done_po_pelnym_dowodzie(self):
        rid = self.nowy()
        for t in ("T1", "T2", "T3", "T4"):
            self.f2("task", "set", t, "--status", "merged")
        self.f2("evidence", "add", "--for", "C1", "--cmd", "curl /n", "--sha", self.head, "--result", "2", "--verdict", "pass")
        self.f2("human", "add", "opublikuj front")
        r = self.f2("close")
        self.assertTrue(r.stdout.startswith("partial"), "otwarty krok ludzki = PARTIAL, nie DONE")
        self.f2("--run", rid, "human", "done", "H1")
        r = self.f2("--run", rid, "close")
        self.assertEqual(r.stdout.strip(), "done")
        d = json.loads(self.f2("--run", rid, "status", "--json").stdout)
        self.assertEqual(d["verdict"]["state"], "done")

    def test_blokada_zadania_daje_blocked(self):
        self.nowy()
        self.f2("task", "set", "T1", "--status", "blocked", "--note", "brak klucza API")
        r = self.f2("close")
        self.assertTrue(r.stdout.startswith("blocked"))

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

    def test_cancel_zwalnia_aktywny(self):
        self.nowy()
        self.f2("cancel", "--note", "zmiana zakresu")
        self.assertNotIn(os.path.realpath(self.repo), json.loads(self.czytaj(os.path.join(self.home, "active.json"))))
        r = self.f2("status", ok=False)
        self.assertNotEqual(r.returncode, 0)

    def test_profile_czyta_repo(self):
        p = json.loads(self.f2("profile", "--repo", self.repo).stdout)
        self.assertEqual(p["package_manager"], "npm")
        self.assertIn("npm run test", p["verify"])
        self.assertIn("npm run lint", p["verify"])
        self.assertTrue(any("baseRef" in n for n in p["notes"]))
        self.assertIn("user_profile_path", p)
        # profil użytkownika nadpisuje: skill weryfikacji na żywo
        os.makedirs(os.path.dirname(p["user_profile_path"]))
        with open(p["user_profile_path"], "w") as f:
            json.dump({"live_verify_skill": "verify-admotiv", "notes": ["dev czyta prod"]}, f)
        p2 = json.loads(self.f2("profile", "--repo", self.repo).stdout)
        self.assertEqual(p2["live_verify_skill"], "verify-admotiv")
        self.assertIn("dev czyta prod", p2["notes"])


if __name__ == "__main__":
    unittest.main()
