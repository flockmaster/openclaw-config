import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

/**
 * Session Summary Hook
 *
 * On /new or /reset:
 * 1. Read recent conversation messages from session file
 * 2. Call LLM to generate a concise summary (not raw dump)
 * 3. Overwrite memory/last-session.md
 * 4. Inject summary into MEMORY.md (between markers) so the new session sees it
 */

const MARKER_START = "<!-- LAST-SESSION-START -->";
const MARKER_END = "<!-- LAST-SESSION-END -->";

// ---------------------------------------------------------------------------
// Message extraction
// ---------------------------------------------------------------------------

async function extractMessages(
  sessionFilePath: string,
  maxMessages = 50
): Promise<string[] | null> {
  try {
    const content = await fs.readFile(sessionFilePath, "utf-8");
    const lines = content.trim().split("\n");
    const messages: string[] = [];

    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        if (entry.type !== "message" || !entry.message) continue;

        const msg = entry.message;
        if (msg.role !== "user" && msg.role !== "assistant") continue;
        if (!msg.content) continue;

        // Skip system-injected user messages (bootstrap / inter-session)
        if (msg.provenance === "inter_session") continue;

        const text: string | undefined = Array.isArray(msg.content)
          ? msg.content.find((c: any) => c.type === "text")?.text
          : msg.content;

        if (!text) continue;
        // Skip slash commands and very short noise
        if (text.startsWith("/")) continue;
        // Skip extremely long system prompts
        if (text.length > 3000 && msg.role === "user") continue;

        // Truncate long messages to keep summary input manageable
        const truncated = text.length > 800 ? text.slice(0, 800) + "..." : text;
        messages.push(`[${msg.role}]: ${truncated}`);
      } catch {
        // skip malformed lines
      }
    }

    return messages.slice(-maxMessages);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Session file resolution (handles .reset.* rotation)
// ---------------------------------------------------------------------------

async function resolveSessionFile(
  sessionFilePath: string
): Promise<string | null> {
  // Try the file directly
  try {
    const stat = await fs.stat(sessionFilePath);
    if (stat.size > 100) return sessionFilePath;
  } catch {
    // file doesn't exist or is empty — try fallback
  }

  // Fallback: look for .reset.* siblings (the latest one)
  try {
    const dir = path.dirname(sessionFilePath);
    const base = path.basename(sessionFilePath);
    const resetPrefix = `${base}.reset.`;
    const files = await fs.readdir(dir);
    const resets = files
      .filter((f) => f.startsWith(resetPrefix))
      .sort();

    if (resets.length > 0) {
      return path.join(dir, resets[resets.length - 1]);
    }
  } catch {
    // ignore
  }

  return null;
}

// ---------------------------------------------------------------------------
// LLM summary generation
// ---------------------------------------------------------------------------

interface ProviderConfig {
  baseUrl: string;
  apiKey: string;
  api?: string;
}

async function generateSummary(
  conversationText: string,
  provider: ProviderConfig
): Promise<string | null> {
  const systemPrompt = `你是一个会话摘要助手。请根据以下对话内容，提炼出简洁的摘要。

要求：
1. 提取关键决策和结论（不超过5条）
2. 列出未完成的待办事项（如果有）
3. 记录重要的上下文信息（技术方案、配置变更等）
4. 整体不超过300字
5. 用中文输出
6. 用 markdown 格式

格式：
## 关键决策
- ...

## 待办事项
- ...

## 重要上下文
- ...

如果某个分类没有内容，省略该分类。`;

  try {
    const response = await fetch(`${provider.baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${provider.apiKey}`,
      },
      body: JSON.stringify({
        model: "qwen3-coder-plus",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: conversationText },
        ],
        max_tokens: 1024,
        temperature: 0.3,
      }),
      signal: AbortSignal.timeout(15_000), // 15s timeout
    });

    if (!response.ok) {
      console.error(
        `[session-summary] LLM call failed: ${response.status} ${response.statusText}`
      );
      return null;
    }

    const data = (await response.json()) as any;
    return data.choices?.[0]?.message?.content || null;
  } catch (err) {
    console.error(
      "[session-summary] LLM call error:",
      err instanceof Error ? err.message : String(err)
    );
    return null;
  }
}

// ---------------------------------------------------------------------------
// MEMORY.md: inject lightweight hint only (no summary content)
// ---------------------------------------------------------------------------

async function injectHintIntoMemory(
  workspaceDir: string
): Promise<void> {
  const memoryPath = path.join(workspaceDir, "MEMORY.md");

  let memoryContent: string;
  try {
    memoryContent = await fs.readFile(memoryPath, "utf-8");
  } catch {
    return;
  }

  // Already has hint? Skip (avoid duplication)
  if (memoryContent.includes(MARKER_START)) return;

  // Append minimal hint
  const hint = [
    "",
    MARKER_START,
    "⚡ 存在上次会话摘要（`memory/last-session.md`），新会话第一句话先问用户是否要延续。",
    MARKER_END,
  ].join("\n");

  memoryContent = memoryContent.trimEnd() + "\n" + hint + "\n";
  await fs.writeFile(memoryPath, memoryContent, "utf-8");
  console.log("[session-summary] Hint injected into MEMORY.md");
}

// ---------------------------------------------------------------------------
// Read openclaw config to get provider credentials
// ---------------------------------------------------------------------------

async function readConfig(stateDir: string): Promise<any | null> {
  try {
    const raw = await fs.readFile(
      path.join(stateDir, "openclaw.json"),
      "utf-8"
    );
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------

const handler = async (event: any) => {
  // Only trigger on /new or /reset
  if (event.type !== "command") return;
  if (event.action !== "new" && event.action !== "reset") return;

  // Only process main agent sessions
  const sessionKey: string = event.sessionKey || "";
  if (!sessionKey.startsWith("agent:main:")) return;

  try {
    const context = event.context || {};
    const sessionEntry =
      context.previousSessionEntry || context.sessionEntry || {};
    const rawSessionFile: string | undefined = sessionEntry.sessionFile;

    if (!rawSessionFile) {
      console.log("[session-summary] No session file in event context, skipping");
      return;
    }

    // Resolve actual file (may have been rotated)
    const sessionFile = await resolveSessionFile(rawSessionFile);
    if (!sessionFile) {
      console.log("[session-summary] Session file not found, skipping");
      return;
    }

    // Extract messages
    const messages = await extractMessages(sessionFile);
    if (!messages || messages.length < 3) {
      console.log(
        `[session-summary] Too few messages (${messages?.length ?? 0}), skipping`
      );
      return;
    }

    const conversationText = messages.join("\n\n");

    // Read config for LLM credentials
    const stateDir =
      process.env.OPENCLAW_STATE_DIR ||
      path.join(os.homedir(), ".openclaw");
    const config = await readConfig(stateDir);

    // Try LLM summary
    let summary: string | null = null;
    const provider = config?.models?.providers?.bailian as
      | ProviderConfig
      | undefined;

    if (provider) {
      summary = await generateSummary(conversationText, provider);
    }

    // Fallback: structured extraction without LLM
    if (!summary) {
      console.log("[session-summary] LLM unavailable, using raw fallback");
      summary = messages.slice(-10).join("\n\n");
    }

    // Write to last-session.md (overwrite, archival)
    const workspaceDir = path.join(stateDir, "workspace");
    const memoryDir = path.join(workspaceDir, "memory");
    await fs.mkdir(memoryDir, { recursive: true });

    const now = new Date(event.timestamp);
    const timeStr = now
      .toISOString()
      .replace("T", " ")
      .split(".")[0];

    const fileContent = [
      "# 上次会话摘要",
      "",
      `> 时间: ${timeStr} UTC`,
      `> 来源: ${context.commandSource || "unknown"}`,
      `> 会话: ${sessionEntry.sessionId || "unknown"}`,
      "",
      summary,
      "",
    ].join("\n");

    const targetPath = path.join(memoryDir, "last-session.md");
    await fs.writeFile(targetPath, fileContent, "utf-8");
    console.log(`[session-summary] Saved to ${targetPath.replace(os.homedir(), "~")}`);

    // Inject lightweight hint into MEMORY.md (not the summary itself)
    await injectHintIntoMemory(workspaceDir);
  } catch (err) {
    console.error(
      "[session-summary] Failed:",
      err instanceof Error ? err.message : String(err)
    );
  }
};

export default handler;
