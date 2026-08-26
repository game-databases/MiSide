import { MapViewer } from "@/components/map/MapViewer";
import { scenes } from "@/data/contracts";
import type { Chrome } from "@/i18n/request";
import {
  defaultSceneId,
  mapChromeStrings,
  markersByScene,
  switcherGroups,
} from "./mapView";

/*
 * /map — SSG shell + Leaflet island (spec §7; map-viewer §5). Registry,
 * switcher grouping, marker partition and popover titles are built
 * server-side (routes/mapView.ts) from the scenes dataset + markers.jsonl
 * ONLY; the island receives plain props and fetches nothing at runtime.
 * Zero marker rows today → the viewer renders its designed explicit-missing
 * states honestly until the M0 projection rerun lands.
 */
export function MapRoute({
  chrome,
  localePrefix,
  localeCode,
}: {
  chrome: Chrome;
  /** Site locale code (labels resolve per locale server-side). */
  localeCode: string;
  localePrefix: string;
}) {
  const chromeStrings = mapChromeStrings(chrome);
  const unlabeled = chromeStrings.chapterUnlabeled;
  return (
    <MapViewer
      mode="full"
      groups={switcherGroups(localeCode, unlabeled, chromeStrings.roleLabels)}
      sceneIds={scenes().map((s) => s.scene_id)}
      initialSceneId={defaultSceneId(localeCode, unlabeled)}
      markersByScene={markersByScene(localePrefix, localeCode)}
      chromeStrings={chromeStrings}
    />
  );
}
