/**
 * Calculator engine — percent key semantics per approved specification.
 *
 * % rules:
 *   after + or −       : percent of the first operand
 *   after × or ÷       : current operand / 100
 *   no pending operator: current operand / 100
 *   repeated %         : current displayed value / 100
 *   right after =      : last result / 100
 *   chained operations : sliding base (each % counts from the last result)
 *   percent > 100      : allowed
 *   division by zero   : Infinity (displayed as-is)
 *
 * Internal math is IEEE-754 double. Display: up to 10 significant digits,
 * trailing zeros stripped; Infinity / NaN shown verbatim.
 */

function format(n) {
  if (!isFinite(n)) return String(n);
  return String(Number(n.toPrecision(10)));
}

function Calculator() {
  this.reset();
}

Calculator.prototype.reset = function () {
  this.acc = null;
  this.op = null;
  this.cur = "0";
  this.typing = false;
  this.justOp = false;
  this.percentApplied = false;
  return this.display();
};

Calculator.prototype.display = function () {
  return this.cur;
};

Calculator.prototype.historyText = function () {
  if (this.op === null) return "";
  return format(this.acc) + " " + this.op + " " + this.cur;
};

Calculator.prototype.digit = function (d) {
  if (d === ".") {
    if (this.justOp || !this.typing) {
      this.cur = "0.";
      this.typing = true;
    } else if (this.cur.indexOf(".") === -1) {
      this.cur += ".";
    }
  } else if (this.justOp || !this.typing) {
    this.cur = d;
    this.typing = true;
  } else if (this.cur === "0" || this.cur === "-0") {
    this.cur = (this.cur.charAt(0) === "-" ? "-" : "") + d;
  } else {
    this.cur += d;
  }
  this.justOp = false;
  this.percentApplied = false;
  return this.display();
};

Calculator.prototype.negate = function () {
  const x = parseFloat(this.cur);
  // String(-0) is "0", so a fresh zero needs an explicit sign to stay negative
  this.cur = x === 0 ? (this.cur.charAt(0) === "-" ? "0" : "-0") : format(-x);
  this.typing = true; // digits typed after ± append to the signed number
  this.percentApplied = false;
  return this.display();
};

Calculator.prototype.compute = function (a, op, b) {
  if (op === "+") return a + b;
  if (op === "-") return a - b;
  if (op === "*") return a * b;
  if (op === "/") return a / b;
  return b;
};

Calculator.prototype.setOp = function (op) {
  if (this.op !== null && !this.justOp) {
    const r = this.compute(this.acc, this.op, parseFloat(this.cur));
    this.acc = r;
    this.cur = format(r);
  } else if (this.op === null) {
    this.acc = parseFloat(this.cur);
  }
  this.op = op;
  this.justOp = true;
  this.typing = false;
  this.percentApplied = false;
  return this.display();
};

Calculator.prototype.percent = function () {
  const x = parseFloat(this.cur);
  if ((this.op === "+" || this.op === "-") && !this.percentApplied) {
    this.cur = format(Math.abs(this.acc) * x / 100);
  } else {
    this.cur = format(x / 100);
  }
  this.percentApplied = true;
  this.typing = false;
  this.justOp = false;
  return this.display();
};

Calculator.prototype.equals = function () {
  if (this.op !== null) {
    const r = this.compute(this.acc, this.op, parseFloat(this.cur));
    this.cur = format(r);
    this.acc = null;
    this.op = null;
  }
  this.justOp = false;
  this.typing = false;
  this.percentApplied = false;
  return this.display();
};

Calculator.prototype.press = function (key) {
  if (key === "C") return this.reset();
  if (key === "%") return this.percent();
  if (key === "=") return this.equals();
  if (key === "+" || key === "-" || key === "*" || key === "/") return this.setOp(key);
  if (key === "±") return this.negate();
  return this.digit(key);
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = { Calculator, format };
}
