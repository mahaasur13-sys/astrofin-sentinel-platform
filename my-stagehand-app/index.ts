import "dotenv/config";
import { localBrowser, Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod/v4";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL,
});

process.on("uncaughtException", (e) => console.error("[UNCAUGHT]", e));
process.on("unhandledRejection", (e) => console.error("[UNHANDLED]", e));

function stripMarkdown(s: string): string {
  return s.replace(/```json\s*/gi, "").replace(/```\s*/g, "").trim();
}

function tryParseJson(s: string): any | null {
  const cleaned = stripMarkdown(s);
  const o = cleaned.indexOf("{");
  const a = cleaned.indexOf("[");
  const start = o === -1 ? a : a === -1 ? o : Math.min(o, a);
  if (start < 0) return null;
  const slice = cleaned.slice(start);
  const oe = slice.lastIndexOf("}");
  const ae = slice.lastIndexOf("]");
  const end = Math.max(oe, ae);
  try {
    return JSON.parse(end >= 0 ? slice.slice(0, end + 1) : slice);
  } catch {
    return null;
  }
}

function coerceAgainstSchema(raw: string, schema: any): any {
  const props = schema?.properties;
  if (props && typeof props === "object") {
    const keys = Object.keys(props);
    if (keys.length === 1) {
      return { [keys[0]]: raw.trim() };
    }
  }
  return { _raw: raw };
}

async function main() {
  console.log("[1] launching browser...");
  const browser = await localBrowser.launch({ headless: false });
  console.log("[2] browser launched");

  console.log("[3] creating Stagehand...");
  const stagehand = await Stagehand.create({
    browser,
    model: {
      generate: async (params: any) => {
        const { messages = [], systemPrompt, responseFormat } = params ?? {};

        const wantsJson =
          responseFormat?.type === "json_schema" ||
          responseFormat?.type === "json";

        const apiMessages: any[] = [];

        let sys = typeof systemPrompt === "string" ? systemPrompt : "";
        if (wantsJson && responseFormat?.schema) {
          sys +=
            "\n\nIMPORTANT: Respond with ONLY valid JSON matching this schema. " +
            "No markdown, no code fences, no explanation. Schema:\n" +
            JSON.stringify(responseFormat.schema);
        }
        if (sys) {
          apiMessages.push({ role: "system", content: sys });
        }

        for (const m of messages) {
          let content = m?.content;
          if (content && typeof content === "object" && !Array.isArray(content)) {
            content = content.text ?? JSON.stringify(content);
          }
          if (Array.isArray(content)) {
            content = content
              .map((p: any) => (typeof p === "string" ? p : p?.text ?? ""))
              .join("\n");
          }
          if (typeof content !== "string") content = JSON.stringify(content);
          apiMessages.push({ role: m?.role ?? "user", content });
        }

        const reqBody: any = {
          model: "aion-2.0",
          messages: apiMessages,
        };
        if (wantsJson) {
          reqBody.response_format = { type: "json_object" };
        }

        console.log(
          "[DEBUG] wants json:", wantsJson,
          "| body len:", JSON.stringify(reqBody).length,
        );

        let response;
        try {
          response = await openai.chat.completions.create(reqBody);
        } catch (err: any) {
          console.error("[LLM ERROR]", err?.status, err?.message);
          if (wantsJson) {
            console.log("[LLM FALLBACK] retry without response_format");
            delete reqBody.response_format;
            response = await openai.chat.completions.create(reqBody);
          } else {
            throw err;
          }
        }

        const raw = response.choices[0].message.content ?? "";
        console.log("[DEBUG] raw preview:", raw.slice(0, 300));

        if (wantsJson) {
          let parsed = tryParseJson(raw);
          if (!parsed) {
            console.log("[DEBUG] JSON parse failed, coercing plain text");
            parsed = coerceAgainstSchema(raw, responseFormat?.schema);
          }
          console.log(
            "[DEBUG] structuredContent:",
            JSON.stringify(parsed).slice(0, 300),
          );
          return {
            outputFormat: "json_schema",
            role: "assistant",
            content: [{ type: "text", text: raw }],
            structuredContent: parsed,
          };
        }

        return {
          outputFormat: "text",
          role: "assistant",
          content: [{ type: "text", text: raw }],
        };
      },
    },
  });
  console.log("[4] Stagehand created");

  try {
    console.log("[5] getting pages...");
    const pages = await browser.context.pages();
    const page = pages[0];
    if (!page) throw new Error("no page in browser context");
    console.log("[6] pages count:", pages.length);

    console.log("[7] navigating...");
    await page.goto("https://example.com", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    console.log("[8] current URL:", await page.url());

    console.log("[9] running extract...");
    const extractResult = await stagehand.extract(
      "Extract the main heading from the page.",
      z.object({ heading: z.string() }),
    );
    console.log("[10] Extract result:", JSON.stringify(extractResult, null, 2));

    console.log("[11] running observe...");
    const observeResult = await stagehand.observe(
      "What can I click on this page?",
    );
    console.log("[12] Observe result:", JSON.stringify(observeResult, null, 2));

    console.log("[13] running act...");
    const actResult = await stagehand.act("Click the 'Learn more' link.");
    console.log("[14] Act result:", JSON.stringify(actResult, null, 2));

    console.log("[15] current URL after act:", await page.url());
  } catch (e) {
    console.error("[ERROR in try block]", e);
  } finally {
    console.log("[16] closing...");
    await stagehand.close();
    await browser.close();
    console.log("[17] closed");
  }
}

main()
  .then(() => console.log("[DONE] main resolved"))
  .catch((err) => console.error("[FATAL]", err));
