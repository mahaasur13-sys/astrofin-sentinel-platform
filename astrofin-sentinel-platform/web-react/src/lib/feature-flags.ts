type FlagValue = boolean | number | string;

interface FlagDefinition {
  key: string;
  defaultValue: FlagValue;
  description: string;
}

interface RemoteFlags {
  flags: Record<string, FlagValue>;
  version: number;
}

const STORAGE_KEY = 'astrofin_feature_flags';
const REMOTE_CONFIG_URL = '/api/v1/feature-flags';

const FLAG_REGISTRY: FlagDefinition[] = [
  { key: 'enableExperimentalWidgets', defaultValue: false, description: 'Show experimental widgets in dashboard' },
  { key: 'enableCommandPalette', defaultValue: true, description: 'Enable Cmd+K command palette' },
  { key: 'enablePWA', defaultValue: true, description: 'Enable PWA install prompt' },
  { key: 'sseReconnectInterval', defaultValue: 30000, description: 'SSE reconnect max interval (ms)' },
  { key: 'maxDashboardWidgets', defaultValue: 12, description: 'Maximum number of dashboard widgets' },
  { key: 'enableRealTimeUpdates', defaultValue: true, description: 'Enable real-time SSE updates' },
  { key: 'enableRiskWarning', defaultValue: true, description: 'Show risk warning banner' },
];

class FeatureFlagManager {
  private overrides: Record<string, FlagValue> = {};
  private remoteCache: RemoteFlags | null = null;
  private initialized = false;

  init(persisted?: Record<string, FlagValue>): void {
    if (this.initialized) return;
    this.initialized = true;

    if (persisted) {
      this.overrides = { ...persisted };
    } else {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          this.overrides = JSON.parse(raw) as Record<string, FlagValue>;
        }
      } catch {
        // localStorage may be blocked
      }
    }

    if (import.meta.env.PROD) {
      this.fetchRemote().catch(() => {
        // remote config unavailable — use local overrides
      });
    }
  }

  private async fetchRemote(): Promise<void> {
    try {
      const resp = await fetch(REMOTE_CONFIG_URL);
      if (resp.ok) {
        this.remoteCache = (await resp.json()) as RemoteFlags;
      }
    } catch {
      // network unavailable
    }
  }

  get<T extends FlagValue = boolean>(key: string): T {
    const def = FLAG_REGISTRY.find((f) => f.key === key);

    // Override takes priority
    if (key in this.overrides) {
      return this.overrides[key] as T;
    }

    // Remote config (production only)
    if (this.remoteCache?.flags && key in this.remoteCache.flags) {
      return this.remoteCache.flags[key] as T;
    }

    // Default
    if (def) {
      return def.defaultValue as T;
    }

    console.warn(`[FeatureFlags] Unknown flag "${key}"`);
    return false as T;
  }

  setOverride(key: string, value: FlagValue): void {
    this.overrides[key] = value;
    this.persist();
  }

  removeOverride(key: string): void {
    delete this.overrides[key];
    this.persist();
  }

  resetAll(): void {
    this.overrides = {};
    this.remoteCache = null;
    this.persist();
  }

  private persist(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.overrides));
    } catch {
      // localStorage unavailable
    }
  }

  getAllFlags(): Record<string, FlagValue> {
    const result: Record<string, FlagValue> = {};
    for (const f of FLAG_REGISTRY) {
      result[f.key] = this.get(f.key);
    }
    return result;
  }
}

export const featureFlags = new FeatureFlagManager();
export { FLAG_REGISTRY };
export type { FlagDefinition, FlagValue };
