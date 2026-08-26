// Test stub for ilspycmd (ILSpy CLI 11.x shape). Compiled on demand with
// .NET Framework csc.exe; NO real tool bytes shipped or run.
//
// Contract: accepts an assembly (.dll) plus a project output dir (-o DIR),
// writes a decompiled source tree there. Assembly-CSharp gets the E1 recon
// anchors verbatim (GlobalLanguage.GetString + ConsoleInterface loader
// chain) so AC-11's anchor greps have something faithful to find.
// Logs argv to MISIDE_STUB_LOG.

using System;
using System.IO;

[assembly: System.Reflection.AssemblyVersion("11.0.0.9335")]
[assembly: System.Reflection.AssemblyFileVersion("11.0.0.9335")]

class ilspycmdStub
{
    static void Log(string[] args)
    {
        var log = Environment.GetEnvironmentVariable("MISIDE_STUB_LOG");
        if (log == null) return;
        var sb = new System.Text.StringBuilder();
        sb.Append("{\"tool\":\"ilspy\",\"argv\":[");
        for (int i = 0; i < args.Length; i++)
        {
            if (i > 0) sb.Append(',');
            sb.Append('"').Append(args[i].Replace("\\", "\\\\").Replace("\"", "\\\"")).Append('"');
        }
        sb.Append("]}\n");
        File.AppendAllText(log, sb.ToString());
    }

    static int Main(string[] args)
    {
        Log(args);
        // Version probe (driver pins the decompiler into EXTRACTION-LOG).
        foreach (var a in args)
            if (a == "--version" || a == "-v")
            {
                Console.Out.WriteLine("11.0.0.9335");
                return 0;
            }
        string asm = null;
        string outDir = null;
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "-o" && i + 1 < args.Length) { outDir = args[i + 1]; i++; continue; }
            if (args[i].ToLower().EndsWith(".dll") && File.Exists(args[i])) { asm = args[i]; continue; }
        }
        if (asm == null)
        {
            Console.Error.WriteLine("STUB: no input assembly found in argv");
            return 96;
        }
        if (outDir == null) outDir = Path.Combine(Path.GetDirectoryName(asm), "decompiled_out");
        Directory.CreateDirectory(outDir);

        string stem = Path.GetFileNameWithoutExtension(asm);
        string assets = Environment.GetEnvironmentVariable("MISIDE_STUB_ASSETS") ?? ".";
        string tmplPath = Path.Combine(assets, "decompiled_assembly.template");

        if (stem == "Assembly-CSharp" && File.Exists(tmplPath))
        {
            string body = File.ReadAllText(tmplPath);
            File.WriteAllText(Path.Combine(outDir, "GlobalLanguage.cs"), body);
            File.WriteAllText(Path.Combine(outDir, "ConsoleInterface.cs"), body);
        }
        using (var w = new StreamWriter(Path.Combine(outDir, "Types.cs")))
        {
            w.WriteLine("// decompiled by stub: " + stem);
            w.WriteLine("public class StubType" + stem.Replace("-", "_") + " {}");
        }
        using (var w = new StreamWriter(Path.Combine(outDir, stem + ".csproj")))
        {
            w.WriteLine("<Project Sdk=\"Microsoft.NET.Sdk\">");
            w.WriteLine("  <PropertyGroup><TargetFramework>netstandard2.0</TargetFramework></PropertyGroup>");
            w.WriteLine("</Project>");
        }
        return 0;
    }
}
