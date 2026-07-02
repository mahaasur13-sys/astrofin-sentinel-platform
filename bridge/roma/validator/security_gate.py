"""Security Gate — validates ROMA JSON before compilation."""



class SecurityGate:
    """
    Filters ROMA JSON for dangerous patterns.
    Returns {passed: bool, reason: str}
    """

    BLOCKED_IMAGES = [
        "privileged",
        ":latest",  # no floating tags
    ]

    BLOCKED_COMMANDS = [
        "rm -rf /",
        "mkfs",
        "dd if=",
        ">/etc/",
        "> /dev/sd",
    ]

    def validate(self, roma_json: dict) -> dict:
        """Run all security checks. Return pass/fail."""
        if not self._check_structure(roma_json):
            return {"passed": False, "reason": "Invalid ROMA JSON structure"}

        security = roma_json.get("security", {})

        # 1. Privileged pod check
        if security.get("privileged"):
            return {"passed": False, "reason": "Privileged pods are blocked"}

        # 2. Host network check
        if security.get("host_network"):
            return {"passed": False, "reason": "hostNetwork is blocked"}

        # 3. HostPath mount check
        if security.get("host_path_allowed"):
            return {"passed": False, "reason": "hostPath mounts are blocked"}

        # 4. Dangerous commands in DAG
        for step in roma_json.get("dag", []):
            cmd = step.get("command", "")
            if any(dangerous in cmd for dangerous in self.BLOCKED_COMMANDS):
                return {
                    "passed": False,
                    "reason": f"Dangerous command detected in step {step.get('id')}: {cmd[:50]}",
                }

        # 5. GPU over-allocation check
        resources = roma_json.get("resources", {})
        if resources.get("gpu_required"):
            vram = resources.get("vram_gb", 0)
            if vram > 10.5:
                return {
                    "passed": False,
                    "reason": f"VRAM request {vram}GB exceeds RTX 3060 safe limit (10.5GB)",
                }

        # 6. Image tag validation
        for step in roma_json.get("dag", []):
            image = step.get("image", "")
            if any(bad in image for bad in self.BLOCKED_IMAGES):
                return {
                    "passed": False,
                    "reason": f"Unsafe image tag in step {step.get('id')}: {image}",
                }

        return {"passed": True, "reason": "All security checks passed"}


# ── Singleton ────────────────────────────────────────────────────────────────
security_gate = SecurityGate()