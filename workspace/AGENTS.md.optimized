# AGENTS.md - Token-Optimized Workspace

## 🎯 Context Loading Strategy (OPTIMIZED)

**Default: Minimal context, load on-demand**

### Every Session (Always Load)
1. Read `SOUL.md` — Who you are (identity/personality)
2. Read `IDENTITY.md` — Your role/name

**Stop there.** Don't load anything else unless needed.

### Load On-Demand Only

**When user mentions memory/history:**
- Read `MEMORY.md`
- Read `memory/YYYY-MM-DD.md` (today only)

**When user asks about workflows/processes:**
- Read `AGENTS.md` (this file)

**When user asks about tools/devices:**
- Read `TOOLS.md`

**When user asks about themselves:**
- Read `USER.md`

**Never load automatically:**
- ❌ Documentation (`docs/**/*.md`) — load only when explicitly referenced
- ❌ Old memory logs (`memory/2026-01-*.md`) — load only if user mentions date
- ❌ Knowledge base (`knowledge/**/*`) — load only when user asks about specific topic
- ❌ Task files (`tasks/**/*`) — load only when user references task

### Context by Conversation Type

**Simple conversation** (hi, thanks, yes, quick question):
- Load: SOUL.md, IDENTITY.md
- Skip: Everything else
- **Token savings: ~80%**

**Standard work request** (write code, check file):
- Load: SOUL.md, IDENTITY.md, memory/TODAY.md
- Conditionally load: TOOLS.md (if mentions tools)
- Skip: docs, old memory logs
- **Token savings: ~50%**

**Complex task** (design system, analyze history):
- Load: SOUL.md, IDENTITY.md, MEMORY.md, memory/TODAY.md, memory/YESTERDAY.md
- Conditionally load: Relevant docs/knowledge
- Skip: Unrelated documentation
- **Token savings: ~30%**

## 🔥 Model Selection (ENFORCED)

**Simple conversations → HAIKU ONLY**
- Greetings, acknowledgments, simple questions
- Never use Sonnet/Opus for casual chat
- Override: `session_status model=haiku-4`

**Standard work → SONNET**
- Code writing, file edits, explanations
- Default model for most work

**Complex reasoning → OPUS**
- Architecture design, deep analysis
- Use sparingly, only when explicitly needed

## 💾 Memory (Lazy Loading)

**Daily notes:** `memory/YYYY-MM-DD.md`
- ✅ Load TODAY when user asks about recent work
- ❌ Don't load YESTERDAY unless explicitly needed
- ❌ Don't load older logs automatically

**Long-term:** `MEMORY.md`
- ✅ Load when user mentions "remember", "history", "before"
- ❌ Don't load for simple conversations

## 📊 Heartbeats (Optimized)

Use `heartbeat_optimizer.py` from token-optimizer skill:
- Check only what needs checking (not everything every time)
- Skip during quiet hours (23:00-08:00)
- Return `HEARTBEAT_OK` when nothing to report

## 🎨 Skills (Lazy Loading)

**Don't pre-read skill documentation.**

When skill triggers:
1. Read only the SKILL.md
2. Read only the specific reference files you need
3. Skip examples/assets unless explicitly needed

## 🚫 Anti-Patterns (What NOT to Do)

❌ Loading all docs at session start  
❌ Re-reading unchanged files  
❌ Using Opus for simple chat  
❌ Checking everything in every heartbeat  
❌ Loading full conversation history for simple questions  

✅ Load minimal context by default  
✅ Read files only when referenced  
✅ Use cheapest model for the task  
✅ Batch heartbeat checks intelligently  
✅ Keep context focused on current task  

## 📈 Monitoring

Track your savings:
```bash
python3 scripts/context_optimizer.py stats
python3 scripts/token_tracker.py check
```

## Integration

Run context optimizer before responding:
```bash
# Get recommendations
context_optimizer.py recommend "<user prompt>"

# Only load recommended files
# Skip everything else
```

---

**This optimized approach reduces token usage by 50-80% for typical workloads.**
