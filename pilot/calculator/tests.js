/**
 * Check scenarios for the % specification.
 *   node tests.js          — run all, print table, exit 1 on any failure
 */

const { Calculator } = require("./calculator");

function run(keys) {
  const c = new Calculator();
  let last = c.display();
  for (const k of keys) last = c.press(k);
  return last;
}

// Mandatory checks from the approved specification.
const MANDATORY = [
  ["200 + 10 %",      ["2","0","0","+","1","0","%","="], "220"],
  ["200 − 10 %",      ["2","0","0","-","1","0","%","="], "180"],
  ["200 × 10 %",      ["2","0","0","*","1","0","%","="], "20"],
  ["200 ÷ 10 %",      ["2","0","0","/","1","0","%","="], "2000"],
  ["100 + 10 % + 10 %", ["1","0","0","+","1","0","%","+","1","0","%","="], "121"],
  ["200 + 10 % %",    ["2","0","0","+","1","0","%","%","="], "200.2"],
  ["200 %",           ["2","0","0","%"], "2"],
  ["200 = %",         ["2","0","0","=","%"], "2"],
  ["200 ÷ 0 %",       ["2","0","0","/","0","%","="], "Infinity"],
  ["200 − 150 %",     ["2","0","0","-","1","5","0","%","="], "-100"],
  ["−200 + 10 %",     ["2","0","0","±","+","1","0","%","="], "-180"],
  ["0 + 10 %",        ["0","+","1","0","%","="], "0"],
];

// Cases derived from the same rules (not listed in the specification table).
const DERIVED = [
  ["−200 − 10 %",     ["2","0","0","±","-","1","0","%","="], "-220"],
  ["200 × 10 % %",    ["2","0","0","*","1","0","%","%","="], "0.2"],
  ["200 ÷ 10 % %",    ["2","0","0","/","1","0","%","%","="], "200000"],
  ["1 ÷ 3",           ["1","/","3","="], "0.3333333333"],
  ["0 ÷ 0 %",         ["0","/","0","%","="], "NaN"],
  ["2 = %",           ["2","=","%"], "0.02"],
  ["50 % + 10 %",     ["5","0","%","+","1","0","%","="], "0.55"],
  ["100 + 10 % = %",  ["1","0","0","+","1","0","%","=","%"], "1.1"],
  ["± 200 + 10 %",    ["±","2","0","0","+","1","0","%","="], "-180"],  // ± FIRST
  ["2.5 × 10 %",      ["2",".","5","*","1","0","%","="], "0.25"],
];

function check(set, label) {
  let failed = 0;
  const rows = [];
  for (const [expr, keys, expected] of set) {
    const actual = run(keys);
    const ok = actual === expected;
    if (!ok) failed++;
    rows.push({ expr, actual, expected, status: ok ? "PASS" : "FAIL" });
  }
  console.log("\n" + label);
  console.log("expr".padEnd(18), "actual".padEnd(16), "expected".padEnd(16), "status");
  for (const r of rows) {
    console.log(r.expr.padEnd(18), r.actual.padEnd(16), r.expected.padEnd(16), r.status);
  }
  return { failed, total: rows.length };
}

const m = check(MANDATORY, "MANDATORY (specification table)");
const d = check(DERIVED, "DERIVED (same rules, not in the table)");

const failed = m.failed + d.failed;
console.log(`\nmandatory: ${m.total - m.failed}/${m.total} passed`);
console.log(`derived:   ${d.total - d.failed}/${d.total} passed`);
console.log(failed === 0 ? "RESULT: ALL PASS" : `RESULT: ${failed} FAILED`);
process.exit(failed === 0 ? 0 : 1);
