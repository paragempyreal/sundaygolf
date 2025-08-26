import React, { useState, useEffect } from "react";
import { RefreshCw, AlertCircle } from "lucide-react";
import { configService } from "../services/configService";

interface SyncStatus {
  total_products: number;
  synced_products: number;
  pending_sync: number;
  recent_synced_products: number;
  last_synced_at: string | null;
}

interface SyncLogItem {
  id: number;
  product_code: string;
  product_name: string;
  action: "created" | "updated";
  changed_fields?: string | null; // JSON string
  synced_at: string | null;
}

const ProductSyncPage: React.FC = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    total_products: 0,
    synced_products: 0,
    pending_sync: 0,
    recent_synced_products: 0,
    last_synced_at: null,
  });
  const [logs, setLogs] = useState<SyncLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [query, setQuery] = useState("");
  const [showDetailsId, setShowDetailsId] = useState<number | null>(null);

  useEffect(() => {
    loadSyncStatus();
  }, []);

  useEffect(() => {
    loadSyncLogs(page, query);
  }, [page]);

  const loadSyncStatus = async () => {
    try {
      const status = await configService.getProductSyncStatus();
      setSyncStatus(status);
    } catch (error) {
      console.error("Failed to load product sync status:", error);
    }
  };

  const loadSyncLogs = async (pageNum: number, q?: string) => {
    try {
      setIsLoading(true);
      const res = await configService.getProductSyncLogs(pageNum, perPage, q);
      setLogs(res.items);
      setTotalPages(res.total_pages);
    } catch (error) {
      console.error("Failed to load product sync logs:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    setPage(1);
    await loadSyncLogs(1, query);
  };

  const clearSearch = async () => {
    setQuery("");
    setPage(1);
    await loadSyncLogs(1, "");
  };

  const refreshData = async () => {
    setIsRefreshing(true);
    try {
      await loadSyncStatus();
      await loadSyncLogs(page, query);
    } catch (error) {
      console.error("Failed to refresh data:", error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getStatusColor = (synced: number, total: number) => {
    if (synced === total) return "text-green-600";
    if (synced > 0) return "text-yellow-600";
    return "text-red-600";
  };

  const getChangedFieldsArray = (changed_fields?: string | null) => {
    if (!changed_fields)
      return [] as Array<{ key: string; old: any; new: any }>;
    try {
      const obj = JSON.parse(changed_fields) as Record<
        string,
        { old: any; new: any }
      >;
      return Object.entries(obj).map(([key, value]) => ({
        key,
        old: value.old,
        new: value.new,
      }));
    } catch {
      return [] as Array<{ key: string; old: any; new: any }>;
    }
  };

  const getChangedFieldsCount = (changed_fields?: string | null) => {
    return getChangedFieldsArray(changed_fields).length;
  };

  const renderActionBadge = (action: "created" | "updated") => {
    const isCreated = action === "created";
    const color = isCreated
      ? "bg-green-100 text-green-800"
      : "bg-blue-100 text-blue-800";
    const label = isCreated ? "Created" : "Updated";
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${color}`}
      >
        {label}
      </span>
    );
  };

  const currentLog = logs.find((l) => l.id === showDetailsId) || null;

  const pageButtons = () => {
    const buttons = [] as number[];
    const start = Math.max(1, Math.min(page - 2, Math.max(1, totalPages - 4)));
    const end = Math.min(totalPages, start + 4);
    for (let p = start; p <= end; p++) buttons.push(p);
    return buttons;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Product Sync</h1>
          <p className="mt-2 text-sm text-gray-700">
            Monitor synchronization between Fulfil and the mediator database
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search by product name, code, Fulfil ID, ShipHero ID"
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button
            onClick={handleSearch}
            className="px-3 py-2 text-sm border rounded bg-white hover:bg-gray-50"
          >
            Search
          </button>
          <button
            onClick={clearSearch}
            className="px-3 py-2 text-sm border rounded bg-white hover:bg-gray-50"
          >
            Clear
          </button>
          <button
            onClick={refreshData}
            disabled={isRefreshing}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <RefreshCw
              className={`h-5 w-5 mr-2 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* Sync Status Summary (no tiles) */}
      <div className="text-sm text-gray-700">
        <span className="mr-6">
          <span className="text-gray-500">Total Products:</span>{" "}
          <span className="font-semibold">{syncStatus.total_products}</span>
        </span>
        <span>
          <span className="text-gray-500">Last Sync:</span>{" "}
          <span className="font-semibold">
            {formatDate(syncStatus.last_synced_at)}
          </span>
        </span>
      </div>

      {/* Product Sync Logs */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Product Sync Logs
          </h3>
          <div className="mt-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <RefreshCw className="h-8 w-8 text-primary-600 animate-spin" />
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-8">
                <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  No product sync logs
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  No products have been synced yet.
                </p>
              </div>
            ) : (
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th
                        scope="col"
                        className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6"
                      >
                        Product Code
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Product Name
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Action
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Changed Fields
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Synced At
                      </th>
                      <th
                        scope="col"
                        className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Details
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                          {log.product_code}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-700">
                          {log.product_name}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-700">
                          {renderActionBadge(log.action)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-700">
                          {getChangedFieldsCount(log.changed_fields)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {formatDate(log.synced_at)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <button
                            onClick={() => setShowDetailsId(log.id)}
                            className="px-2 py-1 border rounded hover:bg-gray-50"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Page {page} of {totalPages}
              </div>
              <div className="space-x-2 flex items-center">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                {pageButtons().map((p) => (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`px-3 py-1 text-sm border rounded ${
                      p === page
                        ? "bg-primary-600 text-white border-primary-600"
                        : "bg-white"
                    }`}
                  >
                    {p}
                  </button>
                ))}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Details Modal */}
      {showDetailsId && currentLog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-3xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Product Sync Details
                </h3>
                <p className="text-xs text-gray-500">
                  Detailed field differences for this sync event
                </p>
              </div>
              <button
                onClick={() => setShowDetailsId(null)}
                className="px-3 py-1 border rounded hover:bg-gray-50"
              >
                Close
              </button>
            </div>

            {/* Meta */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 text-sm">
              <div className="p-3 rounded bg-gray-50">
                <div>
                  <span className="font-medium">Product Code:</span>{" "}
                  {currentLog.product_code}
                </div>
                <div>
                  <span className="font-medium">Product Name:</span>{" "}
                  {currentLog.product_name}
                </div>
              </div>
              <div className="p-3 rounded bg-gray-50">
                <div>
                  <span className="font-medium">Action:</span>{" "}
                  {currentLog.action}
                </div>
                <div>
                  <span className="font-medium">Synced At:</span>{" "}
                  {formatDate(currentLog.synced_at)}
                </div>
              </div>
            </div>

            {/* Changed fields table */}
            <div className="border rounded">
              <div className="px-3 py-2 border-b bg-gray-50 text-sm font-medium">
                Changed Fields (
                {getChangedFieldsCount(currentLog.changed_fields)})
              </div>
              <div className="max-h-96 overflow-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">
                        Field
                      </th>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">
                        Old
                      </th>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">
                        New
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {getChangedFieldsArray(currentLog.changed_fields).map(
                      (row, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-2 text-gray-900 font-medium">
                            {row.key}
                          </td>
                          <td className="px-4 py-2 text-gray-600 break-all">
                            {String(row.old ?? "")}
                          </td>
                          <td className="px-4 py-2 text-gray-900 break-all">
                            {String(row.new ?? "")}
                          </td>
                        </tr>
                      )
                    )}
                    {getChangedFieldsCount(currentLog.changed_fields) === 0 && (
                      <tr>
                        <td
                          className="px-4 py-4 text-center text-gray-500"
                          colSpan={3}
                        >
                          No field-level changes captured.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductSyncPage;
