import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Lock, User, Eye, EyeOff, Loader2, ArrowLeftRight } from "lucide-react";
import toast from "react-hot-toast";

const Login: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsLoading(true);
    try {
      await login(username, password);
      toast.success("Login successful!");
      navigate("/");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2 bg-gray-50">
      {/* Brand / Marketing panel */}
      <div className="relative hidden md:flex flex-col justify-between p-10 text-white bg-gradient-to-br from-primary-600 to-primary-700">
        <div className="relative">
          <div className="flex items-center text-white font-semibold text-xl">
            <span>Fulfil</span>
            <ArrowLeftRight className="mx-2 h-5 w-5" />
            <span>ShipHero</span>
          </div>
          <p className="mt-4 max-w-sm text-primary-50/90">
            Synchronize configurations and manage integrations with a secure,
            modern dashboard.
          </p>
        </div>
        <div className="mt-10 relative h-96 w-full flex items-center justify-center">
          <img
            src="/login-illustration.svg"
            alt="Fulfil ↔ ShipHero illustration"
            className="max-h-full w-auto drop-shadow-lg"
          />
        </div>
        <p className="relative text-xs text-primary-50/70">
          © {new Date().getFullYear()} Fulfil ↔ ShipHero Mediator
        </p>
      </div>

      {/* Login form */}
      <div className="flex items-center justify-center py-12 px-6">
        <div className="w-full max-w-md">
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8">
            <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-50">
              <Lock className="h-6 w-6 text-primary-600" />
            </div>
            <h2 className="mt-6 text-center text-2xl font-bold text-gray-900">
              Welcome back
            </h2>
            <p className="mt-1 text-center text-sm text-gray-600">
              Sign in to manage your integration
            </p>

            <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-5">
                <div>
                  <label htmlFor="username">Username</label>
                  <div className="relative mt-1">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      id="username"
                      name="username"
                      type="text"
                      required
                      className="pl-10"
                      placeholder="Enter your username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password">Password</label>
                  <div className="relative mt-1">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      required
                      className="pl-10 pr-10"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
                      }
                    >
                      {showPassword ? (
                        <EyeOff className="h-5 w-5" />
                      ) : (
                        <Eye className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full flex items-center justify-center gap-2"
                aria-busy={isLoading}
              >
                {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                <span>{isLoading ? "Signing in..." : "Sign in"}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
