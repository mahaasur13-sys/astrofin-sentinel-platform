-- =============================================================================
-- Kong Plugin — Dynamic Branding Injection
-- =============================================================================
-- Logic:
--   1. Read X-Tenant-ID from request/response context
--   2. Inject inline <style> and <link> into HTML responses
--   3. CSS variables per tenant: primary color, logo URL, company name
--
-- Installation:
--   Place in /usr/local/kong/plugins/tenant-branding/handler.lua
--   Add to kong.conf: plugins = bundled,tenant-routing,tenant-branding
-- =============================================================================

local kong = kong
local re_gsub = string.gsub
local re_match = ngx.re.match

local BrandingInjectionHandler = {
  VERSION = "1.0.0",
  PRIORITY = 500,  -- run after tenant-routing (1000)
}

-- Per-tenant branding configuration
local TENANT_BRANDING = {
  ["tenant-alpha"] = {
    primary_color = "#FF6B35",
    logo_url      = "https://cdn.roma.com/logos/alpha.svg",
    company_name  = "Alpha Corp",
    favicon       = "https://cdn.roma.com/logos/alpha-favicon.ico",
    css_overrides = "",
  },
  ["tenant-beta"] = {
    primary_color = "#4A90D9",
    logo_url      = "https://cdn.roma.com/logos/beta.svg",
    company_name  = "Beta Inc",
    favicon       = "https://cdn.roma.com/logos/beta-favicon.ico",
    css_overrides = "",
  },
  ["tenant-gamma"] = {
    primary_color = "#2ECC71",
    logo_url      = "https://cdn.roma.com/logos/gamma.svg",
    company_name  = "Gamma LLC",
    favicon       = "https://cdn.roma.com/logos/gamma-favicon.ico",
    css_overrides = "",
  },
}

-- Default branding (no tenant or unknown)
local DEFAULT_BRAND = {
  primary_color = "#6366F1",
  logo_url      = "https://cdn.roma.com/logos/roma-default.svg",
  company_name  = "ROMA",
  favicon       = "https://cdn.roma.com/logos/roma-favicon.ico",
  css_overrides = "",
}

function BrandingInjectionHandler:header_filter(conf)
  -- Inject CSS variables into <head> via response header
  local tenant_id = kong.ctx.shared.tenant_id or "default"
  local brand = TENANT_BRANDING[tenant_id] or DEFAULT_BRAND

  -- Encode brand config as base64 JSON (decoded by client-side JS or proxy)
  local brand_header = string.format(
    '{"tenant":"%s","primary":"%s","logo":"%s","name":"%s"}',
    tenant_id, brand.primary_color, brand.logo_url, brand.company_name
  )

  kong.response.set_header("X-Tenant-Branding", brand_header)
end

function BrandingInjectionHandler:body_filter(conf)
  -- Only process HTML responses
  local content_type = kong.response.get_header("Content-Type") or ""
  if not re_match(content_type, "text/html", "jo") then
    return
  end

  local chunk = kong.response.get_chunk()
  if not chunk then
    return
  end

  local tenant_id = kong.ctx.shared.tenant_id or "default"
  local brand = TENANT_BRANDING[tenant_id] or DEFAULT_BRAND

  -- CSS injection template
  local css_inject = string.format([[
<style id="roma-tenant-branding">
  :root {
    --tenant-primary: %s;
    --tenant-logo: url('%s');
    --tenant-name: '%s';
  }
  .tenant-logo { background-image: var(--tenant-logo) !important; }
  .tenant-primary-bg { background-color: var(--tenant-primary) !important; }
  .tenant-primary-text { color: var(--tenant-primary) !important; }
  .tenant-primary-border { border-color: var(--tenant-primary) !important; }
  .tenant-name { content: var(--tenant-name) !important; }
  %s
</style>
]], brand.primary_color, brand.logo_url, brand.company_name, brand.css_overrides)

  -- Inject after <head> opening tag
  local modified = re_gsub(chunk, "<head>", "<head>" .. css_inject, "jo")

  kong.response.set_chunk(modified)
end

return BrandingInjectionHandler
