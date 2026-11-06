# weights/vba: VBA lexer and interpreter (ids 384..447)

Hand-written. Not generated. Encoding: encodings/vba.md. Log: log/vba-agent.md; decisions VB1..VB9 in log/WORKLOG.md ("2026-11-06, Stage 9 groundwork"). Tests: tests/output/vba/test_vba.py (86 cases, black box).

Notes: lexer.md (384..399), parser.md (400..419), interp.md (420..429, 431, 435, 446), vi_bin.md (427), output.md (430, 436..438, 441, 442), strings.md (432, 439, 440, 443..445), vi_div.md (434), vi_scmp.md (433, 447).

**Status.** Lexer complete for the groundwork token set. Interpreter executes bytecode with Integer, Long, Double, String, Boolean, Date (as a number) values, frames, calls and For loops, Debug.Print and MsgBox. Parser (ids 400..419) built: VBA source runs end to end (lexer CHAIN 1 -> parser -> interpreter); limits in parser.md. / \ Mod ^ (vi_div 434, calls the math agent's fm_dv1 and fm_pw0) and string comparison (vi_scmp 433, vi_scl 447) built. Not yet: Like, Is, bitwise And/Or on general integers, objects (vi_obj 446 is the hook, ERR 438). Every id 384..447 is now in use.

**Shared conventions.** Every network whose output has a payload (more than 64 words) uses a block operation on every step (a block read of 0 words when nothing is needed), because the harness forwards the whole output after a non-block step (decision VB6). MUX_INT uses M = 2^23 for addresses, 1024 for network ids, 2^17 for characters; doubles are gated with mul layers only.
