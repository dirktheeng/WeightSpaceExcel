# Encoding: VBA (program representation, tokens, bytecode, variables, frames, output)

Status: design and first build (memory relocated 2026-11-06: FILE_SCRATCH took 0x3B0000 up, decision F2), stage 9 groundwork. Owner: VBA agent (weights/vba, ids 384 to 447). Log: log/vba-agent.md; decisions VB1 to VB9 in log/WORKLOG.md ("2026-11-06, Stage 9 groundwork"). Related: encodings/value.md (TAG, PAY), encodings/control.md (state width, registers, calling convention), encodings/memory-map.md section 10 (VBA_STATE), harness/FORMAT.md (block operations).

## 1. Pipeline

A VBA module goes through three hand-written network groups, each a loop of harness steps:

1. **Lexer** (ids 384 to 399): source characters (one UTF-16 unit per word) to a token stream of 2-word tokens. Also registers every procedure name in the procedure table, so calls may precede definitions.
2. **Parser** (ids 400 to 419): token stream to bytecode (2-word instructions) for a stack machine, one token per step, shunting-yard expressions and a block stack for control structures.
3. **Interpreter** (ids 420 to 447): fetch, dispatch, execute bytecode on a value stack, with variables in frames, writing Debug.Print and MsgBox text into output buffers.

Each group is entered with a register setup documented below and ends in a halt (groundwork) or a return to (LR, LP) (later, when the VBE and Run Macro UI exist).

## 2. Memory layout (VBA_STATE 0x380000 to 0x3AFFFF)

| Name | Range | Contents |
|---|---|---|
| VGLOB | 0x380000 to 0x3800FF | globals: 0 DEBUG_LEN, 1 MSG_LEN, 2 ERRNUM (runtime error that stopped the program, 0 none), 3 PSTATUS (0 parsed, else parse error code), 4 NPROC (procedures registered by the lexer), 5 NTOK (tokens written, including the EOF token), 6 BCLEN (bytecode words), 7 PERRTOK (token index of a parse error) |
| SRC | 0x380100 to 0x387FFF | word 0x380100 = source length L; unit i (0-based) at 0x380101 + i |
| TOK | 0x388000 to 0x38FFFF | tokens [K, V], token j at 0x388000 + 2 j |
| BC | 0x390000 to 0x397FFF | bytecode [OP, ARG], instruction addresses are absolute word addresses |
| PROCT | 0x398000 to 0x3983FF | procedure records, 4 words at 0x398000 + 4 p: [key, entry address, slot count, parameter count] |
| SYMT | 0x398400 to 0x3987FF | local symbol table of the procedure being parsed: [key, info] pairs, info = slot + 4096 vt |
| CSTK | 0x398800 to 0x398BFF | parser block stack, 4 words per entry (section 6) |
| OSTK | 0x398C00 to 0x398FFF | parser operator stack, 1 word per entry: op + 64 prec (section 6) |
| VSTR | 0x399000 to 0x39BFFF | VBA string heap: record [length, unit 0, unit 1, ...], one unit per word |
| VSTACK | 0x3A0000 to 0x3A7FFF | frames and the value stack (section 5), 2 words per value |
| OBJT | 0x3A8000 to 0x3AFFFF | object table: reserved for the object model hook (section 8) |
| DEBUG_OUT | 0x39C000 to 0x39DFFF | Debug.Print text, one unit per word, lines end with LF (10) |
| MSG_OUT | 0x39E000 to 0x39FFFF | MsgBox prompts, one unit per word, each ends with LF (10) |

The source is placed one unit per word (not packed 3 per word like TEXT_HEAP) because the lexer reads one character per step anyway, a module file arrives one byte per word in the file transfer region, and unpacked strings let block reads and writes copy 8 units per step without repacking (decision VB2).

## 3. Values: Variant subtypes on value.md tags

A VBA value is the usual (TAG, PAY) pair. VarType(v) = TAG - 16 for every tag 16 to 63, except Empty, which uses the Excel blank tag 0 so that zeroed memory is a valid Empty variable with no initialisation pass (decision VB3).

| VBA type | VarType | TAG | PAY |
|---|---|---|---|
| Empty | 0 | 0 (16 reserved, never produced) | 0 |
| Null | 1 | 17 | 0 |
| Integer | 2 | 18 | integer in -32768..32767 |
| Long | 3 | 19 | integer in -2^31..2^31 - 1 |
| Single | 4 | 20 | double (single rounding not yet applied, limit) |
| Double | 5 | 21 | double |
| Currency | 6 | 22 | reserved (value times 10^4 as an integer) |
| Date | 7 | 23 | serial as Excel (days since 1899-12-30, fraction = time) |
| String | 8 | 24 | VSTR handle (address of the length word); "" is a record with length 0 |
| Object | 9 | 25 | OBJT handle, 0 = Nothing (reserved, section 8) |
| Error | 10 | 26 | error number |
| Boolean | 11 | 27 | -1 True, 0 False (VBA's values, so Not, And, Or work as integers) |
| Byte | 17 | 33 | 0..255 |

Declared types of variables use the same VarType numbers (vt); vt 0 (or 12) means Variant (no coercion on store).

**Numeric rank** (result type of + - *): Integer (also Boolean, Byte, Empty) < Long < Double (also Single, Date). Overflow of an Integer or Long result is runtime error 6, as VBA does for typed operands (VBA widens Variant operands instead; limit, section 9). `/` and `^` give Double; `\` and Mod round both operands half to even to Long and give Integer if both were Integer rank, else Long.

## 4. Lexer tokens

Token = [K, V].

| K | Meaning | V |
|---|---|---|
| 0 | end of file | 0 |
| 1 | end of statement (LF or ':') | 0 |
| 2 | identifier | KEY + 2^48 min(LEN, 31) |
| 3 | Integer literal | value |
| 4 | Long literal | value |
| 5 | Double literal | value |
| 6 | String literal | VSTR handle |
| 7 | Date literal | serial |
| 8 | Boolean literal | -1 or 0 |
| 10 to 14 | ( ) , ; . | 0 |
| 16 to 41 | operator (bytecode opcode, section 7) | precedence (section 6) |
| 64 to 127 | keyword (table below) | 0 |

KEY is the identifier folded to a base-64 integer of its last 8 characters: a..z (either case) are 1..26, digits 27..36, underscore 37; KEY = ((v1 64 + v2) 64 + v3) ...; exact below 2^48. Keywords are recognised when LEN <= 8 and KEY equals the keyword's constant (every digit of KEY is nonzero, so for LEN <= 8 the key determines the word). Identifiers longer than 8 characters that agree in their last 8 characters and in length collide (limit).

Keyword constants (computed by hand by Horner's rule, worksheet in log/vba-agent.md):

| K | Word | KEY | K | Word | KEY |
|---|---|---|---|---|---|
| 64 | Sub | 79170 | 86 | Exit | 1409620 |
| 65 | Function | 27846476075982 | 87 | Call | 791308 |
| 66 | End | 21380 | 88 | Debug | 68429127 |
| 67 | Dim | 16973 | 89 | Print | 273191828 |
| 68 | As | 83 | 90 | MsgBox | 14279255000 |
| 69 | If | 582 | 91 | Integer | 633844560210 |
| 70 | Then | 5275982 | 92 | Long | 3208071 |
| 71 | Else | 1361093 | 93 | Double | 4552139525 |
| 72 | ElseIf | 5575037510 | 94 | String | 20741395335 |
| 73 | Select | 20488147156 | 95 | Boolean | 153799905358 |
| 74 | Case | 791749 | 96 | Variant | 1513206584212 |
| 75 | For | 25554 | 97 | Single | 20555789061 |
| 76 | To | 1295 | 98 | Date | 1053957 |
| 77 | Step | 5062992 | 99 | Byte | 627973 |
| 78 | Next | 3692052 | 100 | Private | 1118995748101 |
| 79 | Each | 1315016 | 101 | Public | 17532764739 |
| 80 | In | 590 | 102 | ByVal | 40198220 |
| 81 | Do | 271 | 103 | ByRef | 40182086 |
| 82 | Loop | 3208144 | 104 | Option | 16379843534 |
| 83 | While | 388010757 | 105 | Explicit | 23656883565140 |
| 84 | Until | 356074060 | 106 | Const | 54322388 |
| 85 | Wend | 6050692 | | | |

Operator words become operator tokens: Mod 54212 (K 21), And 4996 (30), Or 978 (31), Xor 99282 (32), Eqv 21590 (33), Imp 37712 (34), Like 3183301 (35), Is 595 (36), Not 58324 (41). True 5317957 and False 100975813 become K 8 with V -1 and 0. Rem 74061 starts a comment.

**Lexical rules.** Spaces, tabs and CR are skipped. `'` and `Rem` start a comment to the end of the line (the LF still ends the statement). A `_` between tokens marks a line continuation: the next LF is skipped. Numbers: digits with optional `.` fraction and `E` or `D` exponent with sign, then an optional type suffix `%` (Integer), `&` (Long), `!` (Single, kept as Double), `#` (Double). A literal without point, exponent or suffix is Integer if it is at most 32767, Long if at most 2147483647, else Double (VBA's rule). At most 15 significant digits are kept (as Excel); conversion to a double is the parse agent's numconv (id 75), correctly rounded. Strings: `"..."` with `""` for a quote, copied to a new VSTR record. Dates: `#m/d/yyyy#` (US order, as VBA source always stores it) to the serial (section 4.1). `<>`, `<=`, `>=` are single tokens. An identifier just after the keyword Sub or Function is registered as procedure NPROC (PROCT record word 0 = its V).

### 4.1 Date serial

serial = days(y, m, d) - 693900 with days(y, m, d) = 365 y' + floor(y'/4) - floor(y'/100) + floor(y'/400) + floor((153 (m' - 3) + 2) / 5) + d, where y' = y - [m < 3] and m' = m + 12 [m < 3]. 693900 = days(1899, 12, 30) (hand computation in the log; check: 1/1/2000 gives 36526, Excel's serial). Times of day and two-digit years are not yet lexed (limit).

## 5. Variables, frames and the value stack

Variables live in frames on VSTACK, 2 words per slot (TAG, PAY). Registers during interpretation (output word numbers): IP 40 (address of the current instruction), SP 41 (next free word of VSTACK), FP 42 (address of slot 0 of the running procedure), VHT 43 (VSTR heap top), DOUT 44 (next free word of DEBUG_OUT), MOUT 45 (next free word of MSG_OUT), ERR 46, OP 47, ARG 48 (the instruction being executed), XHT 23 (Excel TEXT_HEAP top, the HT word that ev_totext uses). Words 49 to 63 and the T registers are handler scratch.

Frame of a procedure with n parameters and s slots (s counts slot 0, the parameters and every local), as built by the caller and CALL:

| Address | Contents |
|---|---|
| FP - 2, FP - 1 | link: return address, caller's FP |
| FP + 0, + 1 | slot 0: the Function result (Empty for a Sub) |
| FP + 2 i | slot i = parameter i (1..n), then locals (n + 1..s - 1) |
| FP + 2 s | first word of the expression stack of this procedure |

Calling sequence (bytecode): PUSH Empty (link space), PUSH Empty (slot 0), the n argument values, CALL p. CALL reads PROCT[p], sets FP = SP - 2 (n + 1), writes the link, zeroes the local slots n + 1..s - 1 (Empty) by block writes of 8 words, SP = FP + 2 s, IP = entry. RET moves slot 0 into the link position, so after the return the result is the top of the caller's stack (FP - 2 of the callee), restores IP and FP. A Sub call statement is followed by POP. Arguments are passed by value (ByRef is parsed and treated as ByVal; limit).

Dim with a declared type stores the type's initial value at the Dim (Integer 0, Long 0, Double 0, String "", Boolean False); an undeclared or Variant local is Empty from the CALL zeroing. Every STORE carries the declared type of its slot and coerces (section 7).

The program entry: the parser writes a 4-instruction prologue at BC + 0: PUSH Empty, PUSH Empty, CALL 0, END, so a run executes procedure 0 (the first procedure in the module). The interpreter starts at vi_start (id 420) with IP = 0x390000.

## 6. Parser structures

**As built (2026-11-06, decision VB10).** The operator stack (depth 6), the block stack (3 entries of 4 words), the local symbol table (8 keys and infos) and the procedure keys (8) are parser registers, not memory: the parser state is 136 words (block ops with K = 136) and every state network sees 3 tokens of lookahead. OSTK, SYMT and CSTK memory below stay reserved. Every procedure frame has 15 slots: slot 0, locals 1..8, hidden For slots 9..14 (h = 9 + 2 depth). Register map, networks and limits: weights/vba/parser.md. The design text below is the original plan; where it differs, parser.md is authoritative.

**Operator stack** (OSTK, 1 word per entry): E = op + 64 prec, op the opcode (or 10 for '(' marker, 7 for a call marker with the callee in a separate block stack entry), prec 0 for markers. The top is cached in a register. Shunting-yard: a binary operator with precedence p pops and emits every stacked operator with precedence >= p (all VBA binary operators are left associative); unary minus (op 40, prec 13) and Not (op 41, prec 6) are pushed without popping. Precedences: ^ 14, unary - 13, * / 12, \ 11, Mod 10, + - 9, & 8, comparisons = <> < <= > >= Like Is 7, Not 6, And 5, Or 4, Xor 3, Eqv 2, Imp 1 (VBA's order).

**Block stack** (CSTK, 4 words per entry): [kind, a, b, c].

| kind | Block | a | b | c |
|---|---|---|---|---|
| 1 | If | address of the pending JZ (0 when none) | head of the end-jump chain | 0 |
| 2 | For | loop top address | loop variable slot | hidden slot h (limit h, step h + 1); exit chain in the CSTK word 4 of the next entry, see parser notes |
| 3 | Do | loop top address | exit chain head | address of the pending JZ of a Do While/Until header (0 none) |
| 4 | While | loop top | 0 | pending JZ |
| 5 | Select | hidden slot h of the selector | pending JZ of the current Case | end-jump chain |
| 6 | Sub/Function | proc index | exit chain | kind (1 Sub, 2 Function) |

Forward jumps are linked through their ARG words (a chain ends at 0) and patched when the target is known, one read and one write per link.

## 7. Bytecode

Instruction = [OP, ARG] at BC + 2 k.

| OP | Name | ARG | Effect |
|---|---|---|---|
| 0 | END | 0 | write DEBUG_LEN, MSG_LEN, ERRNUM to VGLOB, halt |
| 1 | JMP | target address | IP = ARG |
| 2 | JZ | target | pop v; if v is false (0) IP = ARG |
| 3 | JNZ | target | pop v; if v is true (nonzero) IP = ARG |
| 4 | LOAD | slot | push slot |
| 5 | STORE | slot + 4096 vt | pop, coerce to vt, store |
| 6 | POP | 0 | drop the top value |
| 7 | CALL | proc index | section 5 |
| 8 | RET | 0 | section 5 |
| 9 | PRINT | 0 newline after, 1 no newline (trailing ';') | pop and append to DEBUG_OUT: numbers as " 5 " / "-5 " (sign space, trailing space), strings as is, Boolean True/False, Empty nothing |
| 10 | MSGBOX | 0 | pop, append CStr(v) and LF to MSG_OUT, push Integer 1 (vbOK) |
| 11 | FORCHK | 0 | pop step, limit, i; push Boolean (step >= 0 ? i <= limit : i >= limit) |
| 13 | OBJ | member code | object model hook (section 8) |
| 16 to 36 | binary operators | 0 | pop b, pop a, push a op b: 16 +, 17 -, 18 *, 19 /, 20 \, 21 Mod, 22 ^, 23 &, 24 =, 25 <>, 26 <, 27 <=, 28 >, 29 >=, 30 And, 31 Or, 32 Xor, 33 Eqv, 34 Imp, 35 Like, 36 Is |
| 40, 41 | NEG, NOT | 0 | unary on the top value |
| 64 + TAG | PUSH | PAY | push the literal (TAG, PAY) |

Runtime errors set ERR to the VBA error number and stop through vi_halt: 5 invalid procedure call, 6 overflow, 11 division by zero, 13 type mismatch, 51 internal error (bad opcode), 438 object hook not implemented. On Error is not yet supported. `/` `\` Mod `^` run in vi_div (434), string comparisons in vi_scmp/vi_scl (433, 447); see their notes.

## 8. Object model hook (later stages)

OP 13 (OBJ) is the single entry for member access: the parser will compile `Range("A1").Value = x`, `Cells(r, c)`, `For Each c In rng` into OBJ instructions whose ARG names a member code, with operands on the stack. The interpreter's dispatcher routes OP 13 to id 446 (vi_obj), which today sets ERR 438 and halts. The object model stage replaces id 446 with a network that reads the member code and calls the cell store (CELL_GET, CELL_SET, encodings/control.md) through the ordinary calling convention; Object values use TAG 25 with an OBJT handle. Range values cross into cells by converting VSTR strings to packed TEXT_HEAP strings (and back), which belongs to that stage.

## 9. Limits of the groundwork

Single rounding, Currency, Decimal, arrays, user types, ByRef, Optional, On Error, GoTo, With, Static, module-level variables, string to number coercion, bitwise And/Or/Xor on values other than 0 and -1, Like matching, string to number comparison ("5" = 5), Option Compare Text, Variant overflow widening and Date output formatting are not implemented. Each network note lists its own limits.
