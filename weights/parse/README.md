# weights/parse: entry parser and formula compiler (ids 64..79)

Hand-written. Not generated. Log: log/parse-agent.md; decisions P1..P5 in log/WORKLOG.md (2026-11-06, parse agent).

## Call contract (weights/kernel/commit.md)
Entry is id 78 with PC 0, A = (2, HS) (typed text, packed heap string), address register (AS, AR1, AC1) = home cell, LR, LP = return link. Exit is always through 79, which returns to (LR, LP) with:
- constant: STATUS 0, A = (TAG, PAY) (number, boolean, error, or text), P1 = 0;
- formula: STATUS 0, A = (0, 0), P1 = formula record address (record words 0 text handle HS, 1 token stream address, 2 token count excluding the end token);
- rejected: STATUS 1 (A, P1 meaningless).
L0..L23 are preserved (spill and restore). The parser may move HEAP_TOP (string literals, apostrophe text) and FORMULA_TOP (accepted formulas only).

## Network ids and flow
| id | file | role |
|---|---|---|
| 78 | spill | save L12..L23 to RET_STACK (12 steps) |
| 64 | pentry | read length, HEAP_TOP, FORMULA_TOP; call unpack; dispatch on first char |
| 65 | unpack | heap text -> char buffer 0x2800 + i (4 steps per 3 chars) |
| 66 | idle | formula lexer between tokens |
| 67 | lnum | number lexer (formula and entry mode) |
| 68 | lword | names, functions, booleans, references, ranges |
| 69 | wordend | classify a word, pack reference operands |
| 70 | lstr | string literal / text builder |
| 71 | lerr | error literal after # |
| 72 | lcmp | second char of <= <> >= |
| 73 | parse | shunting-yard decision step |
| 74 | pemit | emit, pop and finish phases; formula record |
| 75 | numconv | decimal to double in one pass |
| 76 | const | constant entry prefix, suffix, sign, text fallback |
| 77 | ckey | constant TRUE, FALSE and error keywords |
| 79 | restore | reload L12..L23, return |

## Register map (output word numbers; input index = word + 1)
| word | name | role |
|---|---|---|
| 7 | PC | phase inside the current parse network |
| 12 | STATUS | 0 ok, 1 rejected |
| 13, 14 | A | result value |
| 15, 16, 17 | NEG, PCT, PAR | constant entry: minus or '(' seen, % seen, '(' open |
| 22 | HT | heap top while parsing |
| 23 | EM | entry mode (1 constant entry, 0 formula) for lnum and lstr |
| 24 | HS | handle of the typed text |
| 26 | P1 | result formula record |
| 27 | FT | formula record address (old FORMULA_TOP) |
| 29 | I | index of the current character |
| 30 | LEN | text length |
| 31 | RDOK | 1 when input word 0 holds character I |
| 32, 33 | E, J | parser: expecting an operand; just after a function '(' or a comma |
| 34 | SP | operator stack depth (stack at 0x2000 + SP) |
| 35, 36 | TOPK, TOPA | cached stack top: kind (opcode, 1 paren, 64 + fid function, 0 bottom) and argument count |
| 37, 38 | OUTP, NT | next token address, tokens written |
| 39 | PP | x0 holds a popped stack word |
| 52..55 | TK, TO, TV, TV2 | token handed to the parser: kind, opcode, operand, second corner operand |
| 56..63 | X0..X7 | token scratch; role set by the lexer state (see each note) |

**Multi-role words.** X0..X7 serve one token at a time. Their roles are exclusive by lexer state: lnum (M, SIG, FRAC, DROP, EXPV, ESGN, return id, return PC), lword (KEY, KLEN, COL, ROW, RS, FLAGS, OPND1, CSn), lstr (SACC, SK, SL, SW, SH), lerr and ckey (KEY, KLEN), unpack (j, word address, c1, c2). Every state network that starts a token sets the X words it reads (idle, const, pentry), so a stale value from another role is never read. TK holds the '(' flag between lword and wordend, then the token kind. Crosstalk coverage: tests/output/parse/test_parse.py mixes numbers, names, references, strings and errors in one formula.

## Common blocks (retyped in each network)
- END = step(I - LEN + 0.5); c_eff = relu(c - 2^17 (END + 1 - RDOK)), so classes are all 0 at end of text or with no character.
- Character class thresholds t_k = step(c_eff - k + 0.5); a class [a, b) is t_a - t_b (exact 0/1).
- AND of n binaries: step(sum - n + 0.5). Gates are mutually exclusive by construction, so sums of gates are 0/1.
- MUX_INT (encodings/primitives.md): relu(v + M g - M) with M = 2^23 for integers below 2^22 (2^27 for 10 ROW in lword, 2^40 for packed operands); doubles and large keys are gated with mul layers.
- Output assembly: computed rows plus slices of the input, joined by concat in word order (pass-through costs no parameters).
- Address field when no memory operation: left at a computed value (encodings/address.md A2 asks for 0 only for readable traces; it has no effect).

## Totals
16 networks, 18,132 dense parameters (rows x cols + rows, zeros included). Steps measured by tests/output/parse/test_parse.py: "5" 44, "abc" 43, "=1+2*3" 83, "=SUM(A1:A3)*2" 101. Spill plus restore is 25 of these.

## Limits (all networks)
2047 characters per entry. Numbers need |decimal exponent| <= 22 after normalisation (1E+308, 1E-200 are rejected in formulas, text as entries). Not yet supported: whole column or row references (A:A, 3:3), sheet prefixes, the union (,) and intersection (space) operators, array constants, structured references, defined names (a name compiles to #NAME?), function names longer than 10 characters (they compile to the unknown function, fid 0), #GETTING_DATA.
