import fetch from "node-fetch";

const LEGO_SERVERS = [
  "http://bias-agent:8003/mcp",
  "http://ai-act-agent:8004/mcp",
  "http://unesco-agent:8005/mcp",
];

class EthicalLego {
  static async checkAll(prompt) {
    const promises = LEGO_SERVERS.map(async (server) => {
      const res = await fetch(server, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "bias_detector",
          params: { text: prompt },
        }),
      });
      return res.json();
    });

    const results = await Promise.allSettled(promises);
    const ethical = results.every(
      (r) => r.status === "fulfilled" && r.value.result?.ethical !== false,
    );

    return { ethical, results };
  }
}

module.exports = EthicalLego;

// Uso: EthicalLego.checkAll("test").then(console.log)
