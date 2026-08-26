import { notFound } from "next/navigation";

import { Breadcrumbs } from "@/components/chrome/Breadcrumbs";
import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { DialogueBandLine } from "@/components/kit/DialogueBandLine";
import { NameTagPill } from "@/components/kit/NameTagPill";
import { readJsonl } from "@/data/contracts";
import type { Chrome } from "@/i18n/request";
import { getLocale } from "@/i18n/locales";
import { resolveLoc } from "@/data/resolveLoc";
import { desluggedLabel } from "./entityView";

/*
 * /dialogue/[container] — level-scoped transcript view (spec §5). The band
 * + name-tag pill + SPACE keycap pattern carries REAL lines: every rendered
 * row resolves this page's locale text from its text_ref pointer. Per-node
 * pages stay banned; speaker/choice scoping is an in-place filter canonical
 * to this unfiltered view.
 */

interface NodeRow {
  id: string;
  kind?: string;
  level?: string;
  speaker?: { display?: { en?: string }; theme?: string };
  text_ref?: { category: string; line_index: number };
}

export function DialogueGraphRoute({
  container,
  localePrefix,
  homeLabel,
  chrome,
  localeCode,
}: {
  container: string;
  localePrefix: string;
  homeLabel: string;
  chrome: Chrome;
  /** Page locale for line resolution (never another locale's text). */
  localeCode: string;
}) {
  if (!dialogueContainers().includes(container)) notFound();
  const { rows } = readJsonl<NodeRow>("data/dialogue/nodes.jsonl", "id");
  const levelNodes = rows.filter((r) => r.id.startsWith(`${container}:`));
  const def = getLocale(localeCode);
  // Lines resolve per-locale; a node whose cell is empty here renders no
  // line (the declared omission half of the filler policy).
  const lines = levelNodes
    .map((n) => ({
      node: n,
      text:
        n.text_ref && def
          ? resolveLoc(localeCode, {
              category: n.text_ref.category,
              line_index: n.text_ref.line_index,
            })
          : "",
    }))
    .filter((l) => l.text.trim().length > 0)
    .slice(0, 24);

  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        localePrefix={localePrefix}
        segments={["dialogue", container]}
        labels={{
          dialogue: chrome["nav.dialogue"],
          [container]: dialogueTitle(container, localeCode),
        }}
        homeLabel={homeLabel}
      />
      <h1 className="text-3xl font-bold uppercase tracking-wide">
        {dialogueTitle(container, localeCode)}
      </h1>
      <LcdTerminal className="w-fit">
        <span className="font-sans font-bold">{chrome["nav.dialogue"]}</span>{" "}
        <span>nodes:{levelNodes.length}</span>
      </LcdTerminal>
      <ul className="flex flex-col gap-2">
        {lines.map(({ node, text }) => {
          const speaker = node.speaker?.display?.en ?? node.speaker?.theme ?? "";
          return (
            <li key={node.id} className="flex items-center gap-3">
              <NameTagPill className="w-32 shrink-0 justify-center text-xs">
                {speaker}
              </NameTagPill>
              <DialogueBandLine
                speaker={speaker}
                text={text}
                openLabel={text.length > 64 ? `${text.slice(0, 61)}…` : text}
              />
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/**
 * The carrier's human title in THIS page's locale (VC-2 fix #5): the scene
 * dataset's own chapter name where it holds one; otherwise the id honestly
 * re-spaced ("Level 3") — never a bare raw id as a title.
 */
export function dialogueTitle(container: string, localeCode: string): string {
  const ptr = sceneChapterLocales().get(container);
  const named = ptr ? resolveLoc(localeCode, ptr) : "";
  return named || desluggedLabel(container) || container;
}

let chapterLocCache: Map<string, { category: string; line_index: number }> | null = null;
function sceneChapterLocales(): Map<string, { category: string; line_index: number }> {
  if (!chapterLocCache) {
    chapterLocCache = new Map();
    for (const s of readJsonl<{ scene_id: string; chapter_name_loc?: { category: string; line_index: number } | null }>(
      "data/scenes/scenes.jsonl",
      "scene_id"
    ).rows) {
      if (s.chapter_name_loc) chapterLocCache.set(s.scene_id, s.chapter_name_loc);
    }
  }
  return chapterLocCache;
}

/** generateStaticParams source for both trees. */
export function dialogueContainers(): string[] {
  const { rows } = readJsonl<{ id: string }>("data/dialogue/nodes.jsonl", "id");
  const levels = new Set<string>();
  for (const r of rows) levels.add(r.id.split(":")[0]);
  return [...levels].sort();
}
