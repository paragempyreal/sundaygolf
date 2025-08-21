import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { configService } from "../services/configService";
import {
  BarChart3,
  Database,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Users,
  Settings,
  Mail,
} from "lucide-react";
import toast from "react-hot-toast";

interface SystemStatus {
  fulfil: boolean;
  shiphero: boolean;
  email: boolean;
  lastSync: string | null;
  syncStatus: "idle" | "running" | "success" | "error";
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    fulfil: false,
    shiphero: false,
    email: false,
    lastSync: null,
    syncStatus: "idle",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [configStatus, setConfigStatus] = useState({
    fulfilConfigured: false,
    shipheroConfigured: false,
    emailConfigured: false,
  });

  useEffect(() => {
    loadSystemStatus();
    loadConfigurationStatus();
  }, []);

  const loadSystemStatus = async () => {
    try {
      setIsLoading(true);
      // Test connections
      const fulfilTest = await configService.testFulfilConnection();
      const shipheroTest = await configService.testShipHeroConnection();

      // Check email configuration
      let emailTest = { success: false, message: "Not configured" };
      try {
        emailTest = await configService.testEmailConfig();
      } catch (error) {
        // Email not configured yet
      }

      setSystemStatus({
        fulfil: fulfilTest.success,
        shiphero: shipheroTest.success,
        email: emailTest.success,
        lastSync: new Date().toISOString(), // This would come from backend
        syncStatus: "idle",
      });
    } catch (error) {
      toast.error("Failed to load system status");
    } finally {
      setIsLoading(false);
    }
  };

  const loadConfigurationStatus = async () => {
    try {
      const config = await configService.getConfig();
      setConfigStatus({
        fulfilConfigured: !!(config.fulfil.subdomain && config.fulfil.apiKey),
        shipheroConfigured: !!config.shiphero.refreshToken,
        emailConfigured: false, // Will be updated below
      });

      // Check email configuration
      try {
        const emailConfig = await configService.getEmailConfig();
        setConfigStatus((prev) => ({
          ...prev,
          emailConfigured:
            emailConfig.isActive &&
            !!emailConfig.smtpHost &&
            !!emailConfig.smtpUsername,
        }));
      } catch (error) {
        // Email not configured yet
      }
    } catch (error) {
      console.error("Failed to load configuration status:", error);
    }
  };

  const handleTestConnections = async () => {
    await loadSystemStatus();
    toast.success("Connection tests completed");
  };

  const getStatusIcon = (status: boolean) => {
    return status ? (
      <CheckCircle className="h-6 w-6 text-green-500" />
    ) : (
      <AlertTriangle className="h-6 w-6 text-red-500" />
    );
  };

  const getStatusText = (status: boolean) => {
    return status ? "Connected" : "Disconnected";
  };

  const getStatusColor = (status: boolean) => {
    return status ? "text-green-600" : "text-red-600";
  };

  const getConfigStatusText = (configured: boolean) => {
    return configured ? "Configured" : "Not Configured";
  };

  const getConfigStatusColor = (configured: boolean) => {
    return configured ? "text-green-600" : "text-yellow-600";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-700">
            Welcome back, {user?.username}. Here's an overview of your system.
            {user?.isAdmin && (
              <span className="ml-2 text-primary-600 font-medium">(Admin)</span>
            )}
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={handleTestConnections}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Test Connections
          </button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        {/* Fulfil Status */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Fulfil Connection
                  </dt>
                  <dd className="flex items-center text-sm font-medium text-gray-900">
                    {getStatusIcon(systemStatus.fulfil)}
                    <span
                      className={`ml-2 ${getStatusColor(systemStatus.fulfil)}`}
                    >
                      {getStatusText(systemStatus.fulfil)}
                    </span>
                  </dd>
                  <dd
                    className={`text-xs ${getConfigStatusColor(
                      configStatus.fulfilConfigured
                    )}`}
                  >
                    {getConfigStatusText(configStatus.fulfilConfigured)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* ShipHero Status */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3 className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    ShipHero Connection
                  </dt>
                  <dd className="flex items-center text-sm font-medium text-gray-900">
                    {getStatusIcon(systemStatus.shiphero)}
                    <span
                      className={`ml-2 ${getStatusColor(
                        systemStatus.shiphero
                      )}`}
                    >
                      {getStatusText(systemStatus.shiphero)}
                    </span>
                  </dd>
                  <dd
                    className={`text-xs ${getConfigStatusColor(
                      configStatus.shipheroConfigured
                    )}`}
                  >
                    {getConfigStatusText(configStatus.shipheroConfigured)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Email Status */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Mail className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Email Service
                  </dt>
                  <dd className="flex items-center text-sm font-medium text-gray-900">
                    {getStatusIcon(systemStatus.email)}
                    <span
                      className={`ml-2 ${getStatusColor(systemStatus.email)}`}
                    >
                      {getStatusText(systemStatus.email)}
                    </span>
                  </dd>
                  <dd
                    className={`text-xs ${getConfigStatusColor(
                      configStatus.emailConfigured
                    )}`}
                  >
                    {getConfigStatusText(configStatus.emailConfigured)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Sync Status */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <RefreshCw className="h-6 w-6 text-indigo-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Last Sync
                  </dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {systemStatus.lastSync
                      ? new Date(systemStatus.lastSync).toLocaleString()
                      : "Never"}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* User Status */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-6 w-6 text-pink-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    User Role
                  </dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {user?.isAdmin ? "Administrator" : "User"}
                  </dd>
                  <dd className="text-xs text-gray-500">
                    {user?.isActive ? "Active" : "Inactive"}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <a
              href="/configuration?tab=fulfil"
              className="relative group bg-white p-6 border border-gray-300 rounded-lg hover:border-primary-400 hover:ring-1 hover:ring-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <div>
                <span className="rounded-lg inline-flex p-3 bg-primary-50 text-primary-700 ring-4 ring-white">
                  <Database className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium">
                  <span className="absolute inset-0" aria-hidden="true" />
                  Manage Fulfil Config
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Update Fulfil API credentials and settings
                </p>
              </div>
            </a>

            <a
              href="/configuration?tab=shiphero"
              className="relative group bg-white p-6 border border-gray-300 rounded-lg hover:border-primary-400 hover:ring-1 hover:ring-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <div>
                <span className="rounded-lg inline-flex p-3 bg-green-50 text-green-700 ring-4 ring-white">
                  <BarChart3 className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium">
                  <span className="absolute inset-0" aria-hidden="true" />
                  Manage ShipHero Config
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Update ShipHero API credentials and settings
                </p>
              </div>
            </a>

            <a
              href="/configuration?tab=email"
              className="relative group bg-white p-6 border border-gray-300 rounded-lg hover:border-primary-400 hover:ring-1 hover:ring-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <div>
                <span className="rounded-lg inline-flex p-3 bg-purple-50 text-purple-700 ring-4 ring-white">
                  <Mail className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium">
                  <span className="absolute inset-0" aria-hidden="true" />
                  Email Settings
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Configure SMTP settings and email notifications
                </p>
              </div>
            </a>

            <a
              href="/configuration?tab=system"
              className="relative group bg-white p-6 border border-gray-300 rounded-lg hover:border-primary-400 hover:ring-1 hover:ring-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <div>
                <span className="rounded-lg inline-flex p-3 bg-indigo-50 text-indigo-700 ring-4 ring-white">
                  <Settings className="h-6 w-6" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium">
                  <span className="absolute inset-0" aria-hidden="true" />
                  System Settings
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Configure sync intervals and system preferences
                </p>
              </div>
            </a>

            {user?.isAdmin && (
              <a
                href="/configuration?tab=users"
                className="relative group bg-white p-6 border border-gray-300 rounded-lg hover:border-primary-400 hover:ring-1 hover:ring-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-pink-50 text-pink-700 ring-4 ring-white">
                    <Users className="h-6 w-6" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium">
                    <span className="absolute inset-0" aria-hidden="true" />
                    User Management
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Create and manage user accounts
                  </p>
                </div>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Configuration Status */}
      {user?.isAdmin && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Configuration Status
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center">
                  <Database className="h-5 w-5 text-blue-600 mr-3" />
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      Fulfil Configuration
                    </h4>
                    <p
                      className={`text-sm ${getConfigStatusColor(
                        configStatus.fulfilConfigured
                      )}`}
                    >
                      {getConfigStatusText(configStatus.fulfilConfigured)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center">
                  <BarChart3 className="h-5 w-5 text-green-600 mr-3" />
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      ShipHero Configuration
                    </h4>
                    <p
                      className={`text-sm ${getConfigStatusColor(
                        configStatus.shipheroConfigured
                      )}`}
                    >
                      {getConfigStatusText(configStatus.shipheroConfigured)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center">
                  <Mail className="h-5 w-5 text-purple-600 mr-3" />
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      Email Configuration
                    </h4>
                    <p
                      className={`text-sm ${getConfigStatusColor(
                        configStatus.emailConfigured
                      )}`}
                    >
                      {getConfigStatusText(configStatus.emailConfigured)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
