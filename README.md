# Bryan Cruz

**Java backend and developer tooling.** I build local-first tools that hold up under the conditions that break the naive version.

Computer science student at San Jose State University, finishing up and looking for new-grad work. Most of what I build starts as something I actually needed, then keeps going past the point where it works — into the part where I find out what breaks it. I care about proving a change is an improvement before claiming it is: measure the baseline, change one thing, measure again. The repos below are where that reasoning lives, and their READMEs are written for someone who wants to read the decisions, not just the feature list.

**What I'm looking for:** new-grad / junior Software Engineer roles — Java backend, full-stack, or developer tooling. Bay Area, on-site or remote. If you're hiring, email me at **isdisbryan@gmail.com** and I'll reply the same day.

---

### 🛠️ Tech I build with

![Java](https://img.shields.io/badge/Java-21-5d86b4?style=flat-square)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.3-5d86b4?style=flat-square)
![JavaFX](https://img.shields.io/badge/JavaFX-21-5d86b4?style=flat-square)
![Python](https://img.shields.io/badge/Python-3-5d86b4?style=flat-square)
![React](https://img.shields.io/badge/React-19-5d86b4?style=flat-square)
![TypeScript](https://img.shields.io/badge/TypeScript-5d86b4?style=flat-square)

---

### 🚀 What I'm building

**[CreatorFlow](https://github.com/Bryancruzcb/creatorflow)** — a local-first release-preflight
tool for small Roblox teams
> Before a team publishes an update, CreatorFlow checks every changed asset against a snapshot of
> the last version that worked and returns a deterministic **PASS / BLOCKED** record naming exactly
> which version to roll back to. A hardened `127.0.0.1` desktop bridge pairs with a Roblox Studio
> plugin and reads only normalized KeyframeSequence data, so the animation never leaves Studio.
>
> The part I'd point at: the motion engine was Java and had to run in the browser. I ported it to
> TypeScript and **proved numeric parity against the Java reference before touching any of the
> math**, so every later change was measured against a provably identical baseline. Banded DTW and
> a position de-weight then went in as separately graded changes — false positives fell from
> **14.4% to 4.1%**, at a cost of 1.7 points of recall (94.1% → 92.4%, entirely two mirror cases).
> Pinned by 23 golden vectors and a parity test that fails if the port drifts.
>
> Java 21 · JavaFX · SQLite · React 19 + TypeScript · Luau · CI on every push

**[second-brain-tools](https://github.com/Bryancruzcb/second-brain-tools)** — a local knowledge
engine for my own Obsidian vault
> Reads my notes off my own machine, draws the links between them as a 3D graph, and answers
> questions about them against a model running locally — nothing I've written is ever sent
> anywhere.
>
> The part I'd point at: parsing a cloud-synced vault correctly *and* fast. The Rust core reads
> files sequentially on purpose — parallel reads saturate OneDrive's File Provider daemon and stall
> the whole scan — while fanning the CPU-bound link and tag extraction across cores with Rayon. It
> also detects OneDrive placeholder files (metadata on disk, content not downloaded) and serves
> them read-only from the last index instead of erroring out. I only found that by running it on my
> own vault and watching it stall.
>
> Rust + Rayon · FastAPI · ChromaDB · Ollama / Qwen · Next.js + React Three Fiber

**[Signal Path](https://github.com/Bryancruzcb/signal-path)** — a browser-local workspace I built
to run my own school and job search
> **[Open the live app →](https://bryancruzcb.github.io/signal-path/)**
>
> A single-page React/TypeScript app running course prep, a four-term academic plan, six career
> tracks, and an application tracker out of one tab. Everything persists in the browser — no
> account, no backend, no analytics.
>
> The part I'd point at: the focus timer stays correct where a naive `setInterval` countdown
> doesn't. It derives from an absolute deadline and re-syncs on `focus` and `visibilitychange`, so
> a throttled background tab snaps back to the true value. On `beforeunload`/`pagehide` it writes
> the finished session straight to localStorage — React state can't flush during unload — then
> nulls the deadline so the `pagehide` that follows `beforeunload` can't bank the same session
> twice.
>
> React 19 · TypeScript · Vite · localStorage

---

### 📫 Reach me

- Email: **isdisbryan@gmail.com**
- LinkedIn: [linkedin.com/in/bryan-cruz](https://www.linkedin.com/in/bryan-cruz-078819279/)
- GitHub: [@Bryancruzcb](https://github.com/Bryancruzcb)

<sub>Currently job hunting — if you're hiring junior engineers and want to see how I work, my repos are the résumé.</sub>
