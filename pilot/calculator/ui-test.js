// UI wiring check: runs the page's key handler logic against the real engine,
// with minimal element stubs. Catches keys wired to methods that do not exist.
const fs = require("fs");
const { Calculator } = require("./calculator.js");

const html = fs.readFileSync("index.html", "utf8");
const keys = [...html.matchAll(/data-k="([^"]+)"/g)].map((m) => m[1]);
const scriptSrc = /<script src="([^"]+)"><\/script>/.exec(html);

const el = () => ({ value: "", textContent: "" });
const display = el();
const history = el();

function press(k, calc) {
  calc.press(k);
  display.value = calc.display();
  history.textContent = calc.historyText();
}

let fails = 0;
const check = (name, got, want) => {
  const ok = got === want;
  if (!ok) fails++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}: got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);
};

const calc = new Calculator();
display.value = calc.display();
history.textContent = calc.historyText();
check("initial display", display.value, "0");
check("initial history", history.textContent, "");
check("page loads engine file", scriptSrc && scriptSrc[1].split("?")[0], "calculator.js");

// every key present in the page must be handled without throwing
for (const k of keys) {
  try { press(k, calc); } catch (e) { fails++; console.log(`FAIL  key ${JSON.stringify(k)} threw: ${e.message}`); }
}
console.log(`keys in page: ${keys.length} (${keys.join(" ")})`);

// one full scenario through the page handler path
const c2 = new Calculator();
for (const k of ["2", "0", "0", "+", "1", "0", "%"]) press(k, c2);
check("200 + 10 % -> display", display.value, "20");
check("200 + 10 % -> history", history.textContent, "200 + 20");
press("=", c2);
check("200 + 10 % = -> display", display.value, "220");

console.log(fails ? `\nRESULT: ${fails} FAILED` : "\nRESULT: ALL PASS");
process.exit(fails ? 1 : 0);
