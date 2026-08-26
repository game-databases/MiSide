// Test stub for Il2CppDumper.exe (v6.7.46 shape). Compiled on demand with
// the .NET Framework csc.exe; NO real tool bytes are shipped or run.
//
// Contract enforced by this stub (spec S3 / AC-7):
//   * refuses to run when its own-dir config.json still has RequireAnyKey
//     true -> proves the driver applied the headless config delta BEFORE
//     spawning (exit code 97 = invariant violation, never ignore);
//   * validates GameAssembly.dll + global-metadata.dat exist (exit 96);
//   * emits the five artifact shapes: dump.cs / il2cpp.h / script.json /
//     stringliteral.json / DummyDll\ with exactly 57 DLLs;
//   * logs argv + child cwd to MISIDE_STUB_LOG (cwd must equal the tool dir).

using System;
using System.IO;

[assembly: System.Reflection.AssemblyVersion("6.7.46.0")]
[assembly: System.Reflection.AssemblyFileVersion("6.7.46.0")]

class Il2CppDumperStub
{
    static void Log(string tool, string[] args)
    {
        var log = Environment.GetEnvironmentVariable("MISIDE_STUB_LOG");
        if (log == null) return;
        var sb = new System.Text.StringBuilder();
        sb.Append("{\"tool\":\"").Append(tool).Append("\",\"argv\":[");
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
        Log("il2cpp-dump", args);
        // Invariant: headless config delta must already be applied.
        string cfg = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
        if (File.Exists(cfg))
        {
            string body = File.ReadAllText(cfg);
            int k = body.IndexOf("\"RequireAnyKey\"", StringComparison.OrdinalIgnoreCase);
            if (k >= 0 && k + 60 < body.Length)
            {
                string around = body.Substring(k, Math.Min(60, body.Length - k)).ToLower();
                if (around.Contains("true"))
                {
                    Console.Error.WriteLine("STUB-INVARIANT: RequireAnyKey not set false before spawn");
                    return 97;
                }
            }
        }
        if (args.Length < 3) return 98;
        if (!File.Exists(args[0]) || !File.Exists(args[1]))
        {
            Console.Error.WriteLine("STUB: missing input dll/metadata");
            return 96;
        }
        string outDir = args[2];
        Directory.CreateDirectory(outDir);

        string assets = Environment.GetEnvironmentVariable("MISIDE_STUB_ASSETS") ?? ".";
        string tmpl = Path.Combine(assets, "dump_cs.template");
        File.Copy(tmpl, Path.Combine(outDir, "dump.cs"), true);
        using (var w = new StreamWriter(Path.Combine(outDir, "il2cpp.h")))
            for (int i = 0; i < 200; i++) w.WriteLine("// stub il2cpp.h line " + i);
        File.WriteAllText(Path.Combine(outDir, "script.json"),
            "{\"ScriptMethods\":[],\"ScriptMetadata\":[]}\n");
        File.WriteAllText(Path.Combine(outDir, "stringliteral.json"),
            "[{\"index\":0,\"value\":\"Pro Gamer\"},{\"index\":1,\"value\":\"MiniGame CarSpace\"}]\n");

        string dummy = Path.Combine(outDir, "DummyDll");
        Directory.CreateDirectory(dummy);
        string[] named = {
            "Assembly-CSharp.dll", "Assembly-CSharp-firstpass.dll", "mscorlib.dll",
            "System.dll", "UnityEngine.CoreModule.dll", "UnityEngine.UI.dll",
            "MagicaCloth.dll", "UIEffect.dll" };
        foreach (var n in named)
            File.WriteAllBytes(Path.Combine(dummy, n), new byte[] { 0x4D, 0x5A, 0x00, 0x01 });
        for (int i = 1; i <= 49; i++)
            File.WriteAllBytes(Path.Combine(dummy,
                string.Format("Stub{0:D2}.dll", i)), new byte[] { 0x4D, 0x5A, 0x00, 0x02 });
        return 0; // 8 named + 49 numbered = 57 DummyDlls
    }
}
