// Test stub for venv pip.exe. Compiled on demand with .NET Framework
// csc.exe. Makes stage S1 (`env`) fully offline and deterministic:
//
//   pip freeze   -> prints the pins file named by MISIDE_STUB_PIP_FREEZE
//                   (the test copies the sandbox's pipeline/requirements.txt
//                   there), so the driver's idempotency rule ("skip install
//                   when pip freeze already matches the pins") fires and no
//                   network is ever touched;
//   pip install  -> exit 0 (records a marker file beside the freeze file).
//
// Any other subcommand exits 0 quietly.

using System;
using System.IO;

class pipStub
{
    static int Main(string[] args)
    {
        bool freeze = false, install = false;
        foreach (var a in args)
        {
            var t = a.ToLower();
            if (t == "freeze") freeze = true;
            if (t == "install") install = true;
        }
        if (freeze)
        {
            var f = Environment.GetEnvironmentVariable("MISIDE_STUB_PIP_FREEZE");
            if (f != null && File.Exists(f))
            {
                Console.Out.Write(File.ReadAllText(f));
                return 0;
            }
            return 101; // test harness bug: freeze file not staged
        }
        if (install)
        {
            var f = Environment.GetEnvironmentVariable("MISIDE_STUB_PIP_FREEZE");
            if (f != null)
                File.WriteAllText(f + ".installed", "stub install ran\n");
            return 0;
        }
        return 0;
    }
}
