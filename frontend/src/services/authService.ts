import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

export interface LoginResponse {
  user: {
    id: string;
    username: string;
    email: string;
    isAdmin: boolean;
    isActive: boolean;
    created_at?: string;
    updated_at?: string;
  };
  token: string;
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

class AuthService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
  });

  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await this.api.post("/api/login", {
        username,
        password,
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.message || "Login failed");
      }
      throw new Error("Login failed");
    }
  }

  async validateToken(token: string): Promise<User> {
    try {
      const response = await this.api.get("/api/validate-token", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error("Invalid token");
    }
  }
}

export const authService = new AuthService();
