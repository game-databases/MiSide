// Test stub for AssetStudioModCLI.exe (0.19.0.0 shape). Compiled on demand
// with .NET Framework csc.exe; NO real tool bytes shipped or run.
//
// Contract enforced by this stub:
//   * input path must be argv[1] and must exist, else the E1 verbatim error
//     "Error: Input path was empty." + exit 95;
//   * MEASURE-FIRST GATE (R-E1-1): a container named level*/sharedassets*
//     is refused (exit 99) unless census/sweep-budget.json ALREADY exists
//     at MISIDE_STUB_SWEEP_BUDGET -> proves the driver writes the budget
//     before any full-sweep invocation;
//   * failure injection: MISIDE_STUB_FAIL_CONTAINERS="level0,sharedassets0"
//     makes matching containers exit 42 (drives LEDGER-mode tests);
//   * -m dump: emits typed tab-indented .txt dumps; resources.assets gets
//     exactly 993 incl. DataAchievements.txt (E1 shape), others get 7;
//   * asset-list XML: emitted whenever the invocation mentions
//     --export-asset-list / xml / asset-list tokens (AC-8 accepts either
//     same-pass or second-pass mechanism — stub serves both);
//   * logs argv + cwd to MISIDE_STUB_LOG (argv-order regression evidence).

using System;
using System.IO;

[assembly: System.Reflection.AssemblyVersion("0.19.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("0.19.0.0")]

class AssetStudioModCLIStub
{
    static string ArgValue(string[] args, string flag)
    {
        for (int i = 0; i < args.Length - 1; i++)
            if (args[i] == flag) return args[i + 1];
        return null;
    }

    static void Log(string[] args)
    {
        var log = Environment.GetEnvironmentVariable("MISIDE_STUB_LOG");
        if (log == null) return;
        var sb = new System.Text.StringBuilder();
        sb.Append("{\"tool\":\"assetstudio\",\"argv\":[");
        for (int i = 0; i < args.Length; i++)
        {
            if (i > 0) sb.Append(',');
            sb.Append('"').Append(args[i].Replace("\\", "\\\\").Replace("\"", "\\\"")).Append('"');
        }
        var cwd = Directory.GetCurrentDirectory().Replace("\\", "\\\\");
        sb.Append("],\"cwd\":\"").Append(cwd).Append("\"}\n");
        File.AppendAllText(log, sb.ToString());
    }

    static int Main(string[] args)
    {
        Log(args);
        // NOTE: .NET Main(args) EXCLUDES the exe name — args[0] is the
        // input container (input-path-first, E1 deviation 5).
        if (args.Length < 1)
        {
            Console.Error.WriteLine("Error: Input path was empty.");
            return 95;
        }
        string input = args[0];
        if (!File.Exists(input))
        {
            Console.Error.WriteLine("Error: Input path was empty.");
            return 95;
        }
        string stem = Path.GetFileNameWithoutExtension(input);
        string lower = stem.ToLower();

        // Failure injection (LEDGER-mode driver behavior under test).
        var failList = Environment.GetEnvironmentVariable("MISIDE_STUB_FAIL_CONTAINERS");
        if (failList != null && ("," + failList.ToLower() + ",").Contains("," + lower + ","))
        {
            Console.Error.WriteLine("STUB-INJECTED failure for " + stem);
            return 42;
        }

        // Measure-first gate (R-E1-1): the FIRST level-family invocation is
        // allowed to be the measure probe itself (spec order: probe the
        // smallest levelN, then record sweep-budget.json, then sweep).
        // Every SUBSEQUENT level*/sharedassets* invocation requires the
        // budget file to already exist.
        if (lower.StartsWith("level") || lower.StartsWith("sharedassets"))
        {
            var budget = Environment.GetEnvironmentVariable("MISIDE_STUB_SWEEP_BUDGET");
            var probeMarker = budget == null ? null : budget + ".probe-seen";
            bool budgetExists = budget != null && File.Exists(budget);
            if (!budgetExists)
            {
                if (probeMarker == null)
                {
                    Console.Error.WriteLine("STUB-INVARIANT: no sweep budget path configured");
                    return 99;
                }
                if (File.Exists(probeMarker))
                {
                    Console.Error.WriteLine("STUB-INVARIANT: sweep-budget.json missing before level/sharedassets sweep");
                    return 99;
                }
                Directory.CreateDirectory(Path.GetDirectoryName(probeMarker));
                File.WriteAllText(probeMarker, "probe\n");
            }
        }

        string mode = ArgValue(args, "-m") ?? "dump";
        string outDir = ArgValue(args, "-o") ?? ".";
        bool xmlWanted = false;
        foreach (var a in args)
        {
            var t = a.ToLower();
            if (t.Contains("export-asset-list") || t.Contains("asset-list")) xmlWanted = true;
        }
        for (int i = 0; i < args.Length - 1; i++)
            if (args[i].ToLower() == "--export-asset-list" && args[i + 1].ToLower() == "xml")
                xmlWanted = true;

        Directory.CreateDirectory(outDir);

        if (mode == "dump" || mode.Contains("dump"))
        {
            int count = lower.Contains("resources") ? 993 : 7;
            string assets = Environment.GetEnvironmentVariable("MISIDE_STUB_ASSETS") ?? ".";
            for (int i = 0; i < count; i++)
            {
                string name = (i == 0 && lower.Contains("resources"))
                    ? "DataAchievements.txt"
                    : string.Format("MBType{0:D3}.txt", i);
                string path = Path.Combine(outDir, name);
                if (name == "DataAchievements.txt")
                    File.Copy(Path.Combine(assets, "DataAchievements.txt"), path, true);
                else
                {
                    using (var w = new StreamWriter(path))
                    {
                        w.WriteLine("MonoBehaviour Base");
                        w.WriteLine("\tPPtr<GameObject> m_GameObject");
                        w.WriteLine("\t\tint m_FileID = 0");
                        w.WriteLine("\t\tSInt64 m_PathID = " + (1000 + i));
                        w.WriteLine("\tstring m_Name = \"\"");
                        w.WriteLine("\tbool EveryEnable = False");
                        w.WriteLine("\tstring NameFile = \"Menu\"");
                        w.WriteLine("\tSInt32 StringNumber = " + (i % 26));
                        w.WriteLine("\tUInt8 m_Enabled = 1");
                    }
                }
            }
        }

        if (xmlWanted)
        {
            using (var w = new StreamWriter(Path.Combine(outDir, stem + ".xml")))
            {
                w.WriteLine("<?xml version=\"1.0\" encoding=\"utf-8\"?>");
                w.WriteLine("<Assets>");
                w.WriteLine("  <Asset Name=\"" + stem + "\" Type=\"TextAsset\" PathID=\"1\" Container=\"" + stem + "\" />");
                w.WriteLine("</Assets>");
            }
        }
        return 0;
    }
}
