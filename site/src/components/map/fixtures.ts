/*
 * FIXTURES ONLY — never imported by a production route.
 *
 * `markers.jsonl` ships zero data rows until the M0 projection rerun lands
 * (map-viewer §0). These rows exist so the viewer's per-disposition states
 * (plotted pin / awaiting-transform chip / scene-granular list entry /
 * bounds-driven fit) can be exercised in tests and dev verification against
 * the CONTRACTED v2 shapes of spec §4.1 — nothing here is corpus data, every
 * slug is namespaced `fixture-`, and no file under extracted/ is touched.
 * A grep for "fixture-" across src/components/routes must stay EMPTY.
 */
import type { MarkerRow } from "@/data/contracts";

export const FIXTURE_SCENE = "level9";

export const FIXTURE_MARKERS: MarkerRow[] = [
  {
    marker_id: `${FIXTURE_SCENE}:cartridge:fixture-cap`,
    poi_id: `${FIXTURE_SCENE}:Trigger_Teleport_#10938`,
    layer: "location-scenes/Location7",
    kind: "cartridge",
    entity_kind: "cartridges",
    entity_slug: "fixture-cap-cartridge",
    icon: { source: null, fallback_state: "named-explicit-missing" },
    position: {
      x: 11.25,
      y: -7.8,
      z: 0,
      status: "projected",
    },
    placement: {
      mechanism: "hard",
      source_join: "save_key",
      scene_binding: FIXTURE_SCENE,
    },
    instance_census: { bare: 1, suffixed: 0 },
    links: {
      page_url: "/cartridges/fixture-cap-cartridge",
      focus_url: `/map?focus=cartridges:fixture-cap-cartridge&scene=${FIXTURE_SCENE}`,
    },
  },
  {
    marker_id: `${FIXTURE_SCENE}:profile:fixture-usual`,
    poi_id: null,
    layer: "location-scenes/Location15",
    kind: "profile_document",
    entity_kind: "profiles",
    entity_slug: "fixture-usual-profile",
    icon: { source: null, fallback_state: "named-explicit-missing" },
    position: {
      x: null,
      y: null,
      z: null,
      status: "scene-granular",
    },
    placement: {
      mechanism: "hard",
      source_join: "DS-5 placement",
      scene_binding: "level17",
    },
    links: {
      page_url: "/lore/profiles/fixture-usual-profile",
      focus_url: "/map?focus=profiles:fixture-usual-profile&scene=level17",
    },
  },
  {
    marker_id: `${FIXTURE_SCENE}:minigame_access:fixture-dance`,
    poi_id: null,
    layer: "location-scenes/Location7",
    kind: "minigame_access",
    entity_kind: "minigames",
    entity_slug: "fixture-dance-minigame",
    icon: { source: null, fallback_state: "named-explicit-missing" },
    position: {
      x: null,
      y: null,
      z: null,
      status: "awaiting-transform-stage",
    },
    placement: {
      mechanism: "hard",
      source_join: "minigame--scene-carrier",
      scene_binding: FIXTURE_SCENE,
    },
    instance_census: { controllers: 3, minigames: 4 },
    links: {
      page_url: "/minigames/fixture-dance-minigame",
      focus_url: `/map?focus=minigames:fixture-dance-minigame&scene=${FIXTURE_SCENE}`,
    },
  },
];

/** Registry entry WITH calibrated bounds — exercises the fit-to-bounds leg. */
export const FIXTURE_REGISTRY_ENTRY = {
  scene_id: FIXTURE_SCENE,
  role: "story" as const,
  label: "Fixture Scene Label",
  group: "story",
  bounds: [-30, -110, 14, 14] as [number, number, number, number],
  zoom: [1, 4] as [number, number],
  status: "awaiting-artwork" as const,
};

/** The same scene WITHOUT bounds — exercises mean-center fallback. */
export const FIXTURE_REGISTRY_ENTRY_NO_BOUNDS = {
  ...FIXTURE_REGISTRY_ENTRY,
  bounds: null,
};
