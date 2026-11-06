# Weight block notes: finisher (ids 212..215)

Hand-written. Not generated. Log: log/format-agent.md "finisher and General".

| Id | File | Step | Params |
|---|---|---|---|
| 212 | fx_fin | len = BP - 0xC800; numbers (kind <= 1) longer than W > 0 (fill not counted) become W '#'; a fill (N1 = 2) expands to W - len copies; sets up the pack loop; reads HEAP_TOP | 346 |
| 214 | fx_fin2 | writes the string length at h = HEAP_TOP; T2 = h, HW = h + 2 | 30 |
| 215 | fx_fin3 | HEAP_TOP = h + 2 + ceil(len / 3) (ceil by ROUND(len/3 + 1/3)) | 43 |
| 213 | fx_pack | per step takes at most one unit (fill char while filling, else the unit read last step, the marker starting the fill), adds it at slot pos (ACC += u 65536^pos), writes a full word, else reads the next unit, else flushes the last partial word and returns with A = (2, h) | 1440 |

**Derivation.** All choices are 0/1 gates; addresses and the next id are MUX_INT (B = 2^23); ACC uses a mul gate (values up to 2^48). Strings follow encodings/memory-map.md section 9 (reference count word left 0). Multi-role words: T0 holds the length in fx_fin..fx_fin3 and ACC in fx_pack (sequential, never both). Tests: test_full (8 cases: ######, fills, empty result), test_heap_top_advances.
