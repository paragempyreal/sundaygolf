import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

// Configure axios defaults
axios.defaults.withCredentials = true;

export interface FulfilConfig {
  mode: "live" | "test";
  live: {
    subdomain: string;
    apiKey: string;
  };
  test: {
    subdomain: string;
    apiKey: string;
  };
}

export interface ShipHeroConfig {
  mode: "live" | "test";
  live: {
    refreshToken: string;
    oauthUrl: string;
    apiBaseUrl: string;
    defaultWarehouseId?: string;
  };
  test: {
    refreshToken: string;
    oauthUrl: string;
    apiBaseUrl: string;
    defaultWarehouseId?: string;
  };
}

export interface SystemConfig {
  pollIntervalMinutes: number;
}

export interface EmailConfig {
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpPassword: string;
  smtpUseTls: boolean;
  smtpUseSsl: boolean;
  fromEmail: string;
  fromName: string;
  isActive: boolean;
}

export interface ProductSyncConfig {
  mode: "live" | "test";
}

export interface ConfigResponse {
  fulfil: FulfilConfig;
  shiphero: ShipHeroConfig;
  system: SystemConfig;
}

export interface User {
  id: string;
  username: string;
  email: string;
  isAdmin: boolean;
  isActive: boolean;
  created_at?: string;
  updated_at?: string;
}

class ConfigService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
  });

  setAuthToken(token: string) {
    this.api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  }

  async getConfig(): Promise<ConfigResponse> {
    try {
      const response = await this.api.get("/api/config");
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to fetch configuration"
        );
      }
      throw new Error("Failed to fetch configuration");
    }
  }

  async updateFulfilConfig(config: FulfilConfig): Promise<void> {
    try {
      await this.api.put("/api/config/fulfil", {
        mode: config.mode,
        live: {
          subdomain: config.live.subdomain,
          apiKey: config.live.apiKey,
        },
        test: {
          subdomain: config.test.subdomain,
          apiKey: config.test.apiKey,
        },
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message ||
            "Failed to update Fulfil configuration"
        );
      }
      throw new Error("Failed to update Fulfil configuration");
    }
  }

  async updateShipHeroConfig(config: ShipHeroConfig): Promise<void> {
    try {
      await this.api.put("/api/config/shiphero", {
        mode: config.mode,
        live: {
          refreshToken: config.live.refreshToken,
          oauthUrl: config.live.oauthUrl,
          apiBaseUrl: config.live.apiBaseUrl,
          defaultWarehouseId: config.live.defaultWarehouseId || "",
        },
        test: {
          refreshToken: config.test.refreshToken,
          oauthUrl: config.test.oauthUrl,
          apiBaseUrl: config.test.apiBaseUrl,
          defaultWarehouseId: config.test.defaultWarehouseId || "",
        },
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message ||
            "Failed to update ShipHero configuration"
        );
      }
      throw new Error("Failed to update ShipHero configuration");
    }
  }

  async updateSystemConfig(config: SystemConfig): Promise<void> {
    try {
      await this.api.put("/api/config/system", {
        pollIntervalMinutes: config.pollIntervalMinutes,
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message ||
            "Failed to update system configuration"
        );
      }
      throw new Error("Failed to update system configuration");
    }
  }

  async testFulfilConnection(): Promise<{ success: boolean; message: string }> {
    return { success: false, message: "Not supported" };
  }

  async testShipHeroConnection(): Promise<{
    success: boolean;
    message: string;
  }> {
    return { success: false, message: "Not supported" };
  }

  // Email Configuration Methods
  async getEmailConfig(): Promise<EmailConfig> {
    try {
      const response = await this.api.get("/api/config/email");
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to fetch email configuration"
        );
      }
      throw new Error("Failed to fetch email configuration");
    }
  }

  async updateEmailConfig(config: EmailConfig): Promise<void> {
    try {
      await this.api.put("/api/config/email", {
        smtpHost: config.smtpHost,
        smtpPort: config.smtpPort,
        smtpUsername: config.smtpUsername,
        smtpPassword: config.smtpPassword,
        smtpUseTls: config.smtpUseTls,
        smtpUseSsl: config.smtpUseSsl,
        fromEmail: config.fromEmail,
        fromName: config.fromName,
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message ||
            "Failed to update email configuration"
        );
      }
      throw new Error("Failed to update email configuration");
    }
  }

  async testEmailConfig(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await this.api.post("/api/config/email/test");
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        return {
          success: false,
          message: error.response?.data?.message || "Email test failed",
        };
      }
      return {
        success: false,
        message: "Email test failed",
      };
    }
  }

  // User management methods
  async getUsers(): Promise<User[]> {
    try {
      const response = await this.api.get("/api/users");
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to fetch users"
        );
      }
      throw new Error("Failed to fetch users");
    }
  }

  async createUser(userData: {
    username: string;
    email: string;
    password: string;
    isAdmin?: boolean;
  }): Promise<{ message: string; user: User }> {
    try {
      const response = await this.api.post("/api/users", userData);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to create user"
        );
      }
      throw new Error("Failed to create user");
    }
  }

  // Product sync
  async getProductSyncStatus(): Promise<any> {
    try {
      const response = await this.api.get("/api/product-sync/status");
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to fetch product sync status"
        );
      }
      throw new Error("Failed to fetch product sync status");
    }
  }

  async getProductSyncLogs(
    page = 1,
    perPage = 20,
    q?: string,
    mode?: "live" | "test"
  ): Promise<{
    items: any[];
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  }> {
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      if (q && q.trim()) params.set("q", q.trim());
      if (mode) params.set("mode", mode);
      const response = await this.api.get(
        `/api/product-sync/logs?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to fetch product sync logs"
        );
      }
      throw new Error("Failed to fetch product sync logs");
    }
  }

  // Product sync mode methods
  async getProductSyncMode(): Promise<ProductSyncConfig> {
    try {
      const response = await this.api.get("/api/config/product-sync/mode");
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to fetch product sync mode"
        );
      }
      throw new Error("Failed to fetch product sync mode");
    }
  }

  async updateProductSyncMode(mode: "live" | "test"): Promise<void> {
    try {
      await this.api.put("/api/config/product-sync/mode", { mode });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to update product sync mode"
        );
      }
      throw new Error("Failed to update product sync mode");
    }
  }

  async checkProductSync(code: string, mode: "live" | "test"): Promise<any> {
    try {
      const params = new URLSearchParams();
      params.set("code", code);
      params.set("mode", mode);
      const response = await this.api.get(
        `/api/product-sync/check?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.message || "Failed to check product sync"
        );
      }
      throw new Error("Failed to check product sync");
    }
  }
}

export const configService = new ConfigService();
