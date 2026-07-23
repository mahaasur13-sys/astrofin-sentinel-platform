package slsa.release.v1
import future.keywords.if
allow if { input.oidc.verified == true }
allow if { input.source.deterministic == true }
allow if { input.source.file_count > 0 }
allow if { input.cvg_policy.hash != "" }
allow if { input.external_attestation == true }
deny if { not allow }