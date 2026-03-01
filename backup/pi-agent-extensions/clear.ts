import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("clear", {
    description: "Clear context memory and start a fresh session",
    handler: async (_args, ctx) => {
      ctx.ui.notify("🧹 Clearing context — starting fresh session...", "info");
      await ctx.newSession();
    },
  });
}
