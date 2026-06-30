-- =============================================================================
-- Kong Plugin — Tenant Routing via X-Tenant-ID Header
-- =============================================================================
-- Logic:
--   1. Extract X-Tenant-ID from request header
--   2. If missing → reject with 400 (tenant required)
--   3. If valid → inject upstream header X-Roma-Tenant and continue
--   4. Tenant whitelist stored in kong.db (consumers with custom_id = tenant_id)
--
-- Installation:
--   Place in /usr/local/kong/plugins/tenant-routing/handler.lua
--   Add to kong.conf: plugins = bundled,tenant-routing
-- =============================================================================

local kong = kong
local re_find = string.find
local re_match = ngx.re.match

local TenantRoutingHandler = {
  VERSION = "1.0.0",
  PRIORITY = 1000,  -- run before routing
}

-- Allowed tenant IDs (in production: query from kong.db or external service)
local ALLOWED_TENANTS = {
  ["tenant-alpha"] = true,
  ["tenant-beta"]  = true,
  ["tenant-gamma"] = true,
}

function TenantRoutingHandler:access(conf)
  -- Extract tenant ID from header
  local tenant_id = kong.request.get_header("X-Tenant-ID")

  if not tenant_id then
    kong.log.warn("X-Tenant-ID header missing")
    return kong.response.exit(400, {
      error = "X-Tenant-ID header required",
      hint  = "Include X-Tenant-ID: <your-tenant-id> in your request headers",
    })
  end

  -- Validate tenant against whitelist or consumer store
  local consumer, err = kong.client.get_consumer()
  if err then
    kong.log.err("Consumer lookup error: ", err)
  end

  -- Also allow consumer.custom_id as tenant identifier
  local valid = ALLOWED_TENANTS[tenant_id]
  if not valid and consumer and consumer.custom_id then
    valid = (consumer.custom_id == tenant_id)
  end

  if not valid then
    kong.log.warn("Unknown tenant: ", tenant_id)
    return kong.response.exit(403, {
      error = "Unknown tenant",
      hint  = "Tenant '" .. tenant_id .. "' is not registered. Contact sales.",
    })
  end

  -- Inject upstream header (backend receives real tenant context)
  kong.service.request.set_header("X-Roma-Tenant", tenant_id)
  kong.service.request.set_header("X-Roma-Tenant-ID", tenant_id)

  -- Also add to variable for logging/metrics
  kong.ctx.shared.tenant_id = tenant_id

  kong.log("Tenant routing: ", tenant_id)
end

-- Set upstream headers before proxying
function TenantRoutingHandler.header_filter(conf)
  -- Add tenant info to response headers for client visibility
  local tenant_id = kong.ctx.shared.tenant_id
  if tenant_id then
    kong.response.set_header("X-Tenant-ID", tenant_id)
  end
end

return TenantRoutingHandler
