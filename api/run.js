const DEFAULT_TOPIC = "AI agents for SMBs";
const DEFAULT_BATCH = "W25";

module.exports = async function handler(req, res) {
  if (req.method === "OPTIONS") {
    setCors(res);
    return res.status(200).json({ ok: true });
  }

  setCors(res);
  try {
    const body = parseBody(req);
    const topic = String(body.topic || DEFAULT_TOPIC).slice(0, 160);
    const ycBatch = String(body.yc_batch || body.batch || DEFAULT_BATCH).slice(0, 40);
    const limit = clamp(Number(body.limit || 10), 1, 15);
    const rows = await fetchYCCompanies(ycBatch);
    const analyses = rows
      .map((row) => ({ row, relevance: relevance(row, topic), freshness: freshness(row) }))
      .filter((item) => item.relevance > 0 || ycBatch)
      .sort((a, b) => b.relevance - a.relevance || b.freshness - a.freshness)
      .slice(0, limit)
      .map((item) => analyze(item.row, topic))
      .sort((a, b) => b.score - a.score);

    return res.status(200).json({
      topic,
      yc_batch: ycBatch,
      generated_at: new Date().toISOString(),
      llm_mode: "never",
      warnings: [],
      results: analyses
    });
  } catch (error) {
    return res.status(500).json({ error: error.message || "Pipeline failed" });
  }
};

function parseBody(req) {
  if (!req.body) return {};
  if (typeof req.body === "object") return req.body;
  try {
    return JSON.parse(req.body);
  } catch {
    return {};
  }
}

function setCors(res) {
  res.setHeader("access-control-allow-origin", "*");
  res.setHeader("access-control-allow-methods", "GET,POST,OPTIONS");
  res.setHeader("access-control-allow-headers", "content-type");
  res.setHeader("cache-control", "no-store");
}

async function fetchYCCompanies(batch) {
  const slug = batchToSlug(batch);
  const url = slug
    ? `https://yc-oss.github.io/api/batches/${slug}.json`
    : "https://yc-oss.github.io/api/companies/all.json";
  const response = await fetch(url, {
    headers: { accept: "application/json", "user-agent": "venture-pipeline-vercel/0.1" }
  });
  if (!response.ok) throw new Error(`YC source failed: ${response.status}`);
  return response.json();
}

function batchToSlug(value) {
  const raw = String(value || "").trim().toLowerCase();
  const match = raw.match(/^(winter|w|summer|s|spring|sp|fall|f)[\s-]?(\d{2}|\d{4})$/);
  if (!match) return null;
  const season = {
    w: "winter",
    winter: "winter",
    s: "summer",
    summer: "summer",
    sp: "spring",
    spring: "spring",
    f: "fall",
    fall: "fall"
  }[match[1]];
  let year = Number(match[2]);
  if (year < 100) year += 2000;
  return `${season}-${year}`;
}

function relevance(row, topic) {
  const terms = expandedTerms(topic);
  const text = searchText(row).toLowerCase();
  let score = 0;
  for (const term of terms) {
    if (text.includes(term)) score += 3;
  }
  if (terms.has("ai") && /\bai\b|artificial intelligence/.test(text)) score += 6;
  if ((terms.has("agent") || terms.has("agents")) && /agent|automate|workflow/.test(text)) score += 5;
  if ((terms.has("smb") || terms.has("smbs")) && /small business|smb|local/.test(text)) score += 4;
  return score;
}

function freshness(row) {
  let score = 0;
  if (/202[4-9]|winter 2025|summer 2025/i.test(String(row.batch || ""))) score += 5;
  if (row.top_company) score += 3;
  if (String(row.status || "").toLowerCase() === "active") score += 2;
  if (row.team_size) score += 1;
  return score;
}

function analyze(row, topic) {
  const oneLiner = clean(row.one_liner || sentence(row.long_description, 180));
  const text = searchText(row).toLowerCase();
  const topicTerms = expandedTerms(topic);
  const scoreBreakdown = score(row, oneLiner, text, topicTerms);
  const total = Object.values(scoreBreakdown).reduce((sum, value) => sum + value, 0);
  const status = String(row.status || "").toLowerCase();
  const recommendation =
    ["acquired", "public", "inactive", "dead"].includes(status)
      ? "Pass"
      : total >= 80
        ? "Take a meeting"
        : total >= 60
          ? "Watch"
          : "Pass";

  const candidate = {
    name: clean(row.name),
    website: row.website || null,
    one_liner: oneLiner,
    source_url: row.url || row.api,
    traction_signals: traction(row)
  };

  const rationale =
    recommendation === "Take a meeting"
      ? `Score ${total}/100 clears the meeting bar because the company shows a recent, vertical workflow wedge with enough source-level traction to justify founder diligence.`
      : recommendation === "Watch"
        ? `Score ${total}/100 suggests the company matches parts of the thesis, but the public evidence is not yet strong enough for immediate partner time.`
        : `Score ${total}/100 does not clear the bar for this seed thesis, or the company appears non-investable based on current status/source evidence.`;

  const team = `YC ${row.batch || "company"}, team size ${row.team_size || "not listed"}, ${row.stage || "stage not listed"}, ${row.industry || "industry not listed"}. Founder backgrounds need verification from sources beyond the YC record.`;
  const product = `${candidate.name}: ${clean(row.long_description || oneLiner)}`;
  const market = `The beachhead is ${row.industry || "the listed market"}. Tags/signals: ${(row.tags || row.industries || []).slice(0, 5).join(", ") || "none listed"}.`;
  const risks = [
    "Founder backgrounds are not fully available from the selected source.",
    recommendation === "Take a meeting"
      ? "Main risk is whether the workflow becomes a durable platform rather than a narrow tool."
      : "The current evidence does not yet prove urgency, buyer pull, or differentiated distribution."
  ];
  const changeMind = [
    "Verified founder backgrounds showing deep domain access or technical advantage.",
    "Customer proof: named SMB or vertical customers, retention, expansion, or quantified ROI.",
    "Evidence that the workflow expands into a system of record or labor-replacement wedge."
  ];

  return {
    ...candidate,
    recommendation,
    score: total,
    score_breakdown: { ...scoreBreakdown, total },
    rationale,
    team,
    product,
    market,
    risks,
    change_mind: changeMind,
    confidence: "medium",
    analyst: "vercel-deterministic",
    memo: renderMemo(candidate, { recommendation, total, rationale, team, product, market, risks, changeMind })
  };
}

function score(row, oneLiner, text, topicTerms) {
  const hasAI = /\bai\b|agent|automation|automate|workflow|artificial intelligence/.test(text);
  const hasVertical = /billing|clinic|dental|healthcare|insurance|legal|logistics|operations|revenue|sales|support/.test(text);
  const hasSMB = /smb|small|business|merchant|local/.test(text);
  const recent = /202[4-9]|winter 2025|summer 2025/i.test(String(row.batch || ""));
  return {
    team: Math.min(20, 6 + (row.team_size ? 4 : 0) + (row.team_size >= 2 && row.team_size <= 10 ? 4 : 0) + (hasAI ? 3 : 0) + (row.top_company ? 3 : 0)),
    product: Math.min(25, (oneLiner.split(/\s+/).length >= 4 ? 6 : 0) + (hasAI ? 7 : 0) + (hasVertical ? 5 : 0) + (overlap(text, topicTerms) ? 7 : 0)),
    market: Math.min(20, (hasSMB ? 6 : 0) + (hasVertical ? 6 : 0) + (/revenue|billing|claims|payments|sales|support|operations/.test(text) ? 5 : 0) + (hasAI ? 3 : 0)),
    traction: Math.min(20, (recent ? 8 : 0) + (String(row.status || "").toLowerCase() === "active" ? 4 : 0) + (row.stage ? 2 : 0) + (row.isHiring ? 3 : 0) + (row.team_size >= 2 ? 2 : 0) + (row.top_company ? 3 : 0)),
    risk: Math.max(0, Math.min(15, 15 - (["acquired", "public", "inactive", "dead"].includes(String(row.status || "").toLowerCase()) ? 6 : 0) - (!row.website ? 3 : 0)))
  };
}

function traction(row) {
  return [
    row.batch ? `YC batch: ${row.batch}` : null,
    row.stage ? `Stage: ${row.stage}` : null,
    row.status ? `Status: ${row.status}` : null,
    row.isHiring ? "Hiring signal on YC profile" : null,
    row.team_size ? `Team size listed as ${row.team_size}` : null
  ].filter(Boolean);
}

function renderMemo(candidate, analysis) {
  return `# ${candidate.name}\n\n**Call:** ${analysis.recommendation}\n**Score:** ${analysis.total}/100\n\n${analysis.rationale}\n`;
}

function expandedTerms(topic) {
  const terms = new Set(String(topic || "").toLowerCase().match(/[a-z0-9]+/g) || []);
  if (terms.has("ai") || terms.has("agent") || terms.has("agents")) {
    ["ai", "agent", "agents", "artificial", "intelligence", "automation", "automate", "workflow"].forEach((term) => terms.add(term));
  }
  if (terms.has("smb") || terms.has("smbs")) {
    ["smb", "smbs", "small", "business", "businesses", "local", "merchant"].forEach((term) => terms.add(term));
  }
  return terms;
}

function overlap(text, terms) {
  for (const term of terms) {
    if (text.includes(term)) return true;
  }
  return false;
}

function searchText(row) {
  return clean([row.name, row.one_liner, row.long_description, row.industry, row.subindustry, ...(row.industries || []), ...(row.tags || [])].join(" "));
}

function sentence(value, limit) {
  const text = clean(value || "");
  return text.length <= limit ? text : `${text.slice(0, limit - 1).trim()}...`;
}

function clean(value) {
  return String(value || "")
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[–—]/g, " - ")
    .replace(/\s+/g, " ")
    .trim();
}

function clamp(value, min, max) {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, value));
}
