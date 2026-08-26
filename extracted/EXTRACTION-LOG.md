# L

```json pipeline-defaults
{
  "buildId": "19029065",
  "versionLabel": "0.93L",
  "unity": "2021.3.35f1",
  "metadataVersion": 29,
  "python": "3.14",
  "tools": {
    "ilspycmd": {
      "version": "ilspycmd: 11.0.0.9335",
      "artifact": "ilspycmd.11.0.0.9335-rc.nupkg",
      "commandPin": "ilspycmd -p -o <outdir> <dll>",
      "verified": true,
      "versionPin": "11.0.0.9335-rc",
      "channel": "nuget.org dotnet-tool 'ilspycmd' (--tool-path install, self-stored)",
      "package_sha256": "9e336464fb5554cf1ed1ac50bb41db2ce369ad875670b6024bc49123d063c816",
      "toolDir": "ILSpy",
      "runtime": "DOTNET_ROOT=<workroot>\\it1-dotnet10 injected by the stage"
    },
    "Il2CppDumper": {
      "version": "6.7.46",
      "artifact": "Il2CppDumper-net6-win-v6.7.46.zip"
    },
    "AssetStudioModCLI": {
      "version": "0.19.0.1",
      "artifact": "local rebuild of upstream aelurum/AssetStudioMod 6b66ec7 + recursive-type guard (natives from AssetStudioModCLI_net8_portable.zip)",
      "versionSource": "assembly FileVersion"
    }
  },
  "configDeltas": {
    "RequireAnyKey": false
  },
  "pipFreeze": [
    "archspec==0.2.6",
    "astc-encoder-py==0.1.12",
    "attrs==26.1.0",
    "brotli==1.2.0",
    "etcpak==0.9.15",
    "fmod_toolkit==0.1.3",
    "fsspec==2026.7.0",
    "lz4==4.4.5",
    "pillow==12.3.0",
    "pyfmodex==0.7.2",
    "texture2ddecoder==1.0.6",
    "tpk_ar==0.2.4",
    "unitypy==1.25.3"
  ],
  "entrypointCommit": "26e6add",
  "references": {
    "dumpCsLines": 288102,
    "dummyDllCount": 57
  }
}
```

## Run events

## 2026-08-24 — loc-run (9e0dc0f9)
<!-- event:loc-run:9e0dc0f9 -->
- `anomalies`: 0
- `categories_parsed`: 2210
- `legacy_files_handled`: 7
- `locales`: 34
- `records`: 180148
- `segments_marked_fffd`: 5

## 2026-08-24 — decompile-run (2682a4c6)
<!-- event:decompile-run:2682a4c6 -->
- `assemblies`: 163
- `failed`: 0
- `ilspycmd_version`: 'ilspycmd: 11.0.0.9335'
- `structure_types`: 6155
