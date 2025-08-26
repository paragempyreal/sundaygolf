import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  configService,
  FulfilConfig,
  ShipHeroConfig,
  SystemConfig,
  EmailConfig,
  User,
} from "../services/configService";
import {
  Database,
  BarChart3,
  Settings,
  Save,
  CheckCircle,
  Users,
  Plus,
  Trash2,
  Edit,
  Mail,
} from "lucide-react";
import toast from "react-hot-toast";
import { useSearchParams } from "react-router-dom";

const Configuration: React.FC = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Get initial tab from URL or default to fulfil
  const initialTab =
    (searchParams.get("tab") as
      | "fulfil"
      | "shiphero"
      | "system"
      | "email"
      | "users") || "fulfil";
  const [activeTab, setActiveTab] = useState<
    "fulfil" | "shiphero" | "system" | "email" | "users"
  >(initialTab);

  // Configuration states
  const [fulfilConfig, setFulfilConfig] = useState<FulfilConfig>({
    subdomain: "",
    apiKey: "",
  });

  const [shipheroConfig, setShipHeroConfig] = useState<ShipHeroConfig>({
    refreshToken: "",
    oauthUrl: "https://public-api.shiphero.com/auth/refresh",
    apiBaseUrl: "https://public-api.shiphero.com",
    defaultWarehouseId: "",
  });

  const [systemConfig, setSystemConfig] = useState<SystemConfig>({
    pollIntervalMinutes: 5,
  });

  const [emailConfig, setEmailConfig] = useState<EmailConfig>({
    smtpHost: "",
    smtpPort: 587,
    smtpUsername: "",
    smtpPassword: "",
    smtpUseTls: true,
    smtpUseSsl: false,
    fromEmail: "",
    fromName: "Fulfil ShipHero Mediator",
    isActive: false,
  });

  // Test connection states removed

  // User management states
  const [users, setUsers] = useState<User[]>([]);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({
    username: "",
    email: "",
    password: "",
    isAdmin: false,
  });

  useEffect(() => {
    loadConfiguration();
    if (user?.isAdmin) {
      loadUsers();
    }
  }, [user]);

  // Update URL when tab changes
  useEffect(() => {
    setSearchParams({ tab: activeTab });
  }, [activeTab, setSearchParams]);

  const loadConfiguration = async () => {
    try {
      setIsLoading(true);
      const config = await configService.getConfig();
      setFulfilConfig(config.fulfil);
      setShipHeroConfig(config.shiphero);
      setSystemConfig(config.system);

      // Load email configuration
      try {
        const emailConfigData = await configService.getEmailConfig();
        setEmailConfig(emailConfigData);
      } catch (error) {
        console.log("Email configuration not available yet");
      }
    } catch (error) {
      toast.error("Failed to load configuration");
    } finally {
      setIsLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const usersData = await configService.getUsers();
      setUsers(usersData);
    } catch (error) {
      toast.error("Failed to load users");
    }
  };

  const handleSaveFulfil = async () => {
    try {
      setIsSaving(true);
      await configService.updateFulfilConfig(fulfilConfig);
      toast.success("Fulfil configuration saved successfully");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to save Fulfil configuration"
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveShipHero = async () => {
    try {
      setIsSaving(true);
      await configService.updateShipHeroConfig(shipheroConfig);
      toast.success("ShipHero configuration saved successfully");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to save ShipHero configuration"
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSystem = async () => {
    try {
      setIsSaving(true);
      await configService.updateSystemConfig(systemConfig);
      toast.success("System configuration saved successfully");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to save system configuration"
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveEmail = async () => {
    try {
      setIsSaving(true);
      await configService.updateEmailConfig(emailConfig);
      toast.success("Email configuration saved successfully");
      // Reload email config to get updated state
      const updatedConfig = await configService.getEmailConfig();
      setEmailConfig(updatedConfig);
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to save email configuration"
      );
    } finally {
      setIsSaving(false);
    }
  };

  // Test handlers removed

  const handleCreateUser = async () => {
    try {
      if (!newUser.username || !newUser.email || !newUser.password) {
        toast.error("Please fill in all required fields");
        return;
      }

      await configService.createUser(newUser);
      toast.success("User created successfully");
      setNewUser({ username: "", email: "", password: "", isAdmin: false });
      setShowCreateUser(false);
      loadUsers();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to create user"
      );
    }
  };

  const tabs = [
    { id: "fulfil", name: "Fulfil Configuration", icon: Database },
    { id: "shiphero", name: "ShipHero Configuration", icon: BarChart3 },
    { id: "system", name: "System Configuration", icon: Settings },
    { id: "email", name: "Email Configuration", icon: Mail },
    ...(user?.isAdmin
      ? [{ id: "users", name: "User Management", icon: Users }]
      : []),
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configuration</h1>
        <p className="mt-2 text-sm text-gray-700">
          Manage your Fulfil and ShipHero API credentials and system settings.
          {user?.isAdmin && (
            <span className="ml-2 text-primary-600 font-medium">
              (Admin Access)
            </span>
          )}
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <Icon className="h-4 w-4 inline mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white shadow rounded-lg">
        {activeTab === "fulfil" && (
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Fulfil Configuration
            </h3>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="fulfil-subdomain"
                  className="block text-sm font-medium text-gray-700"
                >
                  Subdomain
                </label>
                <input
                  type="text"
                  id="fulfil-subdomain"
                  value={fulfilConfig.subdomain}
                  onChange={(e) =>
                    setFulfilConfig({
                      ...fulfilConfig,
                      subdomain: e.target.value,
                    })
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="yourcompany"
                />
              </div>
              <div>
                <label
                  htmlFor="fulfil-api-key"
                  className="block text-sm font-medium text-gray-700"
                >
                  API Key
                </label>
                <input
                  type="password"
                  id="fulfil-api-key"
                  value={fulfilConfig.apiKey}
                  onChange={(e) =>
                    setFulfilConfig({ ...fulfilConfig, apiKey: e.target.value })
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Enter your Fulfil API key"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleSaveFulfil}
                  disabled={isSaving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? "Saving..." : "Save Configuration"}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "shiphero" && (
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              ShipHero Configuration
            </h3>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="shiphero-refresh-token"
                  className="block text-sm font-medium text-gray-700"
                >
                  Refresh Token
                </label>
                <input
                  type="password"
                  id="shiphero-refresh-token"
                  value={shipheroConfig.refreshToken}
                  onChange={(e) =>
                    setShipHeroConfig({
                      ...shipheroConfig,
                      refreshToken: e.target.value,
                    })
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Enter your ShipHero refresh token"
                />
              </div>
              <div>
                <label
                  htmlFor="shiphero-oauth-url"
                  className="block text-sm font-medium text-gray-700"
                >
                  OAuth URL
                </label>
                <input
                  type="url"
                  id="shiphero-oauth-url"
                  value={shipheroConfig.oauthUrl}
                  onChange={(e) =>
                    setShipHeroConfig({
                      ...shipheroConfig,
                      oauthUrl: e.target.value,
                    })
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
              <div>
                <label
                  htmlFor="shiphero-api-base-url"
                  className="block text-sm font-medium text-gray-700"
                >
                  API Base URL
                </label>
                <input
                  type="url"
                  id="shiphero-api-base-url"
                  value={shipheroConfig.apiBaseUrl}
                  onChange={(e) =>
                    setShipHeroConfig({
                      ...shipheroConfig,
                      apiBaseUrl: e.target.value,
                    })
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
              <div>
                <label
                  htmlFor="shiphero-default-warehouse-id"
                  className="block text-sm font-medium text-gray-700"
                >
                  Default Warehouse ID
                </label>
                <input
                  type="text"
                  id="shiphero-default-warehouse-id"
                  value={shipheroConfig.defaultWarehouseId || ""}
                  onChange={(e) =>
                    setShipHeroConfig({
                      ...shipheroConfig,
                      defaultWarehouseId: e.target.value,
                    })
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="V2FyZWhvdXNlOjEyMzQ="
                />
                <p className="mt-1 text-sm text-gray-500">
                  Used when creating products in ShipHero to satisfy required
                  warehouse_products.
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleSaveShipHero}
                  disabled={isSaving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? "Saving..." : "Save Configuration"}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "system" && (
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              System Configuration
            </h3>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="poll-interval"
                  className="block text-sm font-medium text-gray-700"
                >
                  Poll Interval (minutes)
                </label>
                <input
                  type="number"
                  id="poll-interval"
                  min="1"
                  max="60"
                  value={systemConfig.pollIntervalMinutes}
                  onChange={(e) =>
                    setSystemConfig({
                      ...systemConfig,
                      pollIntervalMinutes: parseInt(e.target.value) || 5,
                    })
                  }
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
                <p className="mt-1 text-sm text-gray-500">
                  How often the system should check for new products (1-60
                  minutes)
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleSaveSystem}
                  disabled={isSaving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? "Saving..." : "Save Configuration"}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "email" && (
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Email Configuration
            </h3>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="smtp-host"
                    className="block text-sm font-medium text-gray-700"
                  >
                    SMTP Host
                  </label>
                  <input
                    type="text"
                    id="smtp-host"
                    value={emailConfig.smtpHost}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        smtpHost: e.target.value,
                      })
                    }
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="smtp.gmail.com"
                  />
                </div>
                <div>
                  <label
                    htmlFor="smtp-port"
                    className="block text-sm font-medium text-gray-700"
                  >
                    SMTP Port
                  </label>
                  <input
                    type="number"
                    id="smtp-port"
                    value={emailConfig.smtpPort}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        smtpPort: parseInt(e.target.value) || 587,
                      })
                    }
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="smtp-username"
                    className="block text-sm font-medium text-gray-700"
                  >
                    SMTP Username
                  </label>
                  <input
                    type="text"
                    id="smtp-username"
                    value={emailConfig.smtpUsername}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        smtpUsername: e.target.value,
                      })
                    }
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="your-email@gmail.com"
                  />
                </div>
                <div>
                  <label
                    htmlFor="smtp-password"
                    className="block text-sm font-medium text-gray-700"
                  >
                    SMTP Password
                  </label>
                  <input
                    type="password"
                    id="smtp-password"
                    value={emailConfig.smtpPassword}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        smtpPassword: e.target.value,
                      })
                    }
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Enter your SMTP password"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="from-email"
                    className="block text-sm font-medium text-gray-700"
                  >
                    From Email
                  </label>
                  <input
                    type="email"
                    id="from-email"
                    value={emailConfig.fromEmail}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        fromEmail: e.target.value,
                      })
                    }
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="noreply@yourcompany.com"
                  />
                </div>
                <div>
                  <label
                    htmlFor="from-name"
                    className="block text-sm font-medium text-gray-700"
                  >
                    From Name
                  </label>
                  <input
                    type="text"
                    id="from-name"
                    value={emailConfig.fromName}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        fromName: e.target.value,
                      })
                    }
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Your Company Name"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-6">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="smtp-use-tls"
                    checked={emailConfig.smtpUseTls}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        smtpUseTls: e.target.checked,
                      })
                    }
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="smtp-use-tls"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Use TLS
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="smtp-use-ssl"
                    checked={emailConfig.smtpUseSsl}
                    onChange={(e) =>
                      setEmailConfig({
                        ...emailConfig,
                        smtpUseSsl: e.target.checked,
                      })
                    }
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="smtp-use-ssl"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Use SSL
                  </label>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleSaveEmail}
                  disabled={isSaving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? "Saving..." : "Save Configuration"}
                </button>
              </div>

              {emailConfig.isActive && (
                <div className="p-3 bg-green-50 rounded-md">
                  <div className="flex">
                    <CheckCircle className="h-5 w-5 text-green-400" />
                    <p className="ml-3 text-sm text-green-800">
                      Email configuration is active and ready to use
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "users" && user?.isAdmin && (
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                User Management
              </h3>
              <button
                onClick={() => setShowCreateUser(true)}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add User
              </button>
            </div>

            {/* Users List */}
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((userItem) => (
                    <tr key={userItem.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {userItem.username}
                          </div>
                          <div className="text-sm text-gray-500">
                            {userItem.email}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            userItem.isAdmin
                              ? "bg-purple-100 text-purple-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {userItem.isAdmin ? "Admin" : "User"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            userItem.isActive
                              ? "bg-green-100 text-green-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {userItem.isActive ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {userItem.created_at
                          ? new Date(userItem.created_at).toLocaleDateString()
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button className="text-primary-600 hover:text-primary-900 mr-3">
                          <Edit className="h-4 w-4" />
                        </button>
                        <button className="text-red-600 hover:text-red-900">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Create User Modal */}
            {showCreateUser && (
              <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                  <div className="mt-3">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Create New User
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Username
                        </label>
                        <input
                          type="text"
                          value={newUser.username}
                          onChange={(e) =>
                            setNewUser({ ...newUser, username: e.target.value })
                          }
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Email
                        </label>
                        <input
                          type="email"
                          value={newUser.email}
                          onChange={(e) =>
                            setNewUser({ ...newUser, email: e.target.value })
                          }
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Password
                        </label>
                        <input
                          type="password"
                          value={newUser.password}
                          onChange={(e) =>
                            setNewUser({ ...newUser, password: e.target.value })
                          }
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        />
                      </div>
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="is-admin"
                          checked={newUser.isAdmin}
                          onChange={(e) =>
                            setNewUser({
                              ...newUser,
                              isAdmin: e.target.checked,
                            })
                          }
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <label
                          htmlFor="is-admin"
                          className="ml-2 block text-sm text-gray-900"
                        >
                          Admin user
                        </label>
                      </div>
                    </div>
                    <div className="flex justify-end space-x-3 mt-6">
                      <button
                        onClick={() => setShowCreateUser(false)}
                        className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleCreateUser}
                        className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                      >
                        Create User
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Configuration;
